import pandas as pd
import numpy as np
import re
import os
import openai
from typing import List, Dict, Any

class RecommendationSystem:
    def __init__(self, api_key=None):
        """
        Inicializa o sistema de recomendação baseado na API da OpenAI.
        
        Args:
            api_key (str): Chave da API da OpenAI (opcional, pode ser definida como variável de ambiente)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
        
        # Modelo a ser utilizado
        self.model = "gpt-3.5-turbo"
        
        # Cache para armazenar recomendações e reduzir chamadas à API
        self.recommendation_cache = {}
        
    def set_api_key(self, api_key):
        """
        Define a chave da API da OpenAI.
        
        Args:
            api_key (str): Chave da API da OpenAI
        """
        self.api_key = api_key
        openai.api_key = api_key
    
    def preprocess_text(self, text):
        """
        Pré-processa o texto para melhorar a qualidade das recomendações.
        
        Args:
            text (str): Texto a ser pré-processado
            
        Returns:
            str: Texto pré-processado
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Converte para minúsculas
        text = text.lower()
        
        # Remove caracteres especiais e mantém apenas letras, números e espaços
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def generate_recommendation_prompt(self, company_data, available_solutions, already_scheduled=None):
        """
        Gera o prompt para a API da OpenAI com base nos dados da empresa e soluções disponíveis.
        
        Args:
            company_data (dict): Dados da empresa (desafio, setor, maturidade, etc.)
            available_solutions (list): Lista de soluções disponíveis
            already_scheduled (list): Lista de soluções já agendadas (opcional)
            
        Returns:
            str: Prompt formatado para a API da OpenAI
        """
        # Extrai informações relevantes da empresa
        company_name = company_data.get('Nome da empresa', company_data.get('Nome Empresa', 'Empresa'))
        challenge = company_data.get('Desafio priorizado', company_data.get('Categoria do Problema', ''))
        specific_need = company_data.get('Necessidade específica', company_data.get('Descrição do Problema', ''))
        sector = company_data.get('Setor', '')
        maturity = company_data.get('Maturidade em inovação', company_data.get('Média diagnóstico inicial', ''))
        stage = company_data.get('Estágio do diagnóstico', str(company_data.get('Encontro', '')))
        city = company_data.get('Cidade', company_data.get('Município', ''))
        regional = company_data.get('Regional', company_data.get('Escritório Regional', ''))
        
        # Formata as soluções disponíveis (limitado a 20 para não sobrecarregar o prompt)
        solutions_sample = available_solutions[:20] if len(available_solutions) > 20 else available_solutions
        solutions_text = "\n".join([
            f"- {sol.get('Nome da solução', '')}: {sol.get('Modalidade', '')} | {sol.get('Tema', '')} | {sol.get('Descrição', '')[:100]}..."
            for sol in solutions_sample
        ])
        
        # Formata as soluções já agendadas (se houver)
        scheduled_text = ""
        if already_scheduled and len(already_scheduled) > 0:
            scheduled_text = "Soluções já agendadas para esta empresa ou região:\n" + "\n".join([
                f"- {sol.get('Nome da solução', '')}: {sol.get('Modalidade', '')} | {sol.get('Data prevista', '')}"
                for sol in already_scheduled
            ])
        
        # Constrói o prompt completo
        prompt = f"""
        Você é um consultor especializado do Sebrae MG que recomenda soluções para empresas com base em seus desafios e necessidades.
        
        DADOS DA EMPRESA:
        - Nome: {company_name}
        - Cidade/Regional: {city}/{regional}
        - Setor: {sector}
        - Desafio priorizado: {challenge}
        - Maturidade em inovação: {maturity}
        - Necessidade específica: {specific_need}
        - Estágio do diagnóstico: {stage}
        
        SOLUÇÕES DISPONÍVEIS (amostra das mais relevantes):
        {solutions_text}
        
        {scheduled_text}
        
        TAREFA:
        Recomende as 3 melhores soluções do Sebrae para esta empresa, considerando:
        1. Alinhamento com o desafio priorizado e necessidade específica
        2. Adequação ao setor e maturidade da empresa
        3. Evite recomendar soluções já agendadas
        4. Para cada recomendação, explique por que é adequada para esta empresa
        
        Formato da resposta:
        1. [Nome da Solução 1]: [Justificativa detalhada]
        2. [Nome da Solução 2]: [Justificativa detalhada]
        3. [Nome da Solução 3]: [Justificativa detalhada]
        """
        
        return prompt
    
    def get_recommendations(self, company_data, available_solutions, already_scheduled=None):
        """
        Obtém recomendações de soluções para uma empresa específica.
        
        Args:
            company_data (dict): Dados da empresa
            available_solutions (list): Lista de soluções disponíveis
            already_scheduled (list): Lista de soluções já agendadas (opcional)
            
        Returns:
            list: Lista de recomendações com justificativas
        """
        # Gera uma chave única para o cache
        company_name = company_data.get('Nome da empresa', company_data.get('Nome Empresa', ''))
        challenge = company_data.get('Desafio priorizado', company_data.get('Categoria do Problema', ''))
        cache_key = f"{company_name}-{challenge}"
        
        # Verifica se já existe no cache
        if cache_key in self.recommendation_cache:
            return self.recommendation_cache[cache_key]
        
        # Gera o prompt para a API
        prompt = self.generate_recommendation_prompt(
            company_data, available_solutions, already_scheduled
        )
        
        try:
            # Faz a chamada para a API da OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um consultor especializado do Sebrae MG."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extrai o texto da resposta
            recommendation_text = response.choices[0].message.content.strip()
            
            # Processa o texto para extrair as recomendações
            recommendations = self.parse_recommendations(recommendation_text)
            
            # Armazena no cache
            self.recommendation_cache[cache_key] = recommendations
            
            return recommendations
            
        except Exception as e:
            print(f"Erro ao obter recomendações: {e}")
            return []
    
    def parse_recommendations(self, recommendation_text):
        """
        Analisa o texto da resposta da API para extrair as recomendações.
        
        Args:
            recommendation_text (str): Texto da resposta da API
            
        Returns:
            list: Lista de recomendações estruturadas
        """
        recommendations = []
        
        # Padrão para extrair recomendações numeradas
        pattern = r'(\d+)\.\s+\[([^\]]+)\]:\s+(.*?)(?=\d+\.\s+\[|$)'
        matches = re.findall(pattern, recommendation_text, re.DOTALL)
        
        for match in matches:
            number, solution_name, justification = match
            recommendations.append({
                "number": number.strip(),
                "solution_name": solution_name.strip(),
                "justification": justification.strip()
            })
        
        # Se o padrão não encontrou nada, tenta outro formato
        if not recommendations:
            lines = recommendation_text.split('\n')
            current_rec = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Verifica se é uma nova recomendação
                if line[0].isdigit() and '. ' in line[:10]:
                    if current_rec:
                        recommendations.append(current_rec)
                    
                    parts = line.split(': ', 1)
                    if len(parts) > 1:
                        solution_name = parts[0].split('. ', 1)[1]
                        justification = parts[1]
                        current_rec = {
                            "number": line[0],
                            "solution_name": solution_name,
                            "justification": justification
                        }
                    else:
                        current_rec = {
                            "number": line[0],
                            "solution_name": line[2:],
                            "justification": ""
                        }
                elif current_rec:
                    current_rec["justification"] += " " + line
            
            if current_rec:
                recommendations.append(current_rec)
        
        return recommendations
    
    def calculate_solution_adherence(self, solution, companies_data):
        """
        Calcula a aderência de uma solução para um conjunto de empresas.
        
        Args:
            solution (dict): Dados da solução
            companies_data (list): Lista de dados das empresas
            
        Returns:
            dict: Dicionário com empresas e seus níveis de aderência
        """
        adherence_results = {}
        solution_name = solution.get('Nome da solução', '')
        solution_theme = solution.get('Tema', '')
        solution_modality = solution.get('Modalidade', '')
        solution_description = solution.get('Descrição', '')
        
        # Gera o prompt para a API
        prompt = f"""
        Você é um consultor especializado do Sebrae MG que analisa a aderência de soluções para empresas.
        
        SOLUÇÃO A SER ANALISADA:
        - Nome: {solution_name}
        - Tema: {solution_theme}
        - Modalidade: {solution_modality}
        - Descrição: {solution_description}
        
        Para cada empresa abaixo, avalie a aderência desta solução em uma escala de 0 a 10, onde:
        - 0-3: Baixa aderência (a solução não atende às necessidades da empresa)
        - 4-7: Média aderência (a solução atende parcialmente às necessidades da empresa)
        - 8-10: Alta aderência (a solução atende muito bem às necessidades da empresa)
        
        Forneça também uma breve justificativa para cada avaliação.
        
        EMPRESAS:
        """
        
        # Adiciona dados de até 10 empresas ao prompt para não sobrecarregar
        companies_sample = companies_data[:10]
        for i, company in enumerate(companies_sample):
            company_name = company.get('Nome da empresa', company.get('Nome Empresa', f'Empresa {i+1}'))
            challenge = company.get('Desafio priorizado', company.get('Categoria do Problema', ''))
            specific_need = company.get('Necessidade específica', company.get('Descrição do Problema', ''))
            sector = company.get('Setor', '')
            maturity = company.get('Maturidade em inovação', company.get('Média diagnóstico inicial', ''))
            
            prompt += f"""
            Empresa {i+1}: {company_name}
            - Setor: {sector}
            - Desafio priorizado: {challenge}
            - Maturidade em inovação: {maturity}
            - Necessidade específica: {specific_need}
            """
        
        prompt += """
        FORMATO DA RESPOSTA:
        Para cada empresa, forneça:
        - Empresa X: [Pontuação]/10 - [Justificativa]
        """
        
        try:
            # Faz a chamada para a API da OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um consultor especializado do Sebrae MG."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Extrai o texto da resposta
            adherence_text = response.choices[0].message.content.strip()
            
            # Processa o texto para extrair as aderências
            for i, company in enumerate(companies_sample):
                company_name = company.get('Nome da empresa', company.get('Nome Empresa', f'Empresa {i+1}'))
                
                # Padrão para extrair a pontuação e justificativa
                pattern = rf"Empresa\s+{i+1}.*?:\s+(\d+)/10\s+-\s+(.*?)(?=Empresa|$)"
                match = re.search(pattern, adherence_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    score, justification = match.groups()
                    adherence_results[company_name] = {
                        "score": int(score),
                        "justification": justification.strip()
                    }
                else:
                    adherence_results[company_name] = {
                        "score": 0,
                        "justification": "Não foi possível calcular a aderência."
                    }
            
            return adherence_results
            
        except Exception as e:
            print(f"Erro ao calcular aderência: {e}")
            return {company.get('Nome da empresa', company.get('Nome Empresa', f'Empresa {i+1}')): {"score": 0, "justification": "Erro ao calcular."} 
                   for i, company in enumerate(companies_sample)}
    
    def suggest_new_courses(self, regional_data, scheduled_solutions):
        """
        Sugere novos cursos com base nos dados regionais e soluções já agendadas.
        
        Args:
            regional_data (dict): Dados agregados da regional (desafios, setores, etc.)
            scheduled_solutions (list): Lista de soluções já agendadas
            
        Returns:
            list: Lista de sugestões de novos cursos
        """
        # Extrai informações relevantes da regional
        top_challenges = regional_data.get('top_challenges', [])
        top_sectors = regional_data.get('top_sectors', [])
        maturity_distribution = regional_data.get('maturity_distribution', {})
        
        # Formata os desafios mais comuns
        challenges_text = "\n".join([
            f"- {challenge['challenge']}: {challenge['count']} empresas" for challenge in top_challenges[:10]
        ])
        
        # Formata os setores mais comuns
        sectors_text = "\n".join([
            f"- {sector['sector']}: {sector['count']} empresas" for sector in top_sectors[:10]
        ])
        
        # Formata a distribuição de maturidade
        maturity_text = "\n".join([
            f"- {maturity}: {count} empresas" for maturity, count in maturity_distribution.items()
        ])
        
        # Formata as soluções já agendadas (limitado a 20 para não sobrecarregar o prompt)
        scheduled_sample = scheduled_solutions[:20] if len(scheduled_solutions) > 20 else scheduled_solutions
        scheduled_text = "\n".join([
            f"- {sol.get('Nome da solução', '')}: {sol.get('Modalidade', '')} | {sol.get('Tema', '')}"
            for sol in scheduled_sample
        ])
        
        # Gera o prompt para a API
        prompt = f"""
        Você é um consultor especializado do Sebrae MG que sugere novos cursos e soluções para regiões com base em dados agregados.
        
        DADOS DA REGIONAL:
        
        Desafios mais comuns:
        {challenges_text}
        
        Setores mais comuns:
        {sectors_text}
        
        Distribuição de maturidade em inovação:
        {maturity_text}
        
        Soluções já agendadas:
        {scheduled_text}
        
        TAREFA:
        Sugira 5 novos cursos ou soluções que o Sebrae MG poderia oferecer nesta regional, considerando:
        1. Os desafios e necessidades mais comuns das empresas
        2. Os setores predominantes na região
        3. A distribuição de maturidade em inovação
        4. Evite sugerir soluções similares às já agendadas
        5. Para cada sugestão, explique por que seria benéfica para esta regional
        
        Formato da resposta:
        1. [Nome da Solução Sugerida] ([Modalidade: Curso/Consultoria/Programa]): [Justificativa detalhada]
        2. [Nome da Solução Sugerida] ([Modalidade: Curso/Consultoria/Programa]): [Justificativa detalhada]
        ...
        """
        
        try:
            # Faz a chamada para a API da OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um consultor especializado do Sebrae MG."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            # Extrai o texto da resposta
            suggestions_text = response.choices[0].message.content.strip()
            
            # Processa o texto para extrair as sugestões
            suggestions = []
            pattern = r'(\d+)\.\s+\[([^\]]+)\]\s+\(([^\)]+)\):\s+(.*?)(?=\d+\.\s+\[|$)'
            matches = re.findall(pattern, suggestions_text, re.DOTALL)
            
            for match in matches:
                number, solution_name, modality, justification = match
                suggestions.append({
                    "number": number.strip(),
                    "solution_name": solution_name.strip(),
                    "modality": modality.strip(),
                    "justification": justification.strip()
                })
            
            # Se o padrão não encontrou nada, tenta outro formato
            if not suggestions:
                lines = suggestions_text.split('\n')
                current_sug = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Verifica se é uma nova sugestão
                    if line[0].isdigit() and '. ' in line[:10]:
                        if current_sug:
                            suggestions.append(current_sug)
                        
                        parts = line.split(': ', 1)
                        if len(parts) > 1:
                            header = parts[0].split('. ', 1)[1]
                            justification = parts[1]
                            
                            # Tenta extrair o nome da solução e modalidade
                            header_match = re.match(r'([^\(]+)\s*\(([^\)]+)\)', header)
                            if header_match:
                                solution_name, modality = header_match.groups()
                            else:
                                solution_name = header
                                modality = "Não especificado"
                            
                            current_sug = {
                                "number": line[0],
                                "solution_name": solution_name.strip(),
                                "modality": modality.strip(),
                                "justification": justification
                            }
                        else:
                            current_sug = {
                                "number": line[0],
                                "solution_name": line[2:],
                                "modality": "Não especificado",
                                "justification": ""
                            }
                    elif current_sug:
                        current_sug["justification"] += " " + line
                
                if current_sug:
                    suggestions.append(current_sug)
            
            return suggestions
            
        except Exception as e:
            print(f"Erro ao sugerir novos cursos: {e}")
            return []
    
    def find_similar_solutions(self, query, solutions_data, max_results=5):
        """
        Encontra soluções similares a uma consulta usando a API da OpenAI.
        
        Args:
            query (str): Consulta de texto (problema, necessidade, etc.)
            solutions_data (list): Lista de soluções disponíveis
            max_results (int): Número máximo de resultados a retornar
            
        Returns:
            list: Lista de soluções similares com pontuação
        """
        if not query or not solutions_data:
            return []
        
        # Limita o número de soluções para não sobrecarregar o prompt
        solutions_sample = solutions_data[:50] if len(solutions_data) > 50 else solutions_data
        
        # Gera o prompt para a API
        prompt = f"""
        Você é um especialista em encontrar soluções do Sebrae que correspondam às necessidades das empresas.
        
        CONSULTA:
        {query}
        
        SOLUÇÕES DISPONÍVEIS:
        """
        
        for i, solution in enumerate(solutions_sample):
            name = solution.get('Nome da solução', '')
            modality = solution.get('Modalidade', '')
            theme = solution.get('Tema', '')
            description = solution.get('Descrição', '')[:100]  # Limita o tamanho da descrição
            
            prompt += f"{i+1}. {name} ({modality} - {theme}): {description}\n"
        
        prompt += """
        TAREFA:
        Encontre as soluções mais relevantes para a consulta acima. Para cada solução relevante, forneça:
        1. O número da solução
        2. Uma pontuação de relevância de 0 a 100
        3. Uma breve explicação de por que a solução é relevante
        
        Formato da resposta:
        - Solução X: [Pontuação]/100 - [Explicação]
        """
        
        try:
            # Faz a chamada para a API da OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um especialista em soluções do Sebrae."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            # Extrai o texto da resposta
            result_text = response.choices[0].message.content.strip()
            
            # Processa o texto para extrair as soluções similares
            similar_solutions = []
            pattern = r'Solução\s+(\d+):\s+(\d+)/100\s+-\s+(.*?)(?=Solução\s+\d+:|$)'
            matches = re.findall(pattern, result_text, re.DOTALL)
            
            for match in matches:
                solution_idx, score, explanation = match
                idx = int(solution_idx) - 1
                
                if 0 <= idx < len(solutions_sample):
                    solution = solutions_sample[idx]
                    similar_solutions.append({
                        "solution": solution,
                        "score": int(score),
                        "explanation": explanation.strip()
                    })
            
            # Ordena por pontuação e limita o número de resultados
            similar_solutions.sort(key=lambda x: x["score"], reverse=True)
            return similar_solutions[:max_results]
            
        except Exception as e:
            print(f"Erro ao encontrar soluções similares: {e}")
            return []
