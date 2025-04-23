import pandas as pd
import os
import glob
import logging
from sebrae_scraper_improved import SebraeScraper

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('data_integration')

class DataIntegration:
    def __init__(self, debug=False):
        """
        Inicializa a integração de dados para o Radar de Inovação ALI 360.
        
        Args:
            debug (bool): Se True, ativa o modo de depuração com mais logs
        """
        self.radar_data = None
        self.solutions_data = None
        self.web_solutions = None
        self.combined_solutions = None
        self.debug = debug
        
        if debug:
            logger.setLevel(logging.DEBUG)
    
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
                    logger.info(f"Usando arquivo de radar: {file_path}")
                else:
                    logger.warning(f"Nenhum arquivo de radar encontrado em {file_path}")
                    return None
            
            # Carrega o arquivo Excel
            df = pd.read_excel(file_path)
            logger.info(f"Dados do radar carregados com sucesso: {len(df)} registros")
            
            # Exibe informações sobre as colunas para depuração
            if self.debug:
                logger.debug(f"Colunas do radar: {df.columns.tolist()}")
                logger.debug(f"Primeiros registros do radar:\n{df.head()}")
            
            self.radar_data = df
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar dados do radar: {e}")
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
                    logger.info(f"Usando arquivo de soluções: {file_path}")
                else:
                    logger.warning(f"Nenhum arquivo de soluções encontrado em {file_path}")
                    return None
            
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
            
            # Exibe informações sobre as colunas para depuração
            if self.debug:
                logger.debug(f"Colunas das soluções: {df.columns.tolist()}")
                logger.debug(f"Primeiros registros das soluções:\n{df.head()}")
            
            logger.info(f"Soluções carregadas com sucesso: {len(df)} registros")
            self.solutions_data = df
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar soluções: {e}")
            return None
    
    def scrape_web_solutions(self):
        """
        Coleta soluções dos sites do Sebrae usando o scraper melhorado.
        
        Returns:
            pandas.DataFrame: DataFrame com as soluções coletadas da web
        """
        try:
            logger.info("Iniciando coleta de soluções dos sites do Sebrae")
            scraper = SebraeScraper(debug=self.debug)
            df = scraper.scrape_all()
            
            # Garante que temos um conjunto mínimo de soluções
            if len(df) < 20:
                logger.warning(f"Poucas soluções coletadas ({len(df)}). Adicionando soluções padrão.")
                scraper.add_default_solutions()
                df = pd.DataFrame(scraper.solutions)
            
            # Exibe informações sobre as colunas para depuração
            if self.debug:
                logger.debug(f"Colunas das soluções web: {df.columns.tolist()}")
                logger.debug(f"Primeiros registros das soluções web:\n{df.head()}")
            
            logger.info(f"Soluções coletadas da web: {len(df)} registros")
            self.web_solutions = df
            return df
        except Exception as e:
            logger.error(f"Erro ao coletar soluções da web: {e}")
            # Cria um DataFrame vazio com as colunas necessárias
            df = pd.DataFrame(columns=['Nome da solução', 'Descrição', 'Link', 'Modalidade', 'Fonte', 'Tema'])
            self.web_solutions = df
            return df
    
    def combine_solutions(self):
        """
        Combina as soluções da planilha Excel com as soluções coletadas da web.
        
        Returns:
            pandas.DataFrame: DataFrame com as soluções combinadas
        """
        try:
            # Se não temos soluções da planilha, usamos apenas as da web
            if self.solutions_data is None or len(self.solutions_data) == 0:
                logger.warning("Nenhuma solução carregada da planilha Excel. Usando apenas soluções da web.")
                if self.web_solutions is not None:
                    self.combined_solutions = self.web_solutions.copy()
                    return self.combined_solutions
                else:
                    logger.error("Nenhuma solução disponível (nem da planilha, nem da web)")
                    return None
            
            # Se não temos soluções da web, usamos apenas as da planilha
            if self.web_solutions is None or len(self.web_solutions) == 0:
                logger.warning("Nenhuma solução coletada da web. Usando apenas soluções da planilha.")
                self.combined_solutions = self.solutions_data.copy()
                return self.combined_solutions
            
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
            
            # Garante que todas as colunas necessárias existam
            required_columns = ['Nome da solução', 'Descrição', 'Modalidade', 'Tema', 'Fonte']
            for col in required_columns:
                if col not in df_combined.columns:
                    df_combined[col] = ''
            
            # Preenche valores nulos
            for col in df_combined.columns:
                if df_combined[col].dtype == 'object':
                    df_combined[col] = df_combined[col].fillna('')
            
            logger.info(f"Soluções combinadas: {len(df_combined)} registros")
            self.combined_solutions = df_combined
            return df_combined
            
        except Exception as e:
            logger.error(f"Erro ao combinar soluções: {e}")
            return None
    
    def preprocess_radar_data(self):
        """
        Pré-processa os dados do radar para uso no sistema de recomendação.
        
        Returns:
            pandas.DataFrame: DataFrame pré-processado
        """
        if self.radar_data is None:
            logger.error("Nenhum dado do radar carregado")
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
            
            # Exibe informações sobre as colunas para depuração
            if self.debug:
                logger.debug(f"Colunas do radar pré-processado: {df.columns.tolist()}")
                logger.debug(f"Primeiros registros do radar pré-processado:\n{df.head()}")
            
            logger.info(f"Dados do radar pré-processados: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao pré-processar dados do radar: {e}")
            return None
    
    def preprocess_solutions_data(self):
        """
        Pré-processa os dados de soluções para uso no sistema de recomendação.
        
        Returns:
            pandas.DataFrame: DataFrame pré-processado
        """
        if self.combined_solutions is None:
            logger.error("Nenhuma solução combinada disponível")
            return None
        
        try:
            df = self.combined_solutions.copy()
            
            # Trata valores nulos
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('')
            
            # Garante que todas as colunas necessárias existam
            required_columns = ['Nome da solução', 'Descrição', 'Modalidade', 'Tema', 'Fonte']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Exibe informações sobre as colunas para depuração
            if self.debug:
                logger.debug(f"Colunas das soluções pré-processadas: {df.columns.tolist()}")
                logger.debug(f"Primeiros registros das soluções pré-processadas:\n{df.head()}")
            
            logger.info(f"Dados de soluções pré-processados: {len(df)} registros")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao pré-processar dados de soluções: {e}")
            return None
    
    def get_company_data(self, company_name):
        """
        Obtém dados de uma empresa específica.
        
        Args:
            company_name (str): Nome da empresa
            
        Returns:
            dict: Dicionário com dados da empresa
        """
        if self.radar_data is None:
            logger.error("Nenhum dado do radar carregado")
            return None
        
        try:
            df = self.preprocess_radar_data()
            
            # Verifica se a coluna de nome da empresa existe
            company_col = None
            for col in ['Nome da empresa', 'Empresa', 'Nome Empresa']:
                if col in df.columns:
                    company_col = col
                    break
            
            if company_col is None:
                logger.error("Coluna de nome da empresa não encontrada")
                return None
            
            # Filtra por nome da empresa
            company_data = df[df[company_col] == company_name]
            
            if len(company_data) == 0:
                logger.warning(f"Empresa '{company_name}' não encontrada")
                return None
            
            # Obtém o primeiro registro (caso haja mais de um)
            company_data = company_data.iloc[0].to_dict()
            
            # Adiciona campos padrão se não existirem
            default_fields = {
                'Desafio priorizado': '',
                'Necessidade específica': '',
                'Maturidade em inovação': 0,
                'Estágio do diagnóstico': '',
                'Regional': '',
                'Cidade': '',
                'Setor': ''
            }
            
            for field, default_value in default_fields.items():
                if field not in company_data or pd.isna(company_data[field]):
                    company_data[field] = default_value
            
            return company_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados da empresa: {e}")
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
            logger.error("Nenhum dado do radar carregado")
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
            logger.error(f"Erro ao obter dados da regional: {e}")
            return None
    
    def get_solutions_for_company(self, company_name):
        """
        Obtém soluções recomendadas para uma empresa específica com base em seu desafio.
        
        Args:
            company_name (str): Nome da empresa
            
        Returns:
            pandas.DataFrame: DataFrame com soluções recomendadas
        """
        if self.combined_solutions is None:
            logger.error("Nenhuma solução combinada disponível")
            return None
        
        try:
            # Obtém dados da empresa
            company_data = self.get_company_data(company_name)
            
            if company_data is None:
                logger.warning(f"Empresa '{company_name}' não encontrada")
                return None
            
            # Obtém o desafio priorizado
            challenge = company_data.get('Desafio priorizado', '')
            
            if not challenge:
                logger.warning(f"Empresa '{company_name}' não tem desafio priorizado")
                return None
            
            # Cria um scraper para usar o método de busca de soluções por desafio
            scraper = SebraeScraper()
            scraper.solutions = self.combined_solutions.to_dict('records')
            
            # Obtém soluções para o desafio
            solutions = scraper.get_solutions_for_challenge(challenge)
            
            if not solutions:
                logger.warning(f"Nenhuma solução encontrada para o desafio '{challenge}'")
                return None
            
            # Converte para DataFrame
            df_solutions = pd.DataFrame(solutions)
            
            # Adiciona coluna de relevância (para ordenação)
            df_solutions['Relevância'] = 1.0
            
            # Adiciona coluna de regional da empresa
            df_solutions['Regional da empresa'] = company_data.get('Regional', '')
            
            # Adiciona coluna de cidade da empresa
            df_solutions['Cidade da empresa'] = company_data.get('Cidade', '')
            
            # Adiciona coluna de desafio da empresa
            df_solutions['Desafio da empresa'] = challenge
            
            # Adiciona coluna de necessidade específica da empresa
            df_solutions['Necessidade específica'] = company_data.get('Necessidade específica', '')
            
            # Ordena por relevância
            df_solutions = df_solutions.sort_values('Relevância', ascending=False)
            
            logger.info(f"Encontradas {len(df_solutions)} soluções para a empresa '{company_name}'")
            return df_solutions
            
        except Exception as e:
            logger.error(f"Erro ao obter soluções para a empresa: {e}")
            return None
    
    def get_all_companies(self):
        """
        Obtém a lista de todas as empresas.
        
        Returns:
            list: Lista com nomes das empresas
        """
        if self.radar_data is None:
            logger.error("Nenhum dado do radar carregado")
            return []
        
        try:
            df = self.preprocess_radar_data()
            
            # Verifica se a coluna de nome da empresa existe
            company_col = None
            for col in ['Nome da empresa', 'Empresa', 'Nome Empresa']:
                if col in df.columns:
                    company_col = col
                    break
            
            if company_col is None:
                logger.error("Coluna de nome da empresa não encontrada")
                return []
            
            # Obtém a lista de empresas
            companies = df[company_col].unique().tolist()
            
            logger.info(f"Encontradas {len(companies)} empresas")
            return companies
            
        except Exception as e:
            logger.error(f"Erro ao obter lista de empresas: {e}")
            return []
    
    def get_all_solutions(self):
        """
        Obtém a lista de todas as soluções.
        
        Returns:
            pandas.DataFrame: DataFrame com todas as soluções
        """
        if self.combined_solutions is None:
            logger.error("Nenhuma solução combinada disponível")
            return None
        
        try:
            df = self.preprocess_solutions_data()
            
            logger.info(f"Retornando {len(df)} soluções")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao obter lista de soluções: {e}")
            return None
    
    def get_all_regions(self):
        """
        Obtém a lista de todas as regionais.
        
        Returns:
            list: Lista com nomes das regionais
        """
        if self.radar_data is None:
            logger.error("Nenhum dado do radar carregado")
            return []
        
        try:
            df = self.preprocess_radar_data()
            
            # Verifica se a coluna de regional existe
            if 'Regional' not in df.columns:
                logger.error("Coluna de regional não encontrada")
                return []
            
            # Obtém a lista de regionais
            regions = df['Regional'].unique().tolist()
            
            # Remove valores vazios
            regions = [r for r in regions if r]
            
            logger.info(f"Encontradas {len(regions)} regionais")
            return regions
            
        except Exception as e:
            logger.error(f"Erro ao obter lista de regionais: {e}")
            return []
    
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
                logger.info(f"Dados do radar processados salvos em {radar_output}")
            
            if self.combined_solutions is not None:
                df_solutions = self.preprocess_solutions_data()
                df_solutions.to_excel(solutions_output, index=False)
                solutions_path = solutions_output
                logger.info(f"Soluções processadas salvas em {solutions_output}")
            
            return radar_path, solutions_path
            
        except Exception as e:
            logger.error(f"Erro ao salvar dados processados: {e}")
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
        try:
            # Carrega dados do radar
            logger.info(f"Carregando dados do radar de {radar_file}")
            self.load_radar_data_from_excel(radar_file)
            
            # Carrega soluções da planilha
            logger.info(f"Carregando soluções da planilha de {solutions_file}")
            self.load_solutions_from_excel(solutions_file)
            
            # Coleta soluções da web
            logger.info("Coletando soluções da web")
            self.scrape_web_solutions()
            
            # Combina as soluções
            logger.info("Combinando soluções")
            self.combine_solutions()
            
            # Pré-processa os dados
            logger.info("Pré-processando dados")
            radar_processed = self.preprocess_radar_data()
            solutions_processed = self.preprocess_solutions_data()
            
            # Salva os dados processados
            logger.info("Salvando dados processados")
            self.save_processed_data()
            
            return radar_processed, solutions_processed
            
        except Exception as e:
            logger.error(f"Erro ao processar todos os dados: {e}")
            return None, None
