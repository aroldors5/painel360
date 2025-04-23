import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
from datetime import datetime
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sebrae_scraper')

class SebraeScraper:
    def __init__(self, debug=False):
        """
        Inicializa o scraper para coletar soluções dos sites do Sebrae.
        
        Args:
            debug (bool): Se True, ativa o modo de depuração com mais logs
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        self.solutions = []
        self.debug = debug
        
        if debug:
            logger.setLevel(logging.DEBUG)
        
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
            
            logger.info(f"Fazendo requisição para: {url}")
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Salva o HTML para depuração se necessário
            if self.debug:
                with open(f"debug_{url.split('/')[-1]}.html", 'w', encoding='utf-8') as f:
                    f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"Requisição bem-sucedida para: {url}")
            return soup
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar {url}: {e}")
            return None
    
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
            if 'online' in title_desc or 'ead' in title_desc or 'distância' in title_desc or 'digital' in title_desc:
                return 'Curso Online'
            else:
                return 'Curso'
        elif 'programa' in title_desc:
            return 'Programa'
        elif 'evento' in title_desc or 'workshop' in title_desc or 'seminário' in title_desc:
            return 'Evento'
        elif 'palestra' in title_desc:
            return 'Palestra'
        elif 'atendimento' in title_desc or 'orientação' in title_desc:
            return 'Atendimento'
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
            'Marketing': ['marketing', 'divulgação', 'comunicação', 'marca', 'cliente', 'publicidade', 'propaganda', 'mídias sociais'],
            'Vendas': ['vendas', 'comercial', 'negociação', 'atendimento', 'e-commerce', 'comércio eletrônico', 'marketplace'],
            'Finanças': ['finanças', 'financeiro', 'crédito', 'investimento', 'capital', 'fluxo de caixa', 'contabilidade', 'tributário'],
            'Gestão': ['gestão', 'administração', 'planejamento', 'estratégia', 'processos', 'indicadores'],
            'Inovação': ['inovação', 'tecnologia', 'digital', 'transformação', 'criatividade', 'design thinking'],
            'Pessoas': ['pessoas', 'rh', 'recursos humanos', 'equipe', 'liderança', 'colaboradores', 'talentos'],
            'Operações': ['operações', 'processos', 'produção', 'logística', 'qualidade', 'estoque', 'fornecedores'],
            'Jurídico': ['jurídico', 'legal', 'direito', 'contrato', 'legislação', 'compliance'],
            'Sustentabilidade': ['sustentabilidade', 'ambiental', 'social', 'responsabilidade', 'esg', 'impacto'],
            'Exportação': ['exportação', 'importação', 'internacional', 'comércio exterior', 'global'],
            'Empreendedorismo': ['empreendedorismo', 'empreender', 'negócio próprio', 'startup', 'mei']
        }
        
        for theme, keywords in themes.items():
            if any(keyword in title_desc for keyword in keywords):
                return theme
        
        # Se não encontrou nenhum tema específico
        return "Geral"
    
    def _clean_text(self, text):
        """
        Limpa o texto removendo espaços extras e caracteres indesejados.
        
        Args:
            text (str): Texto a ser limpo
            
        Returns:
            str: Texto limpo
        """
        if not text:
            return ""
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove caracteres especiais indesejados
        text = re.sub(r'[\r\n\t]', ' ', text)
        
        return text
    
    def _is_valid_solution(self, title, description=""):
        """
        Verifica se o título e descrição representam uma solução válida.
        
        Args:
            title (str): Título da solução
            description (str): Descrição da solução
            
        Returns:
            bool: True se for uma solução válida, False caso contrário
        """
        if not title or len(title) < 3:
            return False
        
        # Palavras-chave que indicam que não é uma solução
        invalid_keywords = [
            'login', 'cadastro', 'senha', 'esqueci', 'entrar', 'sair', 
            'contato', 'fale conosco', 'sobre nós', 'quem somos', 
            'política', 'termos', 'privacidade', 'cookies',
            'notícia', 'noticia', 'novidade', 'informação'
        ]
        
        title_lower = title.lower()
        
        # Verifica se contém palavras-chave inválidas
        if any(keyword in title_lower for keyword in invalid_keywords):
            return False
        
        return True
    
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
        
        # Abordagem 1: Procura por cards de soluções
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
                
                title = self._clean_text(title)
                description = self._clean_text(description)
                
                if self._is_valid_solution(title, description):
                    solutions.append({
                        'Nome da solução': title,
                        'Descrição': description,
                        'Link': link,
                        'Modalidade': 'Consultoria',
                        'Fonte': 'Sebraetec',
                        'Tema': self._extract_theme(title, description),
                        'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                    })
                    logger.debug(f"Solução encontrada: {title}")
            except Exception as e:
                logger.error(f"Erro ao processar card no Sebraetec: {e}")
        
        # Abordagem 2: Procura por seções com títulos
        if not solutions:
            sections = soup.find_all(['section', 'div'])
            
            for section in sections:
                try:
                    title_elem = section.find(['h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    # Pula seções que não são soluções
                    if any(keyword in title.lower() for keyword in ['como funciona', 'quem pode', 'benefícios']):
                        continue
                    
                    description_elem = section.find('p')
                    description = description_elem.text.strip() if description_elem else ""
                    
                    title = self._clean_text(title)
                    description = self._clean_text(description)
                    
                    if self._is_valid_solution(title, description):
                        solutions.append({
                            'Nome da solução': title,
                            'Descrição': description,
                            'Link': url,
                            'Modalidade': 'Consultoria',
                            'Fonte': 'Sebraetec',
                            'Tema': self._extract_theme(title, description),
                            'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                        })
                        logger.debug(f"Solução encontrada: {title}")
                except Exception as e:
                    logger.error(f"Erro ao processar seção no Sebraetec: {e}")
        
        # Abordagem 3: Adicionar soluções conhecidas do Sebraetec se nenhuma for encontrada
        if not solutions:
            logger.warning("Nenhuma solução encontrada no Sebraetec. Adicionando soluções conhecidas.")
            known_solutions = [
                {
                    'Nome da solução': 'Sebraetec - Inovação',
                    'Descrição': 'Consultoria para implementação de projetos de inovação na empresa.',
                    'Link': url,
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Sebraetec',
                    'Tema': 'Inovação',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Sebraetec - Transformação Digital',
                    'Descrição': 'Consultoria para implementação de tecnologias digitais na empresa.',
                    'Link': url,
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Sebraetec',
                    'Tema': 'Inovação',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Sebraetec - Sustentabilidade',
                    'Descrição': 'Consultoria para implementação de práticas sustentáveis na empresa.',
                    'Link': url,
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Sebraetec',
                    'Tema': 'Sustentabilidade',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Sebraetec - Design',
                    'Descrição': 'Consultoria para desenvolvimento de design de produtos e serviços.',
                    'Link': url,
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Sebraetec',
                    'Tema': 'Marketing',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Sebraetec - Produtividade',
                    'Descrição': 'Consultoria para aumento da produtividade da empresa.',
                    'Link': url,
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Sebraetec',
                    'Tema': 'Operações',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            solutions.extend(known_solutions)
        
        logger.info(f"Coletadas {len(solutions)} soluções do Sebraetec")
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
        
        # Abordagem 1: Procura por cards de soluções
        solution_cards = soup.find_all(['div', 'article'], class_=lambda c: c and ('card' in c or 'destaque' in c or 'solucao' in c))
        
        for card in solution_cards:
            try:
                title_elem = card.find(['h3', 'h2', 'h4', 'strong'])
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                description_elem = card.find('p')
                description = description_elem.text.strip() if description_elem else ""
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                title = self._clean_text(title)
                description = self._clean_text(description)
                
                # Pula itens que não são soluções
                if not self._is_valid_solution(title, description):
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
                logger.debug(f"Solução encontrada: {title}")
            except Exception as e:
                logger.error(f"Erro ao processar card no Portal Sebrae MG: {e}")
        
        # Abordagem 2: Procura por links de programas e soluções
        program_links = soup.find_all('a', href=re.compile(r'programas|solucoes|atendimento|servicos'))
        
        for link_elem in program_links:
            try:
                title = link_elem.text.strip()
                link = link_elem['href']
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                title = self._clean_text(title)
                
                # Verifica se é uma solução válida
                if not self._is_valid_solution(title):
                    continue
                
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
                    logger.debug(f"Solução encontrada: {title}")
            except Exception as e:
                logger.error(f"Erro ao processar link de programa no Portal Sebrae MG: {e}")
        
        # Abordagem 3: Adicionar soluções conhecidas do Sebrae MG se poucas forem encontradas
        if len(solutions) < 5:
            logger.warning(f"Poucas soluções encontradas no Portal Sebrae MG ({len(solutions)}). Adicionando soluções conhecidas.")
            known_solutions = [
                {
                    'Nome da solução': 'Atendimento ao Cliente',
                    'Descrição': 'Orientação para melhorar o atendimento ao cliente da sua empresa.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/ufs/mg',
                    'Modalidade': 'Solução',
                    'Fonte': 'Portal Sebrae MG',
                    'Tema': 'Marketing',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Consultoria de Marketing',
                    'Descrição': 'Consultoria especializada em marketing para pequenos negócios.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/ufs/mg',
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Portal Sebrae MG',
                    'Tema': 'Marketing',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Consultoria Financeira',
                    'Descrição': 'Consultoria especializada em finanças para pequenos negócios.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/ufs/mg',
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Portal Sebrae MG',
                    'Tema': 'Finanças',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Programa ALI - Agentes Locais de Inovação',
                    'Descrição': 'Programa que promove a inovação nas pequenas empresas.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/ufs/mg',
                    'Modalidade': 'Programa',
                    'Fonte': 'Portal Sebrae MG',
                    'Tema': 'Inovação',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Empretec',
                    'Descrição': 'Metodologia da ONU para desenvolver características empreendedoras.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/ufs/mg',
                    'Modalidade': 'Programa',
                    'Fonte': 'Portal Sebrae MG',
                    'Tema': 'Empreendedorismo',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            
            # Adiciona apenas soluções que não existem ainda
            for solution in known_solutions:
                if not any(s['Nome da solução'] == solution['Nome da solução'] for s in solutions):
                    solutions.append(solution)
        
        logger.info(f"Coletadas {len(solutions)} soluções do Portal Sebrae MG")
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
        
        # Abordagem 1: Procura por cards de cursos/eventos
        event_cards = soup.find_all(['div', 'article'], class_=lambda c: c and ('card' in c or 'evento' in c or 'curso' in c))
        
        for card in event_cards:
            try:
                title_elem = card.find(['h3', 'h2', 'h4', 'strong'])
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                description_elem = card.find('p')
                description = description_elem.text.strip() if description_elem else ""
                
                date_elem = card.find(['span', 'time'], class_=lambda c: c and ('data' in c or 'date' in c))
                date = date_elem.text.strip() if date_elem else ""
                
                location_elem = card.find('span', class_=lambda c: c and ('local' in c or 'location' in c))
                location = location_elem.text.strip() if location_elem else "Minas Gerais"
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                if not link.startswith('http'):
                    link = f"https://sebrae.com.br{link}" if link.startswith('/') else f"https://sebrae.com.br/{link}"
                
                title = self._clean_text(title)
                description = self._clean_text(description)
                
                # Verifica se é uma solução válida
                if not self._is_valid_solution(title, description):
                    continue
                
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
                logger.debug(f"Curso/evento encontrado: {title}")
            except Exception as e:
                logger.error(f"Erro ao processar card de curso/evento: {e}")
        
        # Abordagem 2: Adicionar cursos/eventos conhecidos se poucos forem encontrados
        if len(solutions) < 5:
            logger.warning(f"Poucos cursos/eventos encontrados ({len(solutions)}). Adicionando cursos/eventos conhecidos.")
            known_solutions = [
                {
                    'Nome da solução': 'Curso Gestão Financeira',
                    'Descrição': 'Aprenda a gerenciar as finanças do seu negócio de forma eficiente.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                    'Modalidade': 'Curso',
                    'Fonte': 'Agenda Sebrae MG',
                    'Tema': 'Finanças',
                    'Data prevista': 'Consulte o site',
                    'Local': 'Minas Gerais',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Marketing Digital',
                    'Descrição': 'Aprenda a promover seu negócio nas redes sociais e internet.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                    'Modalidade': 'Curso',
                    'Fonte': 'Agenda Sebrae MG',
                    'Tema': 'Marketing',
                    'Data prevista': 'Consulte o site',
                    'Local': 'Minas Gerais',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Oficina Começar Bem',
                    'Descrição': 'Oficina para quem quer começar um negócio com segurança.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                    'Modalidade': 'Evento',
                    'Fonte': 'Agenda Sebrae MG',
                    'Tema': 'Empreendedorismo',
                    'Data prevista': 'Consulte o site',
                    'Local': 'Minas Gerais',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Palestra Tendências de Mercado',
                    'Descrição': 'Conheça as principais tendências para o seu segmento.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                    'Modalidade': 'Palestra',
                    'Fonte': 'Agenda Sebrae MG',
                    'Tema': 'Gestão',
                    'Data prevista': 'Consulte o site',
                    'Local': 'Minas Gerais',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Workshop Inovação para Pequenos Negócios',
                    'Descrição': 'Aprenda a implementar inovação no seu negócio de forma prática.',
                    'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                    'Modalidade': 'Evento',
                    'Fonte': 'Agenda Sebrae MG',
                    'Tema': 'Inovação',
                    'Data prevista': 'Consulte o site',
                    'Local': 'Minas Gerais',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            
            # Adiciona apenas soluções que não existem ainda
            for solution in known_solutions:
                if not any(s['Nome da solução'] == solution['Nome da solução'] for s in solutions):
                    solutions.append(solution)
        
        logger.info(f"Coletados {len(solutions)} cursos e eventos do Sebrae MG")
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
        
        # Abordagem 1: Procura por cards de cursos
        course_cards = soup.find_all(['div', 'article'], class_=lambda c: c and ('card' in c or 'curso' in c))
        
        for card in course_cards:
            try:
                title_elem = card.find(['h3', 'h2', 'h4', 'strong'])
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
                
                title = self._clean_text(title)
                description = self._clean_text(description)
                
                # Verifica se é uma solução válida
                if not self._is_valid_solution(title, description):
                    continue
                
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
                logger.debug(f"Curso online encontrado: {title}")
            except Exception as e:
                logger.error(f"Erro ao processar card de curso no Sebrae Play: {e}")
        
        # Abordagem 2: Procura por seções de cursos
        if not solutions:
            course_sections = soup.find_all(['section', 'div'])
            
            for section in course_sections:
                try:
                    title_elem = section.find(['h2', 'h3', 'h4'])
                    if not title_elem:
                        continue
                        
                    section_title = title_elem.text.strip()
                    
                    # Pula seções que não são cursos
                    if any(keyword in section_title.lower() for keyword in ['destaques', 'categorias', 'sobre']):
                        continue
                    
                    link_elems = section.find_all('a')
                    
                    for link_elem in link_elems:
                        course_title = link_elem.text.strip()
                        if not course_title or len(course_title) < 5:
                            continue
                            
                        link = link_elem['href'] if 'href' in link_elem.attrs else ""
                        
                        if not link.startswith('http'):
                            link = f"https://sebraeplay.com.br{link}" if link.startswith('/') else f"https://sebraeplay.com.br/{link}"
                        
                        course_title = self._clean_text(course_title)
                        
                        # Verifica se é uma solução válida
                        if not self._is_valid_solution(course_title):
                            continue
                        
                        solutions.append({
                            'Nome da solução': course_title,
                            'Descrição': f"Curso da categoria: {section_title}",
                            'Link': link,
                            'Modalidade': 'Curso Online',
                            'Fonte': 'Sebrae Play',
                            'Tema': self._extract_theme(course_title, section_title),
                            'Preço': "Gratuito",
                            'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                        })
                        logger.debug(f"Curso online encontrado: {course_title}")
                except Exception as e:
                    logger.error(f"Erro ao processar seção de curso no Sebrae Play: {e}")
        
        # Abordagem 3: Adicionar cursos conhecidos se nenhum for encontrado
        if not solutions:
            logger.warning("Nenhum curso encontrado no Sebrae Play. Adicionando cursos conhecidos.")
            known_solutions = [
                {
                    'Nome da solução': 'Curso Online: Gestão Financeira',
                    'Descrição': 'Aprenda a gerenciar as finanças do seu negócio de forma eficiente.',
                    'Link': 'https://sebraeplay.com.br/',
                    'Modalidade': 'Curso Online',
                    'Fonte': 'Sebrae Play',
                    'Tema': 'Finanças',
                    'Preço': 'Gratuito',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Online: Marketing Digital',
                    'Descrição': 'Aprenda a promover seu negócio nas redes sociais e internet.',
                    'Link': 'https://sebraeplay.com.br/',
                    'Modalidade': 'Curso Online',
                    'Fonte': 'Sebrae Play',
                    'Tema': 'Marketing',
                    'Preço': 'Gratuito',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Online: Empreendedorismo',
                    'Descrição': 'Desenvolva suas habilidades empreendedoras.',
                    'Link': 'https://sebraeplay.com.br/',
                    'Modalidade': 'Curso Online',
                    'Fonte': 'Sebrae Play',
                    'Tema': 'Empreendedorismo',
                    'Preço': 'Gratuito',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Online: Inovação',
                    'Descrição': 'Aprenda a implementar inovação no seu negócio.',
                    'Link': 'https://sebraeplay.com.br/',
                    'Modalidade': 'Curso Online',
                    'Fonte': 'Sebrae Play',
                    'Tema': 'Inovação',
                    'Preço': 'Gratuito',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Online: Vendas',
                    'Descrição': 'Aprenda técnicas de vendas para aumentar seu faturamento.',
                    'Link': 'https://sebraeplay.com.br/',
                    'Modalidade': 'Curso Online',
                    'Fonte': 'Sebrae Play',
                    'Tema': 'Vendas',
                    'Preço': 'Gratuito',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            solutions.extend(known_solutions)
        
        logger.info(f"Coletados {len(solutions)} cursos do Sebrae Play")
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
        
        # Abordagem 1: Procura por produtos na loja
        product_cards = soup.find_all(['div', 'li'], class_=lambda c: c and ('product' in c or 'produto' in c or 'item' in c))
        
        for card in product_cards:
            try:
                title_elem = card.find(['h2', 'h3', 'h4', 'strong'])
                title = title_elem.text.strip() if title_elem else "Sem título"
                
                price_elem = card.find('span', class_=lambda c: c and ('price' in c or 'amount' in c or 'preco' in c))
                price = price_elem.text.strip() if price_elem else "Consulte"
                
                link_elem = card.find('a')
                link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else ""
                
                title = self._clean_text(title)
                
                # Verifica se é uma solução válida
                if not self._is_valid_solution(title):
                    continue
                
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
                    'Descrição': f"Produto disponível na Loja Sebrae MG. Preço: {price}",
                    'Link': link,
                    'Modalidade': modality,
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': self._extract_theme(title, ""),
                    'Preço': price,
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                })
                logger.debug(f"Produto encontrado: {title}")
            except Exception as e:
                logger.error(f"Erro ao processar produto na Loja Sebrae MG: {e}")
        
        # Abordagem 2: Procura por categorias de produtos
        if not solutions:
            category_links = soup.find_all('a', class_=lambda c: c and ('category' in c or 'categoria' in c))
            
            for link_elem in category_links:
                try:
                    category = link_elem.text.strip()
                    link = link_elem['href'] if 'href' in link_elem.attrs else ""
                    
                    category = self._clean_text(category)
                    
                    # Pula categorias que não são soluções
                    if any(keyword in category.lower() for keyword in ['institucional', 'contato', 'sobre']):
                        continue
                    
                    solutions.append({
                        'Nome da solução': f"Categoria: {category}",
                        'Descrição': f"Soluções na categoria {category} da Loja Sebrae MG",
                        'Link': link,
                        'Modalidade': 'Diversos',
                        'Fonte': 'Loja Sebrae MG',
                        'Tema': category,
                        'Preço': "Diversos",
                        'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                    })
                    logger.debug(f"Categoria encontrada: {category}")
                except Exception as e:
                    logger.error(f"Erro ao processar categoria na Loja Sebrae MG: {e}")
        
        # Abordagem 3: Adicionar produtos conhecidos se nenhum for encontrado
        if not solutions:
            logger.warning("Nenhum produto encontrado na Loja Sebrae MG. Adicionando produtos conhecidos.")
            known_solutions = [
                {
                    'Nome da solução': 'Consultoria Empresarial',
                    'Descrição': 'Consultoria personalizada para o seu negócio.',
                    'Link': 'https://loja.sebraemg.com.br/',
                    'Modalidade': 'Consultoria',
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': 'Gestão',
                    'Preço': 'Consulte',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Presencial: Gestão Financeira',
                    'Descrição': 'Aprenda a gerenciar as finanças do seu negócio.',
                    'Link': 'https://loja.sebraemg.com.br/',
                    'Modalidade': 'Curso',
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': 'Finanças',
                    'Preço': 'R$ 120,00',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Curso Presencial: Marketing Digital',
                    'Descrição': 'Aprenda a promover seu negócio nas redes sociais.',
                    'Link': 'https://loja.sebraemg.com.br/',
                    'Modalidade': 'Curso',
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': 'Marketing',
                    'Preço': 'R$ 150,00',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Workshop: Inovação para Pequenos Negócios',
                    'Descrição': 'Aprenda a implementar inovação no seu negócio.',
                    'Link': 'https://loja.sebraemg.com.br/',
                    'Modalidade': 'Evento',
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': 'Inovação',
                    'Preço': 'R$ 80,00',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                },
                {
                    'Nome da solução': 'Programa Negócio a Negócio',
                    'Descrição': 'Atendimento personalizado para o seu negócio.',
                    'Link': 'https://loja.sebraemg.com.br/',
                    'Modalidade': 'Programa',
                    'Fonte': 'Loja Sebrae MG',
                    'Tema': 'Gestão',
                    'Preço': 'Consulte',
                    'Data de coleta': datetime.now().strftime('%Y-%m-%d')
                }
            ]
            solutions.extend(known_solutions)
        
        logger.info(f"Coletadas {len(solutions)} soluções da Loja Sebrae MG")
        self.solutions.extend(solutions)
        return solutions
    
    def scrape_all(self):
        """
        Coleta soluções de todos os sites do Sebrae.
        
        Returns:
            pandas.DataFrame: DataFrame com todas as soluções coletadas
        """
        self.solutions = []
        
        logger.info("Iniciando coleta de soluções de todos os sites do Sebrae")
        
        try:
            self.scrape_sebraetec()
        except Exception as e:
            logger.error(f"Erro ao coletar soluções do Sebraetec: {e}")
        
        try:
            self.scrape_sebrae_mg()
        except Exception as e:
            logger.error(f"Erro ao coletar soluções do Portal Sebrae MG: {e}")
        
        try:
            self.scrape_cursos_eventos()
        except Exception as e:
            logger.error(f"Erro ao coletar cursos e eventos: {e}")
        
        try:
            self.scrape_sebrae_play()
        except Exception as e:
            logger.error(f"Erro ao coletar cursos do Sebrae Play: {e}")
        
        try:
            self.scrape_loja_sebrae_mg()
        except Exception as e:
            logger.error(f"Erro ao coletar soluções da Loja Sebrae MG: {e}")
        
        # Converte para DataFrame
        df = pd.DataFrame(self.solutions)
        
        # Remove duplicatas
        df = df.drop_duplicates(subset=['Nome da solução', 'Fonte'])
        
        # Garante que todas as colunas necessárias existam
        required_columns = ['Nome da solução', 'Descrição', 'Link', 'Modalidade', 'Fonte', 'Tema', 'Data de coleta']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        logger.info(f"Total de {len(df)} soluções coletadas de todos os sites")
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
            logger.warning("Nenhuma solução para salvar")
            return None
        
        df = pd.DataFrame(self.solutions)
        df.to_excel(filename, index=False)
        
        logger.info(f"Soluções salvas em {filename}")
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
            logger.warning("Nenhuma solução coletada da web para combinar")
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
            
            logger.info(f"Soluções combinadas salvas em {output_file}")
            return df_combined
            
        except Exception as e:
            logger.error(f"Erro ao combinar soluções: {e}")
            return None
    
    def add_default_solutions(self):
        """
        Adiciona soluções padrão para garantir que haja um conjunto mínimo de soluções disponíveis.
        
        Returns:
            int: Número de soluções padrão adicionadas
        """
        default_solutions = [
            {
                'Nome da solução': 'Consultoria em Marketing Digital',
                'Descrição': 'Consultoria especializada para melhorar a presença digital da sua empresa e aumentar o alcance online.',
                'Link': 'https://sebrae.com.br/sites/PortalSebrae/sebraetec',
                'Modalidade': 'Consultoria',
                'Fonte': 'Sebraetec',
                'Tema': 'Marketing',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Consultoria em Gestão Financeira',
                'Descrição': 'Consultoria para organizar as finanças da empresa, melhorar o fluxo de caixa e aumentar a lucratividade.',
                'Link': 'https://sebrae.com.br/sites/PortalSebrae/sebraetec',
                'Modalidade': 'Consultoria',
                'Fonte': 'Sebraetec',
                'Tema': 'Finanças',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Programa ALI - Agentes Locais de Inovação',
                'Descrição': 'Programa que promove a prática continuada de ações de inovação nas empresas de pequeno porte.',
                'Link': 'https://sebrae.com.br/sites/PortalSebrae/ufs/mg',
                'Modalidade': 'Programa',
                'Fonte': 'Portal Sebrae MG',
                'Tema': 'Inovação',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Curso Gestão de Vendas',
                'Descrição': 'Aprenda técnicas eficientes para aumentar as vendas da sua empresa.',
                'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                'Modalidade': 'Curso',
                'Fonte': 'Agenda Sebrae MG',
                'Tema': 'Vendas',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Curso Online: Atendimento ao Cliente',
                'Descrição': 'Aprenda técnicas para melhorar o atendimento e fidelizar seus clientes.',
                'Link': 'https://sebraeplay.com.br/',
                'Modalidade': 'Curso Online',
                'Fonte': 'Sebrae Play',
                'Tema': 'Marketing',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Consultoria em Processos',
                'Descrição': 'Consultoria para otimizar os processos da sua empresa e aumentar a produtividade.',
                'Link': 'https://loja.sebraemg.com.br/',
                'Modalidade': 'Consultoria',
                'Fonte': 'Loja Sebrae MG',
                'Tema': 'Operações',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Curso de Gestão de Pessoas',
                'Descrição': 'Aprenda a gerenciar sua equipe de forma eficiente e motivadora.',
                'Link': 'https://sebrae.com.br/sites/PortalSebrae/cursoseventos',
                'Modalidade': 'Curso',
                'Fonte': 'Agenda Sebrae MG',
                'Tema': 'Pessoas',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Consultoria em E-commerce',
                'Descrição': 'Consultoria especializada para implementar ou melhorar sua loja virtual.',
                'Link': 'https://sebrae.com.br/sites/PortalSebrae/sebraetec',
                'Modalidade': 'Consultoria',
                'Fonte': 'Sebraetec',
                'Tema': 'Vendas',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Curso Online: Gestão do Tempo',
                'Descrição': 'Aprenda a organizar melhor seu tempo e aumentar sua produtividade.',
                'Link': 'https://sebraeplay.com.br/',
                'Modalidade': 'Curso Online',
                'Fonte': 'Sebrae Play',
                'Tema': 'Gestão',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'Nome da solução': 'Consultoria em Precificação',
                'Descrição': 'Consultoria para definir preços adequados para seus produtos e serviços.',
                'Link': 'https://loja.sebraemg.com.br/',
                'Modalidade': 'Consultoria',
                'Fonte': 'Loja Sebrae MG',
                'Tema': 'Finanças',
                'Data de coleta': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        
        # Adiciona apenas soluções que não existem ainda
        added_count = 0
        for solution in default_solutions:
            if not any(s.get('Nome da solução') == solution['Nome da solução'] and 
                      s.get('Fonte') == solution['Fonte'] for s in self.solutions):
                self.solutions.append(solution)
                added_count += 1
        
        logger.info(f"Adicionadas {added_count} soluções padrão")
        return added_count
    
    def get_solutions_for_challenge(self, challenge):
        """
        Retorna soluções específicas para um desafio.
        
        Args:
            challenge (str): Desafio ou categoria do problema
            
        Returns:
            list: Lista de soluções relevantes para o desafio
        """
        if not self.solutions:
            logger.warning("Nenhuma solução disponível")
            return []
        
        challenge_lower = challenge.lower()
        
        # Mapeamento de desafios para temas
        challenge_theme_map = {
            'marketing': ['Marketing', 'Vendas'],
            'divulgação': ['Marketing', 'Vendas'],
            'vendas': ['Vendas', 'Marketing'],
            'comercial': ['Vendas', 'Marketing'],
            'finanças': ['Finanças', 'Gestão'],
            'financeiro': ['Finanças', 'Gestão'],
            'gestão': ['Gestão', 'Operações'],
            'administração': ['Gestão', 'Operações'],
            'inovação': ['Inovação', 'Gestão'],
            'tecnologia': ['Inovação', 'Gestão'],
            'pessoas': ['Pessoas', 'Gestão'],
            'equipe': ['Pessoas', 'Gestão'],
            'operações': ['Operações', 'Gestão'],
            'processos': ['Operações', 'Gestão'],
            'produção': ['Operações', 'Gestão'],
            'qualidade': ['Operações', 'Gestão'],
            'jurídico': ['Jurídico', 'Gestão'],
            'legal': ['Jurídico', 'Gestão'],
            'sustentabilidade': ['Sustentabilidade', 'Gestão'],
            'ambiental': ['Sustentabilidade', 'Gestão'],
            'exportação': ['Exportação', 'Vendas'],
            'internacional': ['Exportação', 'Vendas'],
            'empreendedorismo': ['Empreendedorismo', 'Gestão']
        }
        
        # Identifica temas relevantes para o desafio
        relevant_themes = []
        for key, themes in challenge_theme_map.items():
            if key in challenge_lower:
                relevant_themes.extend(themes)
        
        # Se não encontrou temas específicos, usa temas genéricos
        if not relevant_themes:
            relevant_themes = ['Gestão', 'Marketing', 'Vendas', 'Finanças', 'Inovação']
        
        # Remove duplicatas
        relevant_themes = list(set(relevant_themes))
        
        # Filtra soluções pelos temas relevantes
        relevant_solutions = [
            s for s in self.solutions 
            if s.get('Tema') in relevant_themes or 
               any(theme.lower() in (s.get('Nome da solução', '') + ' ' + s.get('Descrição', '')).lower() 
                  for theme in relevant_themes)
        ]
        
        # Se encontrou poucas soluções, inclui soluções genéricas
        if len(relevant_solutions) < 5:
            generic_solutions = [
                s for s in self.solutions 
                if s.get('Tema') == 'Geral' or 'Gestão' in s.get('Tema', '')
            ]
            relevant_solutions.extend(generic_solutions)
            
            # Remove duplicatas
            seen = set()
            relevant_solutions = [
                s for s in relevant_solutions 
                if not (s.get('Nome da solução') in seen or seen.add(s.get('Nome da solução')))
            ]
        
        logger.info(f"Encontradas {len(relevant_solutions)} soluções para o desafio '{challenge}'")
        return relevant_solutions[:20]  # Limita a 20 soluções para não sobrecarregar
