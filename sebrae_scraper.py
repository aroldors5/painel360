import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime

class SebraeScraper:
    def __init__(self):
        """
        Inicializa o scraper para coletar soluções dos sites do Sebrae.
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.solutions = []
        
    def _make_request(self, url):
        """
        Faz uma requisição HTTP com tratamento de erros e delays.
        
        Args:
            url (str): URL para fazer a requisição
            
        Returns:
            BeautifulSoup: Objeto BeautifulSoup com o conteúdo da página ou None em caso de erro
        """
        try:
            # Adiciona um delay aleatório para evitar bloqueios
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar {url}: {e}")
            return None
    
    def scrape_sebraetec(self):
        """
        Coleta soluções do Sebraetec.
        
        Returns:
            list: Lista de soluções encontradas
        """
        url = "https://sebrae.com.br/sites/PortalSebrae/sebraetec"
        soup = self._make_request(url)
        
        if not soup:
            return []
        
        solutions = []
        
        # Procura por cards de soluções
        solution_cards = soup.find_all('div', class_='card')
        
        for card in solution_cards:
            try:
                title_elem = card.find('h3') or card.find('h2') or card.find('strong')
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                description_elem = card.find('p')
                description = description_elem.text.strip() if description_elem else ""
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                solutions.append({
                    'Nome da solução': title,
                    'Descrição': description,
                    'Link': link,
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Sebraetec',
                    'Tema': self._extract_theme(title, description),
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception as e:
                print(f"Erro ao processar card no Sebraetec: {e}")
        
        # Se não encontrou cards, tenta outra abordagem
        if not solutions:
            sections = soup.find_all('section')
            
            for section in sections:
                try:
                    title_elem = section.find('h2') or section.find('h3')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    # Pula seções que não são soluções
                    if any(keyword in title.lower() for keyword in ['como funciona', 'quem pode', 'benefícios']):
                        continue
                    
                    description_elem = section.find('p')
                    description = description_elem.text.strip() if description_elem else ""
                    
                    solutions.append({
                        'Nome da solução': title,
                        'Descrição': description,
                        'Link': url,
                        'Modalidade': 'Consultoria',
                        'Fonte': 'Sebraetec',
                        'Tema': self._extract_theme(title, description),
                        'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                    })
                except Exception as e:
                    print(f"Erro ao processar seção no Sebraetec: {e}")
        
        print(f"Coletadas {len(solutions)} soluções do Sebraetec")
        self.solutions.extend(solutions)
        return solutions
    
    def scrape_sebrae_mg(self):
        """
        Coleta soluções do Portal Sebrae MG.
        
        Returns:
            list: Lista de soluções encontradas
        """
        url = "https://sebrae.com.br/sites/PortalSebrae/ufs/mg?codUf=14"
        soup = self._make_request(url)
        
        if not soup:
            return []
        
        solutions = []
        
        # Procura por cards de soluções
        solution_cards = soup.find_all('div', class_='card') or soup.find_all('div', class_='destaque')
        
        for card in solution_cards:
            try:
                title_elem = card.find('h3') or card.find('h2') or card.find('strong')
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                description_elem = card.find('p')
                description = description_elem.text.strip() if description_elem else ""
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                # Pula itens que não são soluções
                if any(keyword in title.lower() for keyword in ['notícia', 'noticia', 'evento']):
                    continue
                
                solutions.append({
                    'Nome da solução': title,
                    'Descrição': description,
                    'Link': link,
                    'Modalidade': self._extract_modality(title, description),
                    'Fonte': 'Portal Sebrae MG',
                    'Tema': self._extract_theme(title, description),
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception as e:
                print(f"Erro ao processar card no Portal Sebrae MG: {e}")
        
        # Procura por links de programas e soluções
        program_links = soup.find_all('a', href=re.compile(r'programas|solucoes|atendimento'))
        
        for link_elem in program_links:
            try:
                title = link_elem.text.strip()
                link = link_elem['href']
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                # Evita duplicatas
                if not any(s['Nome da solução'] == title for s in solutions):
                    solutions.append({
                        'Nome da solução': title,
                        'Descrição': "",
                        'Link': link,
                        'Modalidade': self._extract_modality(title, ""),
                        'Fonte': 'Portal Sebrae MG',
                        'Tema': self._extract_theme(title, ""),
                        'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                    })
            except Exception as e:
                print(f"Erro ao processar link de programa no Portal Sebrae MG: {e}")
        
        print(f"Coletadas {len(solutions)} soluções do Portal Sebrae MG")
        self.solutions.extend(solutions)
        return solutions
    
    def scrape_cursos_eventos(self):
        """
        Coleta cursos e eventos do Sebrae MG.
        
        Returns:
            list: Lista de cursos e eventos encontrados
        """
        url = "https://sebrae.com.br/sites/PortalSebrae/cursoseventos?uf=MG"
        soup = self._make_request(url)
        
        if not soup:
            return []
        
        solutions = []
        
        # Procura por cards de cursos/eventos
        event_cards = soup.find_all('div', class_='card') or soup.find_all('div', class_='evento')
        
        for card in event_cards:
            try:
                title_elem = card.find('h3') or card.find('h2') or card.find('strong')
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                description_elem = card.find('p')
                description = description_elem.text.strip() if description_elem else ""
                
                date_elem = card.find('span', class_='data') or card.find('time')
                date = date_elem.text.strip() if date_elem else ""
                
                location_elem = card.find('span', class_='local')
                location = location_elem.text.strip() if location_elem else "Minas Gerais"
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                modality = 'Curso' if 'curso' in title.lower() else 'Evento'
                
                solutions.append({
                    'Nome da solução': title,
                    'Descrição': description,
                    'Link': link,
                    'Modalidade': modality,
                    'Fonte': 'Agenda Sebrae MG',
                    'Tema': self._extract_theme(title, description),
                    'Data prevista': date,
                    'Local': location,
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception as e:
                print(f"Erro ao processar card de curso/evento: {e}")
        
        print(f"Coletados {len(solutions)} cursos e eventos do Sebrae MG")
        self.solutions.extend(solutions)
        return solutions
    
    def scrape_sebrae_play(self):
        """
        Coleta cursos online do Sebrae Play.
        
        Returns:
            list: Lista de cursos encontrados
        """
        url = "https://sebraeplay.com.br/"
        soup = self._make_request(url)
        
        if not soup:
            return []
        
        solutions = []
        
        # Procura por cards de cursos
        course_cards = soup.find_all('div', class_='card') or soup.find_all('article')
        
        for card in course_cards:
            try:
                title_elem = card.find('h3') or card.find('h2') or card.find('strong')
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                description_elem = card.find('p')
                description = description_elem.text.strip() if description_elem else ""
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                if not link.startswith('http'):
                    link = f"https://sebraeplay.com.br{link}" if link.startswith('/') else f"https://sebraeplay.com.br/{link}"
                
                # Verifica se é gratuito
                price_elem = card.find(text=re.compile(r'Gratuito|R\$'))
                price = price_elem.strip() if price_elem else "Gratuito"
                
                solutions.append({
                    'Nome da solução': title,
                    'Descrição': description,
                    'Link': link,
                    'Modalidade': 'Curso Online',
                    'Fonte': 'Sebrae Play',
                    'Tema': self._extract_theme(title, description),
                    'Preço': price,
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception as e:
                print(f"Erro ao processar card de curso no Sebrae Play: {e}")
        
        # Se não encontrou cards, tenta outra abordagem
        if not solutions:
            course_sections = soup.find_all('section')
            
            for section in course_sections:
                try:
                    title_elem = section.find('h2') or section.find('h3')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    # Pula seções que não são cursos
                    if any(keyword in title.lower() for keyword in ['destaques', 'categorias', 'sobre']):
                        continue
                    
                    link_elems = section.find_all('a')
                    
                    for link_elem in link_elems:
                        course_title = link_elem.text.strip()
                        if not course_title or len(course_title) < 5:
                            continue
                            
                        link = link_elem['href'] if 'href' in link_elem.attrs else ""
                        
                        if not link.startswith('http'):
                            link = f"https://sebraeplay.com.br{link}" if link.startswith('/') else f"https://sebraeplay.com.br/{link}"
                        
                        solutions.append({
                            'Nome da solução': course_title,
                            'Descrição': "",
                            'Link': link,
                            'Modalidade': 'Curso Online',
                            'Fonte': 'Sebrae Play',
                            'Tema': self._extract_theme(course_title, ""),
                            'Preço': "Gratuito",
                            'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    print(f"Erro ao processar seção de curso no Sebrae Play: {e}")
        
        print(f"Coletados {len(solutions)} cursos do Sebrae Play")
        self.solutions.extend(solutions)
        return solutions
    
    def scrape_loja_sebrae_mg(self):
        """
        Coleta soluções da Loja Sebrae MG.
        
        Returns:
            list: Lista de soluções encontradas
        """
        url = "https://loja.sebraemg.com.br/"
        soup = self._make_request(url)
        
        if not soup:
            return []
        
        solutions = []
        
        # Procura por produtos na loja
        product_cards = soup.find_all('div', class_='product') or soup.find_all('li', class_='product')
        
        for card in product_cards:
            try:
                title_elem = card.find('h2') or card.find('h3') or card.find('strong')
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                price_elem = card.find('span', class_='price') or card.find('span', class_='amount')
                price = price_elem.text.strip() if price_elem else "Consulte"
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                # Determina a modalidade com base no título
                modality = 'Curso'
                if 'consultoria' in title.lower():
                    modality = 'Consultoria'
                elif 'programa' in title.lower():
                    modality = 'Programa'
                elif 'evento' in title.lower() or 'workshop' in title.lower():
                    modality = 'Evento'
                
                solutions.append({
                    'Nome da solução': title,
                    'Descrição': "",
                    'Link': link,
                    'Modalidade': modality,
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': self._extract_theme(title, ""),
                    'Preço': price,
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                })
            except Exception as e:
                print(f"Erro ao processar produto na Loja Sebrae MG: {e}")
        
        # Se não encontrou produtos, tenta outra abordagem
        if not solutions:
            category_links = soup.find_all('a', class_='category')
            
            for link_elem in category_links:
                try:
                    category = link_elem.text.strip()
                    link = link_elem['href'] if 'href' in link_elem.attrs else ""
                    
                    # Pula categorias que não são soluções
                    if any(keyword in category.lower() for keyword in ['institucional', 'contato', 'sobre']):
                        continue
                    
                    solutions.append({
                        'Nome da solução': f"Categoria: {category}",
                        'Descrição': f"Soluções na categoria {category}",
                        'Link': link,
                        'Modalidade': 'Diversos',
                        'Fonte': 'Loja Sebrae MG',
                        'Tema': category,
                        'Preço': "Diversos",
                        'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                    })
                except Exception as e:
                    print(f"Erro ao processar categoria na Loja Sebrae MG: {e}")
        
        print(f"Coletadas {len(solutions)} soluções da Loja Sebrae MG")
        self.solutions.extend(solutions)
        return solutions
    
    def _extract_modality(self, title, description):
        """
        Extrai a modalidade da solução com base no título e descrição.
        
        Args:
            title (str): Título da solução
            description (str): Descrição da solução
            
        Returns:
            str: Modalidade da solução
        """
        title_desc = (title + " " + description).lower()
        
        if 'consultoria' in title_desc:
            return 'Consultoria'
        elif 'curso' in title_desc or 'capacitação' in title_desc or 'treinamento' in title_desc:
            if 'online' in title_desc or 'ead' in title_desc or 'distância' in title_desc:
                return 'Curso Online'
            else:
                return 'Curso'
        elif 'programa' in title_desc:
            return 'Programa'
        elif 'evento' in title_desc or 'workshop' in title_desc or 'seminário' in title_desc:
            return 'Evento'
        elif 'palestra' in title_desc:
            return 'Palestra'
        else:
            return 'Solução'
    
    def _extract_theme(self, title, description):
        """
        Extrai o tema da solução com base no título e descrição.
        
        Args:
            title (str): Título da solução
            description (str): Descrição da solução
            
        Returns:
            str: Tema da solução
        """
        title_desc = (title + " " + description).lower()
        
        themes = {
            'marketing': ['marketing', 'divulgação', 'comunicação', 'marca', 'cliente'],
            'vendas': ['vendas', 'comercial', 'negociação', 'atendimento'],
            'finanças': ['finanças', 'financeiro', 'crédito', 'investimento', 'capital'],
            'gestão': ['gestão', 'administração', 'planejamento', 'estratégia'],
            'inovação': ['inovação', 'tecnologia', 'digital', 'transformação'],
            'pessoas': ['pessoas', 'rh', 'recursos humanos', 'equipe', 'liderança'],
            'operações': ['operações', 'processos', 'produção', 'logística', 'qualidade'],
            'jurídico': ['jurídico', 'legal', 'direito', 'contrato', 'legislação'],
            'sustentabilidade': ['sustentabilidade', 'ambiental', 'social', 'responsabilidade'],
            'exportação': ['exportação', 'importação', 'internacional', 'comércio exterior']
        }
        
        for theme, keywords in themes.items():
            if any(keyword in title_desc for keyword in keywords):
                return theme.capitalize()
        
        # Se não encontrou nenhum tema específico
        return "Geral"
    
    def scrape_all(self):
        """
        Coleta soluções de todos os sites do Sebrae.
        
        Returns:
            pandas.DataFrame: DataFrame com todas as soluções coletadas
        """
        self.solutions = []
        
        self.scrape_sebraetec()
        self.scrape_sebrae_mg()
        self.scrape_cursos_eventos()
        self.scrape_sebrae_play()
        self.scrape_loja_sebrae_mg()
        
        # Converte para DataFrame
        df = pd.DataFrame(self.solutions)
        
        # Remove duplicatas
        df = df.drop_duplicates(subset=['Nome da solução', 'Fonte'])
        
        print(f"Total de {len(df)} soluções coletadas de todos os sites")
        return df
    
    def save_to_excel(self, filename="solucoes_sebrae_web.xlsx"):
        """
        Salva as soluções coletadas em um arquivo Excel.
        
        Args:
            filename (str): Nome do arquivo Excel
            
        Returns:
            str: Caminho do arquivo salvo
        """
        if not self.solutions:
            print("Nenhuma solução para salvar")
            return None
        
        df = pd.DataFrame(self.solutions)
        df.to_excel(filename, index=False)
        
        print(f"Soluções salvas em {filename}")
        return filename
    
    def combine_with_excel(self, excel_file, output_file="solucoes_combinadas.xlsx"):
        """
        Combina as soluções coletadas com as soluções de um arquivo Excel.
        
        Args:
            excel_file (str): Caminho do arquivo Excel com soluções
            output_file (str): Nome do arquivo de saída
            
        Returns:
            pandas.DataFrame: DataFrame com as soluções combinadas
        """
        if not self.solutions:
            print("Nenhuma solução coletada da web para combinar")
            return None
        
        try:
            # Carrega o arquivo Excel
            df_excel = pd.read_excel(excel_file)
            
            # Adiciona coluna de fonte se não existir
            if 'Fonte' not in df_excel.columns:
                df_excel['Fonte'] = 'Planilha Excel'
            
            # Converte as soluções coletadas para DataFrame
            df_web = pd.DataFrame(self.solutions)
            
            # Combina os DataFrames
            df_combined = pd.concat([df_excel, df_web], ignore_index=True)
            
            # Remove duplicatas
            df_combined = df_combined.drop_duplicates(subset=['Nome da solução', 'Fonte'])
            
            # Salva o resultado
            df_combined.to_excel(output_file, index=False)
            
            print(f"Soluções combinadas salvas em {output_file}")
            return df_combined
            
        except Exception as e:
            print(f"Erro ao combinar soluções: {e}")
            return None
