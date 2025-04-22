import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import os
import json

class GoogleSheetsIntegration:
    def __init__(self):
        """
        Inicializa a integração com o Google Sheets.
        Requer um arquivo de credenciais para autenticação.
        """
        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']
        self.credentials_path = 'credentials.json'
        self.client = None
        
    def create_credentials_file(self, credentials_json):
        """
        Cria um arquivo de credenciais a partir de uma string JSON.
        
        Args:
            credentials_json (str): String JSON com as credenciais do Google API
        """
        with open(self.credentials_path, 'w') as f:
            f.write(credentials_json)
        
    def authenticate(self):
        """
        Autentica com a API do Google usando as credenciais fornecidas.
        
        Returns:
            bool: True se a autenticação for bem-sucedida, False caso contrário
        """
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_path, self.scope)
            self.client = gspread.authorize(credentials)
            return True
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return False
    
    def get_worksheet_data(self, spreadsheet_url, worksheet_index=0):
        """
        Obtém dados de uma planilha específica.
        
        Args:
            spreadsheet_url (str): URL da planilha do Google Sheets
            worksheet_index (int): Índice da aba da planilha (0 por padrão)
            
        Returns:
            pandas.DataFrame: DataFrame com os dados da planilha
        """
        try:
            # Abre a planilha pelo URL
            spreadsheet = self.client.open_by_url(spreadsheet_url)
            
            # Seleciona a aba da planilha
            worksheet = spreadsheet.get_worksheet(worksheet_index)
            
            # Obtém todos os valores da planilha
            data = worksheet.get_all_records()
            
            # Converte para DataFrame do pandas
            df = pd.DataFrame(data)
            
            return df
        
        except Exception as e:
            print(f"Erro ao obter dados da planilha: {e}")
            return None
    
    def get_all_worksheets_data(self, spreadsheet_url):
        """
        Obtém dados de todas as abas de uma planilha.
        
        Args:
            spreadsheet_url (str): URL da planilha do Google Sheets
            
        Returns:
            dict: Dicionário com os nomes das abas como chaves e DataFrames como valores
        """
        try:
            # Abre a planilha pelo URL
            spreadsheet = self.client.open_by_url(spreadsheet_url)
            
            # Obtém todas as abas da planilha
            worksheets = spreadsheet.worksheets()
            
            # Dicionário para armazenar os DataFrames
            dfs = {}
            
            # Obtém dados de cada aba
            for worksheet in worksheets:
                data = worksheet.get_all_records()
                dfs[worksheet.title] = pd.DataFrame(data)
            
            return dfs
        
        except Exception as e:
            print(f"Erro ao obter dados de todas as abas: {e}")
            return None
    
    def update_worksheet(self, spreadsheet_url, data, worksheet_name=None, worksheet_index=0):
        """
        Atualiza dados em uma planilha específica.
        
        Args:
            spreadsheet_url (str): URL da planilha do Google Sheets
            data (pandas.DataFrame): DataFrame com os dados a serem atualizados
            worksheet_name (str): Nome da aba da planilha (opcional)
            worksheet_index (int): Índice da aba da planilha (0 por padrão)
            
        Returns:
            bool: True se a atualização for bem-sucedida, False caso contrário
        """
        try:
            # Abre a planilha pelo URL
            spreadsheet = self.client.open_by_url(spreadsheet_url)
            
            # Seleciona a aba da planilha
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.get_worksheet(worksheet_index)
            
            # Converte o DataFrame para lista de listas
            values = [data.columns.tolist()] + data.values.tolist()
            
            # Limpa a planilha atual
            worksheet.clear()
            
            # Atualiza a planilha com os novos valores
            worksheet.update(values)
            
            return True
        
        except Exception as e:
            print(f"Erro ao atualizar planilha: {e}")
            return False
    
    def create_worksheet(self, spreadsheet_url, worksheet_name, data=None):
        """
        Cria uma nova aba em uma planilha existente.
        
        Args:
            spreadsheet_url (str): URL da planilha do Google Sheets
            worksheet_name (str): Nome da nova aba
            data (pandas.DataFrame): DataFrame com os dados a serem inseridos (opcional)
            
        Returns:
            gspread.Worksheet: Objeto da nova aba criada, ou None em caso de erro
        """
        try:
            # Abre a planilha pelo URL
            spreadsheet = self.client.open_by_url(spreadsheet_url)
            
            # Cria uma nova aba
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=100, cols=20)
            
            # Se houver dados, insere na nova aba
            if data is not None:
                values = [data.columns.tolist()] + data.values.tolist()
                worksheet.update(values)
            
            return worksheet
        
        except Exception as e:
            print(f"Erro ao criar nova aba: {e}")
            return None
