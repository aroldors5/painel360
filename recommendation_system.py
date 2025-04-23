import pandas as pd
import numpy as np
import re
import os
import openai
import logging
from typing import List, Dict, Any

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('recommendation_system')

class RecommendationSystem:
    def __init__(self, api_key=None, debug=False):
        """
        Inicializa o sistema de recomendação baseado na API da OpenAI.
        
        Args:
            api_key (str): Chave da API da OpenAI (opcional, pode ser definida como variável de ambiente)
            debug (bool): Se True, ativa o modo de depuração com mais logs
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("API key configurada com sucesso")
        else:
            logger.warning("API key não configurada. Use set_api_key() para configurar.")
        
        # Modelo a ser utilizado
        self.model = "gpt-3.5-turbo"
        
        # Cache para armazenar recomendações e reduzir chamadas à API
        self.recommendation_cache = {}
        
        # Modo de depuração
        self.debug = debug
        if debug:
            logger.setLevel(logging.DEBUG)
    
    def set_api_key(self, api_key):
        """
        Define a chave da API da OpenAI.
        
        Args:
            api_key (str): Chave da API da OpenAI
        """
        self.api_key = api_key
        openai.api_key = api_key
        logger.info("API key atualizada com sucesso")
    
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
        
        # Verifica se temos soluções disponíveis
        if not available_solutions or len(available_solutions) == 0:
            logger.warning("Nenhuma solução disponível para recomendação")
            return None
        
        # Formata as soluções disponíveis (limitado a 30 para não sobrecarregar o prompt)
        solutions_sample = available_solutions[:30] if len(available_solutions) > 30 else available_solutions
        solutions_text = "\n".join([
            f"- {sol.get('Nome da solução', '')}: {sol.get('Modalidade', '')} | {sol.get('Tema', '')} | {sol.get('Fonte', '')} | {sol.get('Descrição', '')[:100]}..."
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
        
        SOLUÇÕES DISPONÍVEIS:
        {solutions_text}
        
        {scheduled_text}
        
        TAREFA:
        Recomende as 5 melhores soluções do Sebrae para esta empresa, considerando:
        1. Alinhamento com o desafio priorizado e necessidade específica
        2. Adequação ao setor e maturidade da empresa
        3. Evite recomendar soluções já agendadas
        4. Para cada recomendação, explique por que é adequada para esta empresa
        5. Seja específico e detalhado nas justificativas
        
        Formato da resposta:
        1. [Nome exato da Solução 1]: [Justificativa detalhada]
        2. [Nome exato da Solução 2]: [Justificativa detalhada]
        3. [Nome exato da Solução 3]: [Justificativa detalhada]
        4. [Nome exato da Solução 4]: [Justificativa detalhada]
        5. [Nome exato da Solução 5]: [Justificativa detalhada]
        
        IMPORTANTE: Use EXATAMENTE os nomes das soluções conforme listados acima.
        """
        
        if self.debug:
            logger.debug(f"Prompt gerado para a empresa {company_name}:\n{prompt}")
        
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
        # Verifica se temos dados da empresa
        if not company_data:
            logger.error("Dados da empresa não fornecidos")
            return []
        
        # Verifica se temos soluções disponíveis
        if not available_solutions or len(available_solutions) == 0:
            logger.warning("Nenhuma solução disponível para recomendação")
            return []
        
        # Gera uma chave única para o cache
        company_name = company_data.get('Nome da empresa', company_data.get('Nome Empresa', ''))
        challenge = company_data.get('Desafio priorizado', company_data.get('Categoria do Problema', ''))
        cache_key = f"{company_name}-{challenge}"
        
        # Verifica se já existe no cache
        if cache_key in self.recommendation_cache:
            logger.info(f"Usando recomendações em cache para {company_name}")
            return self.recommendation_cache[cache_key]
        
        # Gera o prompt para a API
        prompt = self.generate_recommendation_prompt(
            company_data, available_solutions, already_scheduled
        )
        
        if not prompt:
            logger.error("Falha ao gerar prompt para recomendações")
            return []
        
        try:
            logger.info(f"Solicitando recomendações para {company_name}")
            
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
            recommendation_text = response.choices[0].message.content.strip()
            
            if self.debug:
                logger.debug(f"Resposta da API para {company_name}:\n{recommendation_text}")
            
            # Processa o texto para extrair as recomendações
            recommendations = self.parse_recommendations(recommendation_text, available_solutions)
            
            # Armazena no cache
            self.recommendation_cache[cache_key] = recommendations
            
            logger.info(f"Obtidas {len(recommendations)} recomendações para {company_name}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Erro ao obter recomendações: {e}")
            return []
    
    def parse_recommendations(self, recommendation_text, available_solutions):
        """
        Analisa o texto da resposta da API para extrair as recomendações.
        
        Args:
            recommendation_text (str): Texto da resposta da API
            available_solutions (list): Lista de soluções disponíveis para validação
            
        Returns:
            list: Lista de recomendações estruturadas
        """
        recommendations = []
        
        # Cria um dicionário de soluções disponíveis para validação
        available_solutions_dict = {sol.get('Nome da solução', '').lower(): sol for sol in available_solutions}
        
        # Padrão para extrair recomendações numeradas
        pattern = r'(\d+)\.\s+\[([^\]]+)\]:\s+(.*?)(?=\d+\.\s+\[|$)'
        matches = re.findall(pattern, recommendation_text, re.DOTALL)
        
        for match in matches:
            number, solution_name, justification = match
            
            # Verifica se a solução existe na lista de soluções disponíveis
            solution_name_lower = solution_name.strip().lower()
            exact_match = False
            matched_solution = None
            
            # Tenta encontrar uma correspondência exata
            if solution_name_lower in available_solutions_dict:
                exact_match = True
                matched_solution = available_solutions_dict[solution_name_lower]
            else:
                # Se não encontrar correspondência exata, procura por correspondência parcial
                for sol_name, sol in available_solutions_dict.items():
                    if solution_name_lower in sol_name or sol_name in solution_name_lower:
                        matched_solution = sol
                        break
            
            # Se encontrou uma solução correspondente, adiciona à lista de recomendações
            if matched_solution:
                recommendation = {
                    "number": number.strip(),
                    "solution_name": matched_solution.get('Nome da solução', solution_name.strip()),
                    "justification": justification.strip(),
                    "exact_match": exact_match,
                    "solution_data": matched_solution
                }
                recommendations.append(recommendation)
            else:
                # Se não encontrou correspondência, adiciona apenas o nome e justificativa
                logger.warning(f"Solução não encontrada na lista de disponíveis: {solution_name}")
                recommendation = {
                    "number": number.strip(),
                    "solution_name": solution_name.strip(),
                    "justification": justification.strip(),
                    "exact_match": False,
                    "solution_data": {"Nome da solução": solution_name.strip()}
                }
                recommendations.append(recommendation)
        
        # Se o padrão não encontrou nada, tenta outro formato
        if not recommendations:
            logger.warning("Padrão principal não encontrou recomendações, tentando formato alternativo")
            lines = recommendation_text.split('\n')
            current_rec = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Verifica se é uma nova recomendação
                if line[0].isdigit() and '. ' in line[:10]:
                    if current_rec:
                        # Verifica se a solução existe na lista de soluções disponíveis
                        solution_name_lower = current_rec["solution_name"].lower()
                        exact_match = False
                        matched_solution = None
                        
                        if solution_name_lower in available_solutions_dict:
                            exact_match = True
                            matched_solution = available_solutions_dict[solution_name_lower]
                        else:
                            for sol_name, sol in available_solutions_dict.items():
                                if solution_name_lower in sol_name or sol_name in solution_name_lower:
                                    matched_solution = sol
                                    break
                        
                        if matched_solution:
                            current_rec["solution_name"] = matched_solution.get('Nome da solução', current_rec["solution_name"])
                            current_rec["exact_match"] = exact_match
                            current_rec["solution_data"] = matched_solution
                        else:
                            current_rec["exact_match"] = False
                            current_rec["solution_data"] = {"Nome da solução": current_rec["solution_name"]}
                        
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
                # Verifica se a solução existe na lista de soluções disponíveis
                solution_name_lower = current_rec["solution_name"].lower()
                exact_match = False
                matched_solution = None
                
                if solution_name_lower in available_solutions_dict:
                    exact_match = True
                    matched_solution = available_solutions_dict[solution_name_lower]
                else:
                    for sol_name, sol in available_solutions_dict.items():
                        if solution_name_lower in sol_name or sol_name in solution_name_lower:
                            matched_solution = sol
                            break
                
                if matched_solution:
                    current_rec["solution_name"] = matched_solution.get('Nome da solução', current_rec["solution_name"])
                    current_rec["exact_match"] = exact_match
                    current_rec["solution_data"] = matched_solution
                else:
                    current_rec["exact_match"] = False
                    current_rec["solution_data"] = {"Nome da solução": current_rec["solution_name"]}
                
                recommendations.append(current_rec)
        
        # Se ainda não encontrou recomendações, usa um método mais simples
        if not recommendations:
            logger.warning("Nenhum formato reconhecido, usando método simples para extrair recomendações")
            lines = recommendation_text.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':', 1)
                    solution_name = parts[0].strip()
                    justification = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Verifica se a solução existe na lista de soluções disponíveis
                    solution_name_lower = solution_name.lower()
                    exact_match = False
                    matched_solution = None
                    
                    if solution_name_lower in available_solutions_dict:
                        exact_match = True
                        matched_solution = available_solutions_dict[solution_name_lower]
                    else:
                        for sol_name, sol in available_solutions_dict.items():
                            if solution_name_lower in sol_name or sol_name in solution_name_lower:
                                matched_solution = sol
                                break
                    
                    if matched_solution:
                        recommendation = {
                            "number": str(i + 1),
                            "solution_name": matched_solution.get('Nome da solução', solution_name),
                            "justification": justification,
                            "exact_match": exact_match,
                            "solution_data": matched_solution
                        }
                    else:
                        recommendation = {
                            "number": str(i + 1),
                            "solution_name": solution_name,
                            "justification": justification,
                            "exact_match": False,
                            "solution_data": {"Nome da solução": solution_name}
                        }
                    
                    recommendations.append(recommendation)
        
        # Limita a 5 recomendações
        return recommendations[:5]
    
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
        
        # Verifica se temos dados suficientes
        if not solution_name or not companies_data or len(companies_data) == 0:
            logger.warning("Dados insuficientes para calcular aderência")
            return adherence_results
        
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
        
        if self.debug:
            logger.debug(f"Prompt para cálculo de aderência da solução {solution_name}:\n{prompt}")
        
        try:
            logger.info(f"Calculando aderência da solução {solution_name} para {len(companies_sample)} empresas")
            
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
            
            if self.debug:
                logger.debug(f"Resposta da API para aderência da solução {solution_name}:\n{adherence_text}")
            
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
                    logger.warning(f"Não foi possível extrair aderência para a empresa {company_name}")
                    adherence_results[company_name] = {
                        "score": 0,
                        "justification": "Não foi possível calcular a aderência."
                    }
            
            logger.info(f"Aderência calculada para {len(adherence_results)} empresas")
            return adherence_results
            
        except Exception as e:
            logger.error(f"Erro ao calcular aderência: {e}")
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
        # Verifica se temos dados suficientes
        if not regional_data:
            logger.warning("Dados regionais não fornecidos")
            return []
        
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
        Você é um consultor especializado do Sebrae MG que sugere novos cursos e soluções com base nas necessidades regionais.
        
        DADOS REGIONAIS:
        
        Desafios mais comuns:
        {challenges_text}
        
        Setores mais comuns:
        {sectors_text}
        
        Distribuição de maturidade em inovação:
        {maturity_text}
        
        Soluções já agendadas:
        {scheduled_text}
        
        TAREFA:
        Com base nos dados acima, sugira 5 novos cursos ou soluções que o Sebrae MG poderia oferecer para atender às necessidades das empresas desta regional.
        
        Para cada sugestão, forneça:
        1. Nome do curso/solução
        2. Modalidade (Curso, Consultoria, Evento, etc.)
        3. Tema principal
        4. Breve descrição
        5. Justificativa de por que esta solução seria relevante para a regional
        
        Formato da resposta:
        1. [Nome da Solução 1]
           - Modalidade: [Modalidade]
           - Tema: [Tema]
           - Descrição: [Descrição]
           - Justificativa: [Justificativa]
        
        2. [Nome da Solução 2]
           - Modalidade: [Modalidade]
           - Tema: [Tema]
           - Descrição: [Descrição]
           - Justificativa: [Justificativa]
        
        (e assim por diante)
        """
        
        if self.debug:
            logger.debug(f"Prompt para sugestão de novos cursos:\n{prompt}")
        
        try:
            logger.info("Solicitando sugestões de novos cursos")
            
            # Faz a chamada para a API da OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um consultor especializado do Sebrae MG."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            # Extrai o texto da resposta
            suggestions_text = response.choices[0].message.content.strip()
            
            if self.debug:
                logger.debug(f"Resposta da API para sugestão de novos cursos:\n{suggestions_text}")
            
            # Processa o texto para extrair as sugestões
            suggestions = self.parse_course_suggestions(suggestions_text)
            
            logger.info(f"Obtidas {len(suggestions)} sugestões de novos cursos")
            return suggestions
            
        except Exception as e:
            logger.error(f"Erro ao sugerir novos cursos: {e}")
            return []
    
    def parse_course_suggestions(self, suggestions_text):
        """
        Analisa o texto da resposta da API para extrair as sugestões de cursos.
        
        Args:
            suggestions_text (str): Texto da resposta da API
            
        Returns:
            list: Lista de sugestões de cursos estruturadas
        """
        suggestions = []
        
        # Padrão para extrair sugestões numeradas
        pattern = r'(\d+)\.\s+\[([^\]]+)\](.*?)(?=\d+\.\s+\[|$)'
        matches = re.findall(pattern, suggestions_text, re.DOTALL)
        
        for match in matches:
            number, name, details = match
            
            # Extrai os detalhes
            modalidade_match = re.search(r'Modalidade:\s+(.+?)(?=\n|$)', details)
            tema_match = re.search(r'Tema:\s+(.+?)(?=\n|$)', details)
            descricao_match = re.search(r'Descrição:\s+(.+?)(?=\n|$)', details)
            justificativa_match = re.search(r'Justificativa:\s+(.+?)(?=\n|$)', details)
            
            modalidade = modalidade_match.group(1).strip() if modalidade_match else ""
            tema = tema_match.group(1).strip() if tema_match else ""
            descricao = descricao_match.group(1).strip() if descricao_match else ""
            justificativa = justificativa_match.group(1).strip() if justificativa_match else ""
            
            suggestions.append({
                "number": number.strip(),
                "name": name.strip(),
                "modalidade": modalidade,
                "tema": tema,
                "descricao": descricao,
                "justificativa": justificativa
            })
        
        # Se o padrão não encontrou nada, tenta outro formato
        if not suggestions:
            logger.warning("Padrão principal não encontrou sugestões, tentando formato alternativo")
            sections = re.split(r'\d+\.\s+', suggestions_text)[1:]  # Divide pelo número e ponto
            
            for i, section in enumerate(sections):
                lines = section.strip().split('\n')
                
                if not lines:
                    continue
                
                name = lines[0].strip()
                modalidade = ""
                tema = ""
                descricao = ""
                justificativa = ""
                
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith('- Modalidade:'):
                        modalidade = line[13:].strip()
                    elif line.startswith('- Tema:'):
                        tema = line[8:].strip()
                    elif line.startswith('- Descrição:'):
                        descricao = line[13:].strip()
                    elif line.startswith('- Justificativa:'):
                        justificativa = line[16:].strip()
                
                suggestions.append({
                    "number": str(i + 1),
                    "name": name,
                    "modalidade": modalidade,
                    "tema": tema,
                    "descricao": descricao,
                    "justificativa": justificativa
                })
        
        return suggestions
    
    def analyze_company_needs(self, company_data):
        """
        Analisa as necessidades de uma empresa com base em seus dados.
        
        Args:
            company_data (dict): Dados da empresa
            
        Returns:
            dict: Análise das necessidades da empresa
        """
        # Verifica se temos dados da empresa
        if not company_data:
            logger.error("Dados da empresa não fornecidos")
            return {}
        
        # Extrai informações relevantes da empresa
        company_name = company_data.get('Nome da empresa', company_data.get('Nome Empresa', 'Empresa'))
        challenge = company_data.get('Desafio priorizado', company_data.get('Categoria do Problema', ''))
        specific_need = company_data.get('Necessidade específica', company_data.get('Descrição do Problema', ''))
        sector = company_data.get('Setor', '')
        maturity = company_data.get('Maturidade em inovação', company_data.get('Média diagnóstico inicial', ''))
        stage = company_data.get('Estágio do diagnóstico', str(company_data.get('Encontro', '')))
        
        # Gera o prompt para a API
        prompt = f"""
        Você é um consultor especializado do Sebrae MG que analisa as necessidades das empresas.
        
        DADOS DA EMPRESA:
        - Nome: {company_name}
        - Setor: {sector}
        - Desafio priorizado: {challenge}
        - Maturidade em inovação: {maturity}
        - Necessidade específica: {specific_need}
        - Estágio do diagnóstico: {stage}
        
        TAREFA:
        Analise as necessidades desta empresa e forneça:
        1. Um resumo das principais necessidades
        2. Os pontos fortes e fracos identificados
        3. As áreas prioritárias para intervenção
        4. Recomendações gerais de tipos de soluções que seriam adequadas
        
        Formato da resposta:
        {{"resumo": "Resumo das necessidades",
         "pontos_fortes": ["Ponto forte 1", "Ponto forte 2", ...],
         "pontos_fracos": ["Ponto fraco 1", "Ponto fraco 2", ...],
         "areas_prioritarias": ["Área 1", "Área 2", ...],
         "tipos_solucoes": ["Tipo 1", "Tipo 2", ...]}}
        """
        
        if self.debug:
            logger.debug(f"Prompt para análise de necessidades da empresa {company_name}:\n{prompt}")
        
        try:
            logger.info(f"Analisando necessidades da empresa {company_name}")
            
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
            analysis_text = response.choices[0].message.content.strip()
            
            if self.debug:
                logger.debug(f"Resposta da API para análise de necessidades da empresa {company_name}:\n{analysis_text}")
            
            # Tenta extrair o JSON da resposta
            try:
                # Remove possíveis caracteres extras antes e depois do JSON
                json_text = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_text:
                    import json
                    analysis = json.loads(json_text.group(0))
                    logger.info(f"Análise de necessidades concluída para {company_name}")
                    return analysis
                else:
                    logger.warning(f"Não foi possível extrair JSON da resposta para {company_name}")
            except Exception as e:
                logger.error(f"Erro ao processar JSON da análise: {e}")
            
            # Se não conseguiu extrair o JSON, tenta extrair manualmente
            analysis = {}
            
            resumo_match = re.search(r'"resumo":\s*"([^"]+)"', analysis_text)
            if resumo_match:
                analysis['resumo'] = resumo_match.group(1)
            
            pontos_fortes_match = re.search(r'"pontos_fortes":\s*\[(.*?)\]', analysis_text, re.DOTALL)
            if pontos_fortes_match:
                pontos_fortes_text = pontos_fortes_match.group(1)
                pontos_fortes = re.findall(r'"([^"]+)"', pontos_fortes_text)
                analysis['pontos_fortes'] = pontos_fortes
            
            pontos_fracos_match = re.search(r'"pontos_fracos":\s*\[(.*?)\]', analysis_text, re.DOTALL)
            if pontos_fracos_match:
                pontos_fracos_text = pontos_fracos_match.group(1)
                pontos_fracos = re.findall(r'"([^"]+)"', pontos_fracos_text)
                analysis['pontos_fracos'] = pontos_fracos
            
            areas_prioritarias_match = re.search(r'"areas_prioritarias":\s*\[(.*?)\]', analysis_text, re.DOTALL)
            if areas_prioritarias_match:
                areas_prioritarias_text = areas_prioritarias_match.group(1)
                areas_prioritarias = re.findall(r'"([^"]+)"', areas_prioritarias_text)
                analysis['areas_prioritarias'] = areas_prioritarias
            
            tipos_solucoes_match = re.search(r'"tipos_solucoes":\s*\[(.*?)\]', analysis_text, re.DOTALL)
            if tipos_solucoes_match:
                tipos_solucoes_text = tipos_solucoes_match.group(1)
                tipos_solucoes = re.findall(r'"([^"]+)"', tipos_solucoes_text)
                analysis['tipos_solucoes'] = tipos_solucoes
            
            logger.info(f"Análise de necessidades extraída manualmente para {company_name}")
            return analysis
            
        except Exception as e:
            logger.error(f"Erro ao analisar necessidades da empresa: {e}")
            return {
                "resumo": f"Não foi possível analisar as necessidades da empresa {company_name}.",
                "pontos_fortes": [],
                "pontos_fracos": [],
                "areas_prioritarias": [],
                "tipos_solucoes": []
            }
    
    def clear_cache(self):
        """
        Limpa o cache de recomendações.
        """
        self.recommendation_cache = {}
        logger.info("Cache de recomendações limpo")
