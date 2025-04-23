import pandas as pd
import os
from google_sheets_integration import GoogleSheetsIntegration
from sebrae_scraper import SebraeScraper

class DataIntegration:
    def __init__(self):
        """
        Inicializa a integração de dados para o Radar de Inovação ALI 360.
        """
        self.radar_data = None
        self.solutions_data = None
        self.web_solutions = None
        self.combined_solutions = None
        
    def load_radar_data_from_excel(self, file_path):
        """
        Carrega os dados do Radar de Inovação ALI 360 a partir de um arquivo Excel.
        
        Args:
            file_path (str): Caminho do arquivo Excel ou diretório contendo o arquivo
            
        Returns:
            pandas.DataFrame: DataFrame com os dados do radar
        """
        try:
            # Verifica se o caminho é um diretório
            if os.path.isdir(file_path):
                # Procura por arquivos que correspondem ao padrão
                xlsx_files = glob.glob(os.path.join(file_path, '*.xlsx'))
                radar_file = [f for f in xlsx_files if '24.2' in f]
                if radar_file:
                    file_path = radar_file[0]
            
            # Carrega o arquivo Excel
            df = pd.read_excel(file_path)
            print(f"Dados do radar carregados com sucesso: {len(df)} registros")
            self.radar_data = df
            return df
        except Exception as e:
            print(f"Erro ao carregar dados do radar: {e}")
            return None
        """
        Carrega os dados do Radar de Inovação ALI 360 a partir de um arquivo Excel.
        
        Args:
            file_path (str): Caminho do arquivo Excel
            
        Returns:
            pandas.DataFrame: DataFrame com os dados do radar
        """
        try:
            df = pd.read_excel(file_path)
            print(f"Dados do radar carregados com sucesso: {len(df)} registros")
            self.radar_data = df
            return df
        except Exception as e:
            print(f"Erro ao carregar dados do radar: {e}")
            return None
    
    def load_solutions_from_excel(self, file_path):
        """
        Carrega as soluções do Sebrae a partir de um arquivo Excel.
        
        Args:
            file_path (str): Caminho do arquivo Excel ou diretório contendo o arquivo
            
        Returns:
            pandas.DataFrame: DataFrame com as soluções
        """
        try:
            # Verifica se o caminho é um diretório
            if os.path.isdir(file_path):
                # Procura por arquivos que correspondem ao padrão
                xlsx_files = glob.glob(os.path.join(file_path, '*.xlsx'))
                solutions_file = [f for f in xlsx_files if 'Solu' in f]
                if solutions_file:
                    file_path = solutions_file[0]
            
            # Carrega o arquivo Excel
            df = pd.read_excel(file_path)
            
            # Renomeia colunas para padronizar
            column_mapping = {
                'Ação Destaque': 'Nome da solução',
                'Objetivo': 'Descrição',
                'Cidade': 'Cidade',
                'Regional': 'Regional',
                'Setor': 'Setor',
                'Segmento / Grupo': 'Segmento',
                'Público Alvo': 'Público-alvo',
                'Instrumento': 'Modalidade',
                'Estratégia': 'Tema',
                'Maturidade': 'Maturidade'
            }
            
            # Aplica o mapeamento apenas para colunas que existem
            valid_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=valid_columns)
            
            # Adiciona coluna de fonte
            df['Fonte'] = 'Planilha Soluções Sebrae'
            
            print(f"Soluções carregadas com sucesso: {len(df)} registros")
            self.solutions_data = df
            return df
        except Exception as e:
            print(f"Erro ao carregar soluções: {e}")
            return None
        """
        Carrega as soluções do Sebrae a partir de um arquivo Excel.
        
        Args:
            file_path (str): Caminho do arquivo Excel
            
        Returns:
            pandas.DataFrame: DataFrame com as soluções
        """
        try:
            df = pd.read_excel(file_path)
            
            # Renomeia colunas para padronizar
            column_mapping = {
                'Ação Destaque': 'Nome da solução',
                'Objetivo': 'Descrição',
                'Cidade': 'Cidade',
                'Regional': 'Regional',
                'Setor': 'Setor',
                'Segmento / Grupo': 'Segmento',
                'Público Alvo': 'Público-alvo',
                'Instrumento': 'Modalidade',
                'Estratégia': 'Tema',
                'Maturidade': 'Maturidade'
            }
            
            # Aplica o mapeamento apenas para colunas que existem
            valid_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=valid_columns)
            
            # Adiciona coluna de fonte
            df['Fonte'] = 'Planilha Soluções Sebrae'
            
            print(f"Soluções carregadas com sucesso: {len(df)} registros")
            self.solutions_data = df
            return df
        except Exception as e:
            print(f"Erro ao carregar soluções: {e}")
            return None
    
    def scrape_web_solutions(self):
        """
        Coleta soluções dos sites do Sebrae.
        
        Returns:
            pandas.DataFrame: DataFrame com as soluções coletadas da web
        """
        try:
            scraper = SebraeScraper()
            df = scraper.scrape_all()
            
            print(f"Soluções coletadas da web: {len(df)} registros")
            self.web_solutions = df
            return df
        except Exception as e:
            print(f"Erro ao coletar soluções da web: {e}")
            return None
    
    def combine_solutions(self):
        """
        Combina as soluções da planilha Excel com as soluções coletadas da web.
        
        Returns:
            pandas.DataFrame: DataFrame com as soluções combinadas
        """
        if self.solutions_data is None:
            print("Nenhuma solução carregada da planilha Excel")
            return None
        
        if self.web_solutions is None:
            print("Nenhuma solução coletada da web")
            return self.solutions_data
        
        try:
            # Seleciona colunas relevantes da planilha de soluções
            excel_cols = ['Nome da solução', 'Descrição', 'Cidade', 'Regional', 
                         'Modalidade', 'Tema', 'Público-alvo', 'Fonte']
            excel_cols = [col for col in excel_cols if col in self.solutions_data.columns]
            df_excel = self.solutions_data[excel_cols].copy()
            
            # Seleciona colunas relevantes das soluções web
            web_cols = ['Nome da solução', 'Descrição', 'Modalidade', 
                       'Tema', 'Fonte', 'Link', 'Data de coleta']
            web_cols = [col for col in web_cols if col in self.web_solutions.columns]
            df_web = self.web_solutions[web_cols].copy()
            
            # Adiciona colunas faltantes
            for col in excel_cols:
                if col not in df_web.columns:
                    df_web[col] = None
            
            for col in web_cols:
                if col not in df_excel.columns:
                    df_excel[col] = None
            
            # Combina os DataFrames
            df_combined = pd.concat([df_excel, df_web], ignore_index=True)
            
            # Remove duplicatas
            df_combined = df_combined.drop_duplicates(subset=['Nome da solução', 'Fonte'])
            
            print(f"Soluções combinadas: {len(df_combined)} registros")
            self.combined_solutions = df_combined
            return df_combined
            
        except Exception as e:
            print(f"Erro ao combinar soluções: {e}")
            return None
    
    def preprocess_radar_data(self):
        """
        Pré-processa os dados do radar para uso no sistema de recomendação.
        
        Returns:
            pandas.DataFrame: DataFrame pré-processado
        """
        if self.radar_data is None:
            print("Nenhum dado do radar carregado")
            return None
        
        try:
            df = self.radar_data.copy()
            
            # Renomeia colunas para padronizar
            column_mapping = {
                'Nome Empresa': 'Nome da empresa',
                'Escritório Regional': 'Regional',
                'Município': 'Cidade',
                'Categoria do Problema': 'Desafio priorizado',
                'Descrição do Problema': 'Necessidade específica',
                'Média diagnóstico inicial': 'Maturidade em inovação',
                'Encontro': 'Estágio do diagnóstico'
            }
            
            # Aplica o mapeamento apenas para colunas que existem
            valid_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            df = df.rename(columns=valid_columns)
            
            # Mapeia valores de estágio do diagnóstico
            if 'Estágio do diagnóstico' in df.columns:
                stage_mapping = {
                    1: 'Nomear',
                    2: 'Elaborar',
                    3: 'Experimentar',
                    4: 'Evoluir',
                    5: 'Concluído'
                }
                df['Estágio do diagnóstico'] = df['Estágio do diagnóstico'].map(lambda x: stage_mapping.get(x, x))
            
            # Trata valores nulos
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('')
            
            print(f"Dados do radar pré-processados: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"Erro ao pré-processar dados do radar: {e}")
            return None
    
    def preprocess_solutions_data(self):
        """
        Pré-processa os dados de soluções para uso no sistema de recomendação.
        
        Returns:
            pandas.DataFrame: DataFrame pré-processado
        """
        if self.combined_solutions is None:
            print("Nenhuma solução combinada disponível")
            return None
        
        try:
            df = self.combined_solutions.copy()
            
            # Trata valores nulos
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('')
            
            # Garante que todas as colunas necessárias existam
            required_columns = ['Nome da solução', 'Descrição', 'Modalidade', 'Tema']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            print(f"Dados de soluções pré-processados: {len(df)} registros")
            return df
            
        except Exception as e:
            print(f"Erro ao pré-processar dados de soluções: {e}")
            return None
    
    def get_regional_data(self, regional=None):
        """
        Obtém dados agregados de uma regional específica ou de todas as regionais.
        
        Args:
            regional (str): Nome da regional (opcional)
            
        Returns:
            dict: Dicionário com dados agregados
        """
        if self.radar_data is None:
            print("Nenhum dado do radar carregado")
            return None
        
        try:
            df = self.preprocess_radar_data()
            
            # Filtra por regional se especificado
            if regional and regional != 'Todas' and 'Regional' in df.columns:
                df = df[df['Regional'] == regional]
            
            # Obtém os desafios mais comuns
            if 'Desafio priorizado' in df.columns:
                top_challenges = df['Desafio priorizado'].value_counts().reset_index()
                top_challenges.columns = ['challenge', 'count']
                top_challenges = top_challenges.to_dict('records')
            else:
                top_challenges = []
            
            # Obtém os setores mais comuns
            if 'Setor' in df.columns:
                top_sectors = df['Setor'].value_counts().reset_index()
                top_sectors.columns = ['sector', 'count']
                top_sectors = top_sectors.to_dict('records')
            else:
                top_sectors = []
            
            # Obtém a distribuição de maturidade
            if 'Maturidade em inovação' in df.columns:
                maturity_distribution = df['Maturidade em inovação'].value_counts().to_dict()
            else:
                maturity_distribution = {}
            
            # Obtém a distribuição de estágios
            if 'Estágio do diagnóstico' in df.columns:
                stage_distribution = df['Estágio do diagnóstico'].value_counts().to_dict()
            else:
                stage_distribution = {}
            
            return {
                'top_challenges': top_challenges,
                'top_sectors': top_sectors,
                'maturity_distribution': maturity_distribution,
                'stage_distribution': stage_distribution,
                'total_companies': len(df)
            }
            
        except Exception as e:
            print(f"Erro ao obter dados da regional: {e}")
            return None
    
    def save_processed_data(self, radar_output="radar_processed.xlsx", solutions_output="solutions_processed.xlsx"):
        """
        Salva os dados processados em arquivos Excel.
        
        Args:
            radar_output (str): Nome do arquivo para dados do radar
            solutions_output (str): Nome do arquivo para soluções
            
        Returns:
            tuple: Caminhos dos arquivos salvos
        """
        radar_path = None
        solutions_path = None
        
        try:
            if self.radar_data is not None:
                df_radar = self.preprocess_radar_data()
                df_radar.to_excel(radar_output, index=False)
                radar_path = radar_output
                print(f"Dados do radar processados salvos em {radar_output}")
            
            if self.combined_solutions is not None:
                df_solutions = self.preprocess_solutions_data()
                df_solutions.to_excel(solutions_output, index=False)
                solutions_path = solutions_output
                print(f"Soluções processadas salvas em {solutions_output}")
            
            return radar_path, solutions_path
            
        except Exception as e:
            print(f"Erro ao salvar dados processados: {e}")
            return radar_path, solutions_path
    
    def process_all_data(self, radar_file, solutions_file):
        """
        Processa todos os dados: carrega arquivos Excel, coleta soluções da web e combina tudo.
        
        Args:
            radar_file (str): Caminho do arquivo Excel com dados do radar
            solutions_file (str): Caminho do arquivo Excel com soluções
            
        Returns:
            tuple: DataFrames processados (radar, soluções)
        """
        # Carrega dados do radar
        self.load_radar_data_from_excel(radar_file)
        
        # Carrega soluções da planilha
        self.load_solutions_from_excel(solutions_file)
        
        # Coleta soluções da web
        self.scrape_web_solutions()
        
        # Combina as soluções
        self.combine_solutions()
        
        # Pré-processa os dados
        radar_processed = self.preprocess_radar_data()
        solutions_processed = self.preprocess_solutions_data()
        
        # Salva os dados processados
        self.save_processed_data()
        
        return radar_processed, solutions_processed
