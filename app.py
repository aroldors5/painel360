import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import os
import json
from PIL import Image
import base64
from io import BytesIO
import time

# Importando os módulos personalizados
from data_integration import DataIntegration
from recommendation_system import RecommendationSystem
from sebrae_scraper import SebraeScraper

# Configuração da página
st.set_page_config(
    page_title="Radar de Inovação ALI 360",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cores do ALI 360
ALI_BLUE = "#0077B5"
ALI_LIGHT_BLUE = "#00A0DC"
ALI_GRAY = "#CCCCCC"
ALI_LIGHT_GRAY = "#F2F2F2"

# Função para aplicar o estilo personalizado
def apply_custom_style():
    st.markdown(f"""
    <style>
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        .stApp {{
            background-color: white;
        }}
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: {ALI_LIGHT_GRAY};
            color: {ALI_BLUE};
            border-radius: 4px 4px 0px 0px;
            padding: 10px 20px;
            border: none;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {ALI_BLUE};
            color: white;
        }}
        .stButton>button {{
            background-color: {ALI_BLUE};
            color: white;
            border-radius: 4px;
            border: none;
            padding: 0.5rem 1rem;
        }}
        .stButton>button:hover {{
            background-color: {ALI_LIGHT_BLUE};
        }}
        h1, h2, h3 {{
            color: {ALI_BLUE};
        }}
        .metric-card {{
            background-color: {ALI_LIGHT_GRAY};
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0px;
            text-align: center;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }}
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            color: {ALI_BLUE};
        }}
        .metric-label {{
            font-size: 1rem;
            color: #666;
        }}
        .recommendation-card {{
            background-color: white;
            border-left: 5px solid {ALI_BLUE};
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }}
        .recommendation-title {{
            font-weight: bold;
            color: {ALI_BLUE};
            font-size: 1.2rem;
        }}
        .recommendation-body {{
            color: #333;
            margin-top: 10px;
        }}
        .adherence-high {{
            color: green;
            font-weight: bold;
        }}
        .adherence-medium {{
            color: orange;
            font-weight: bold;
        }}
        .adherence-low {{
            color: red;
            font-weight: bold;
        }}
        .solution-link {{
            color: {ALI_BLUE};
            text-decoration: none;
            border-bottom: 1px dotted {ALI_BLUE};
        }}
        .solution-link:hover {{
            color: {ALI_LIGHT_BLUE};
            border-bottom: 1px solid {ALI_LIGHT_BLUE};
        }}
        .source-tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
            margin-left: 10px;
            background-color: {ALI_LIGHT_GRAY};
            color: {ALI_BLUE};
        }}
    </style>
    """, unsafe_allow_html=True)

# Função para exibir o cabeçalho
def display_header():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image("logo_ali360.png", width=150)
    with col2:
        st.title("Radar de Inovação ALI 360")
        st.markdown("### Painel Interativo de Recomendação de Soluções Sebrae MG")

# Função para exibir métricas em cards
def display_metric_card(title, value, col):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{title}</div>
        </div>
        """, unsafe_allow_html=True)

# Função para exibir recomendações em cards
def display_recommendation_card(title, body, source=None, link=None, col=None):
    source_tag = f'<span class="source-tag">{source}</span>' if source else ''
    link_html = f'<a href="{link}" target="_blank" class="solution-link">Ver detalhes</a>' if link else ''
    
    card_html = f"""
    <div class="recommendation-card">
        <div class="recommendation-title">{title} {source_tag}</div>
        <div class="recommendation-body">{body}</div>
        {link_html}
    </div>
    """
    
    if col:
        with col:
            st.markdown(card_html, unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)

# Função para exibir o nível de aderência
def display_adherence(score):
    if score >= 8:
        return f'<span class="adherence-high">{score}/10 (Alta)</span>'
    elif score >= 4:
        return f'<span class="adherence-medium">{score}/10 (Média)</span>'
    else:
        return f'<span class="adherence-low">{score}/10 (Baixa)</span>'

# Função para carregar e processar dados
@st.cache_data(ttl=600)
def load_data():
    # Inicializa a integração de dados
    data_integration = DataIntegration()

    # Carrega e processa os dados
    radar_data = data_integration.load_radar_data_from_excel('radar.xlsx')
    solutions_data = data_integration.load_solutions_from_excel('solucoes.xlsx')

    # Coleta soluções da web (opcional, pode ser comentado para desenvolvimento mais rápido)
    try:
        web_solutions = data_integration.scrape_web_solutions()
    except Exception as e:
        st.warning(f"Não foi possível coletar soluções da web: {e}")
        web_solutions = None

    # Combina as soluções
    data_integration.combine_solutions()

    # Pré-processa os dados
    radar_processed = data_integration.preprocess_radar_data()
    solutions_processed = data_integration.preprocess_solutions_data()

    return radar_processed, solutions_processed, data_integration


# Função para filtrar dados por regional
def filter_data_by_regional(radar_data, solutions_data, selected_regional):
    if selected_regional == "Todas":
        return radar_data, solutions_data
    else:
        # Verifica qual coluna usar para filtrar
        regional_column = 'Regional' if 'Regional' in radar_data.columns else 'Escritório Regional'
        filtered_radar = radar_data[radar_data[regional_column] == selected_regional]
        
        # Para soluções, verifica se tem a coluna Regional
        if 'Regional' in solutions_data.columns:
            filtered_solutions = solutions_data[
                (solutions_data['Regional'] == selected_regional) | 
                (solutions_data['Regional'].isna())
            ]
        else:
            filtered_solutions = solutions_data
            
        return filtered_radar, filtered_solutions

# Função para gerar gráfico de empresas por estágio
def plot_companies_by_stage(radar_data):
    # Determina qual coluna usar
    stage_column = 'Estágio do diagnóstico' if 'Estágio do diagnóstico' in radar_data.columns else 'Encontro'
    
    if stage_column == 'Encontro':
        # Mapeia valores numéricos para nomes de estágios
        stage_mapping = {
            1: 'Nomear',
            2: 'Elaborar',
            3: 'Experimentar',
            4: 'Evoluir',
            5: 'Concluído'
        }
        radar_data['Estágio'] = radar_data[stage_column].map(lambda x: stage_mapping.get(x, f'Estágio {x}'))
        stage_column = 'Estágio'
    
    stage_counts = radar_data[stage_column].value_counts().reset_index()
    stage_counts.columns = ['Estágio', 'Quantidade']
    
    fig = px.bar(
        stage_counts, 
        x='Estágio', 
        y='Quantidade',
        color='Quantidade',
        color_continuous_scale=px.colors.sequential.Blues,
        title='Empresas por Estágio do Diagnóstico'
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        margin=dict(l=40, r=40, t=40, b=40),
        coloraxis_showscale=False
    )
    
    return fig

# Função para gerar gráfico de desafios por região
def plot_challenges_by_region(radar_data):
    # Determina quais colunas usar
    regional_column = 'Regional' if 'Regional' in radar_data.columns else 'Escritório Regional'
    challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in radar_data.columns else 'Categoria do Problema'
    
    challenge_region = radar_data.groupby([regional_column, challenge_column]).size().reset_index(name='count')
    
    fig = px.bar(
        challenge_region,
        x=regional_column,
        y='count',
        color=challenge_column,
        title='Desafios Priorizados por Regional',
        barmode='group'
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

# Função para gerar gráfico de distribuição de maturidade
def plot_maturity_distribution(radar_data):
    # Determina qual coluna usar
    maturity_column = 'Maturidade em inovação' if 'Maturidade em inovação' in radar_data.columns else 'Média diagnóstico inicial'
    
    # Se for média diagnóstico, categoriza em níveis
    if maturity_column == 'Média diagnóstico inicial':
        # Converte para numérico se possível
        try:
            radar_data['Maturidade'] = pd.to_numeric(radar_data[maturity_column], errors='coerce')
            # Categoriza em níveis
            bins = [0, 2, 3.5, 5]
            labels = ['Baixa', 'Média', 'Alta']
            radar_data['Maturidade Categorizada'] = pd.cut(radar_data['Maturidade'], bins=bins, labels=labels)
            maturity_column = 'Maturidade Categorizada'
        except:
            # Se não conseguir converter, usa a coluna original
            radar_data['Maturidade Categorizada'] = radar_data[maturity_column]
            maturity_column = 'Maturidade Categorizada'
    
    maturity_counts = radar_data[maturity_column].value_counts().reset_index()
    maturity_counts.columns = ['Maturidade', 'Quantidade']
    
    fig = px.pie(
        maturity_counts,
        values='Quantidade',
        names='Maturidade',
        title='Distribuição de Maturidade em Inovação',
        color_discrete_sequence=px.colors.sequential.Blues
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

# Função para gerar mapa de calor de desafios por setor
def plot_challenges_by_sector(radar_data):
    # Determina qual coluna usar
    challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in radar_data.columns else 'Categoria do Problema'
    
    # Limita a 10 setores e 10 desafios mais comuns para melhor visualização
    top_sectors = radar_data['Setor'].value_counts().nlargest(10).index
    top_challenges = radar_data[challenge_column].value_counts().nlargest(10).index
    
    filtered_data = radar_data[
        (radar_data['Setor'].isin(top_sectors)) & 
        (radar_data[challenge_column].isin(top_challenges))
    ]
    
    challenge_sector = pd.crosstab(filtered_data['Setor'], filtered_data[challenge_column])
    
    fig = px.imshow(
        challenge_sector,
        labels=dict(x="Desafio Priorizado", y="Setor", color="Quantidade"),
        x=challenge_sector.columns,
        y=challenge_sector.index,
        color_continuous_scale=px.colors.sequential.Blues,
        title='Mapa de Calor: Desafios por Setor'
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    return fig

# Função para obter recomendações para uma empresa
def get_recommendations_for_company(company_data, solutions_data, recommendation_system):
    # Verifica se a chave da API está configurada
    if not os.environ.get("OPENAI_API_KEY") and 'openai_api_key' in st.session_state:
        recommendation_system.set_api_key(st.session_state['openai_api_key'])
    
    # Obtém recomendações
    try:
        recommendations = recommendation_system.get_recommendations(
            company_data, 
            solutions_data.to_dict('records')
        )
        return recommendations
    except Exception as e:
        st.error(f"Erro ao obter recomendações: {e}")
        return []

# Função para buscar soluções similares a um problema
def search_similar_solutions(query, solutions_data, recommendation_system, max_results=5):
    # Verifica se a chave da API está configurada
    if not os.environ.get("OPENAI_API_KEY") and 'openai_api_key' in st.session_state:
        recommendation_system.set_api_key(st.session_state['openai_api_key'])
    
    # Busca soluções similares
    try:
        similar_solutions = recommendation_system.find_similar_solutions(
            query, 
            solutions_data.to_dict('records'),
            max_results=max_results
        )
        return similar_solutions
    except Exception as e:
        st.error(f"Erro ao buscar soluções similares: {e}")
        return []

# Função principal da aplicação
def main():
    # Aplicar estilo personalizado
    apply_custom_style()
    
    # Exibir cabeçalho
    display_header()
    
    # Verificar se a chave da API da OpenAI está configurada
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    
    # Sidebar para configuração da API da OpenAI
    with st.sidebar:
        st.header("Configuração")
        api_key = st.text_input("Chave da API da OpenAI", 
                               value=st.session_state.openai_api_key,
                               type="password",
                               help="Necessária para o sistema de recomendação")
        
        if api_key:
            st.session_state.openai_api_key = api_key
            os.environ["OPENAI_API_KEY"] = api_key
    
    # Verificar se a chave da API está configurada
    if not st.session_state.openai_api_key:
        st.warning("Por favor, configure a chave da API da OpenAI no menu lateral para habilitar o sistema de recomendação.")
    
    # Inicializar o sistema de recomendação
    recommendation_system = RecommendationSystem(api_key=st.session_state.openai_api_key)
    
    # Carregar dados com indicador de progresso
    with st.spinner("Carregando dados..."):
        radar_data, solutions_data, data_integration = load_data()
    
    # Sidebar para filtros
    with st.sidebar:
        st.header("Filtros")
        
        # Lista de regionais para o filtro
        regional_column = 'Regional' if 'Regional' in radar_data.columns else 'Escritório Regional'
        regionais = ["Todas"] + sorted(radar_data[regional_column].unique().tolist())
        selected_regional = st.selectbox("Regional", regionais)
        
        # Filtro de setor
        setores = ["Todos"] + sorted(radar_data['Setor'].unique().tolist())
        selected_setor = st.selectbox("Setor", setores)
        
        # Filtro de estágio
        stage_column = 'Estágio do diagnóstico' if 'Estágio do diagnóstico' in radar_data.columns else 'Encontro'
        if stage_column == 'Encontro':
            # Mapeia valores numéricos para nomes de estágios
            stage_mapping = {
                1: 'Nomear',
                2: 'Elaborar',
                3: 'Experimentar',
                4: 'Evoluir',
                5: 'Concluído'
            }
            estagios = ["Todos"] + sorted([stage_mapping.get(x, f'Estágio {x}') for x in radar_data[stage_column].unique()])
        else:
            estagios = ["Todos"] + sorted(radar_data[stage_column].unique().tolist())
        selected_estagio = st.selectbox("Estágio do Diagnóstico", estagios)
    
    # Filtrar dados com base nos filtros selecionados
    filtered_radar, filtered_solutions = filter_data_by_regional(radar_data, solutions_data, selected_regional)
    
    # Aplicar filtro de setor
    if selected_setor != "Todos":
        filtered_radar = filtered_radar[filtered_radar['Setor'] == selected_setor]
    
    # Aplicar filtro de estágio
    if selected_estagio != "Todos":
        stage_column = 'Estágio do diagnóstico' if 'Estágio do diagnóstico' in radar_data.columns else 'Encontro'
        if stage_column == 'Encontro':
            # Mapeia nomes de estágios para valores numéricos
            reverse_mapping = {v: k for k, v in stage_mapping.items()}
            stage_value = reverse_mapping.get(selected_estagio)
            if stage_value:
                filtered_radar = filtered_radar[filtered_radar[stage_column] == stage_value]
        else:
            filtered_radar = filtered_radar[filtered_radar[stage_column] == selected_estagio]
    
    # Exibir métricas principais
    st.markdown("## Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    
    # Determina qual coluna usar para desafios
    challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in radar_data.columns else 'Categoria do Problema'
    
    display_metric_card("Empresas", len(filtered_radar), col1)
    display_metric_card("Soluções Disponíveis", len(filtered_solutions), col2)
    display_metric_card("Desafios Únicos", filtered_radar[challenge_column].nunique(), col3)
    display_metric_card("Setores", filtered_radar['Setor'].nunique(), col4)
    
    # Abas para diferentes visualizações
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Recomendações", "Cadastro de Ações", "Curadoria Inteligente"])
    
    # Aba 1: Dashboard
    with tab1:
        st.markdown("### Dashboard Visual")
        
        # Primeira linha de gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(plot_companies_by_stage(filtered_radar), use_container_width=True)
        
        with col2:
            st.plotly_chart(plot_maturity_distribution(filtered_radar), use_container_width=True)
        
        # Segunda linha de gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(plot_challenges_by_region(filtered_radar), use_container_width=True)
        
        with col2:
            st.plotly_chart(plot_challenges_by_sector(filtered_radar), use_container_width=True)
        
        # Lista de empresas
        st.markdown("### Lista de Empresas")
        
        # Determina quais colunas exibir
        company_column = 'Nome da empresa' if 'Nome da empresa' in filtered_radar.columns else 'Nome Empresa'
        city_column = 'Cidade' if 'Cidade' in filtered_radar.columns else 'Município'
        challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in filtered_radar.columns else 'Categoria do Problema'
        need_column = 'Necessidade específica' if 'Necessidade específica' in filtered_radar.columns else 'Descrição do Problema'
        maturity_column = 'Maturidade em inovação' if 'Maturidade em inovação' in filtered_radar.columns else 'Média diagnóstico inicial'
        stage_column = 'Estágio do diagnóstico' if 'Estágio do diagnóstico' in filtered_radar.columns else 'Encontro'
        
        display_columns = [company_column, city_column, 'Setor', challenge_column, maturity_column, stage_column]
        
        st.dataframe(
            filtered_radar[display_columns],
            use_container_width=True
        )
    
    # Aba 2: Recomendações
    with tab2:
        st.markdown("### Recomendação Inteligente de Soluções")
        
        # Opções de recomendação
        recommendation_option = st.radio(
            "Escolha uma opção:",
            ["Recomendar para uma empresa específica", "Buscar soluções para um problema específico"]
        )
        
        if recommendation_option == "Recomendar para uma empresa específica":
            # Seleção de empresa
            company_column = 'Nome da empresa' if 'Nome da empresa' in filtered_radar.columns else 'Nome Empresa'
            selected_company = st.selectbox(
                "Selecione uma empresa para ver recomendações personalizadas:",
                filtered_radar[company_column].tolist()
            )
            
            # Dados da empresa selecionada
            company_data = filtered_radar[filtered_radar[company_column] == selected_company].iloc[0].to_dict()
            
            # Exibir informações da empresa
            st.markdown(f"#### Informações da Empresa: {selected_company}")
            
            col1, col2 = st.columns(2)
            
            # Determina quais colunas exibir
            city_column = 'Cidade' if 'Cidade' in filtered_radar.columns else 'Município'
            regional_column = 'Regional' if 'Regional' in filtered_radar.columns else 'Escritório Regional'
            challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in filtered_radar.columns else 'Categoria do Problema'
            need_column = 'Necessidade específica' if 'Necessidade específica' in filtered_radar.columns else 'Descrição do Problema'
            maturity_column = 'Maturidade em inovação' if 'Maturidade em inovação' in filtered_radar.columns else 'Média diagnóstico inicial'
            stage_column = 'Estágio do diagnóstico' if 'Estágio do diagnóstico' in filtered_radar.columns else 'Encontro'
            
            with col1:
                st.markdown(f"**Cidade/Regional:** {company_data.get(city_column, '')}/{company_data.get(regional_column, '')}")
                st.markdown(f"**Setor:** {company_data.get('Setor', '')}")
                st.markdown(f"**Maturidade em inovação:** {company_data.get(maturity_column, '')}")
            
            with col2:
                st.markdown(f"**Desafio priorizado:** {company_data.get(challenge_column, '')}")
                st.markdown(f"**Necessidade específica:** {company_data.get(need_column, '')}")
                st.markdown(f"**Estágio do diagnóstico:** {company_data.get(stage_column, '')}")
            
            # Botão para gerar recomendações
            if st.button("Gerar Recomendações"):
                if not st.session_state.openai_api_key:
                    st.warning("Por favor, configure a chave da API da OpenAI no menu lateral para gerar recomendações.")
                else:
                    with st.spinner("Gerando recomendações..."):
                        recommendations = get_recommendations_for_company(
                            company_data, 
                            filtered_solutions,
                            recommendation_system
                        )
                    
                    if recommendations:
                        st.markdown("#### Soluções Recomendadas")
                        
                        for rec in recommendations:
                            # Busca informações adicionais da solução
                            solution_name = rec["solution_name"]
                            solution_data = filtered_solutions[filtered_solutions['Nome da solução'].str.contains(solution_name, case=False, na=False)]
                            
                            source = None
                            link = None
                            
                            if not solution_data.empty:
                                source = solution_data.iloc[0].get('Fonte', None)
                                link = solution_data.iloc[0].get('Link', None)
                            
                            display_recommendation_card(
                                rec["solution_name"], 
                                rec["justification"],
                                source=source,
                                link=link
                            )
                    else:
                        st.info("Não foi possível gerar recomendações para esta empresa. Tente novamente ou selecione outra empresa.")
            
            # Soluções já agendadas
            st.markdown("#### Soluções disponíveis na região")
            
            if not filtered_solutions.empty:
                # Determina quais colunas exibir
                display_columns = ['Nome da solução', 'Modalidade', 'Tema', 'Fonte']
                display_columns = [col for col in display_columns if col in filtered_solutions.columns]
                
                st.dataframe(
                    filtered_solutions[display_columns],
                    use_container_width=True
                )
            else:
                st.info("Não há soluções disponíveis para esta região.")
        
        else:  # Buscar soluções para um problema específico
            st.markdown("#### Buscar Soluções para um Problema Específico")
            
            # Campo de busca
            search_query = st.text_area(
                "Descreva o problema ou necessidade:",
                height=100,
                help="Descreva em detalhes o problema ou necessidade para o qual você busca soluções"
            )
            
            # Botão de busca
            if st.button("Buscar Soluções"):
                if not search_query:
                    st.warning("Por favor, descreva o problema ou necessidade.")
                elif not st.session_state.openai_api_key:
                    st.warning("Por favor, configure a chave da API da OpenAI no menu lateral para buscar soluções.")
                else:
                    with st.spinner("Buscando soluções..."):
                        similar_solutions = search_similar_solutions(
                            search_query,
                            filtered_solutions,
                            recommendation_system,
                            max_results=5
                        )
                    
                    if similar_solutions:
                        st.markdown("#### Soluções Encontradas")
                        
                        for item in similar_solutions:
                            solution = item["solution"]
                            score = item["score"]
                            explanation = item["explanation"]
                            
                            # Formata o título com a pontuação
                            title = f"{solution.get('Nome da solução', '')} ({score}% de relevância)"
                            
                            display_recommendation_card(
                                title,
                                explanation,
                                source=solution.get('Fonte', None),
                                link=solution.get('Link', None)
                            )
                    else:
                        st.info("Não foram encontradas soluções para este problema. Tente uma descrição diferente.")
    
    # Aba 3: Cadastro de Ações
    with tab3:
        st.markdown("### Cadastro de Ações e Análise de Aderência")
        
        # Formulário para cadastro de nova solução
        with st.form("cadastro_solucao"):
            st.markdown("#### Cadastre uma nova solução")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome_solucao = st.text_input("Nome da solução")
                modalidade = st.selectbox("Modalidade", ["Curso", "Consultoria", "Workshop", "Programa", "Evento", "Palestra", "Curso Online"])
                tema = st.text_input("Tema")
            
            with col2:
                cidade = st.text_input("Cidade")
                regional = st.selectbox("Regional", sorted(radar_data[regional_column].unique().tolist()))
                data_prevista = st.date_input("Data prevista")
            
            descricao = st.text_area("Descrição", height=100)
            publico_alvo = st.text_input("Público-alvo")
            
            submitted = st.form_submit_button("Cadastrar Solução")
        
        if submitted:
            if not nome_solucao:
                st.error("Por favor, informe o nome da solução.")
            else:
                # Cria um novo registro de solução
                nova_solucao = {
                    'Nome da solução': nome_solucao,
                    'Modalidade': modalidade,
                    'Tema': tema,
                    'Cidade': cidade,
                    'Regional': regional,
                    'Data prevista': data_prevista.strftime('%Y-%m-%d'),
                    'Descrição': descricao,
                    'Público-alvo': publico_alvo,
                    'Fonte': 'Cadastro Manual'
                }
                
                # Adiciona à lista de soluções
                solutions_data = pd.concat([solutions_data, pd.DataFrame([nova_solucao])], ignore_index=True)
                
                st.success(f"Solução '{nome_solucao}' cadastrada com sucesso!")
                
                # Análise de aderência
                if st.session_state.openai_api_key:
                    st.markdown("#### Análise de Aderência às Empresas da Regional")
                    
                    with st.spinner("Analisando aderência..."):
                        # Filtra empresas da regional selecionada
                        regional_companies = filtered_radar[filtered_radar[regional_column] == regional]
                        
                        if len(regional_companies) > 0:
                            # Limita a 10 empresas para não sobrecarregar a API
                            sample_companies = regional_companies.head(10).to_dict('records')
                            
                            # Calcula aderência
                            adherence_results = recommendation_system.calculate_solution_adherence(
                                nova_solucao, 
                                sample_companies
                            )
                            
                            # Ordena empresas por score de aderência
                            sorted_companies = sorted(adherence_results.items(), key=lambda x: x[1]["score"], reverse=True)
                            
                            # Exibe resultados de aderência
                            for company, data in sorted_companies:
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**{company}**")
                                    st.markdown(data["justification"])
                                
                                with col2:
                                    st.markdown(f"Aderência: {display_adherence(data['score'])}", unsafe_allow_html=True)
                                
                                st.divider()
                        else:
                            st.info(f"Não há empresas cadastradas na regional {regional}.")
                else:
                    st.warning("Configure a chave da API da OpenAI no menu lateral para analisar a aderência da solução às empresas.")
    
    # Aba 4: Curadoria Inteligente
    with tab4:
        st.markdown("### Curadoria Inteligente de Soluções")
        
        # Análise regional
        st.markdown(f"#### Análise da Regional: {selected_regional if selected_regional != 'Todas' else 'Todas as Regionais'}")
        
        # Obtém dados agregados da regional
        regional_data = data_integration.get_regional_data(selected_regional if selected_regional != 'Todas' else None)
        
        if regional_data:
            col1, col2 = st.columns(2)
            
            with col1:
                # Desafios mais comuns
                st.markdown("##### Desafios mais comuns")
                challenges_df = pd.DataFrame(regional_data['top_challenges'])
                if not challenges_df.empty:
                    st.dataframe(challenges_df, use_container_width=True)
                else:
                    st.info("Não há dados de desafios disponíveis.")
            
            with col2:
                # Setores mais comuns
                st.markdown("##### Setores mais comuns")
                sectors_df = pd.DataFrame(regional_data['top_sectors'])
                if not sectors_df.empty:
                    st.dataframe(sectors_df, use_container_width=True)
                else:
                    st.info("Não há dados de setores disponíveis.")
            
            # Botão para gerar sugestões de cursos
            if st.button("Gerar Sugestões de Novas Soluções"):
                if not st.session_state.openai_api_key:
                    st.warning("Por favor, configure a chave da API da OpenAI no menu lateral para gerar sugestões.")
                else:
                    with st.spinner("Gerando sugestões de novas soluções..."):
                        # Obtém soluções já agendadas na regional
                        if 'Regional' in solutions_data.columns:
                            scheduled_solutions = solutions_data[
                                solutions_data['Regional'] == selected_regional
                            ].to_dict('records') if selected_regional != "Todas" else []
                        else:
                            scheduled_solutions = []
                        
                        # Gera sugestões
                        suggestions = recommendation_system.suggest_new_courses(
                            regional_data,
                            scheduled_solutions
                        )
                    
                    if suggestions:
                        st.markdown("#### Sugestões de Novas Soluções")
                        
                        for i, sug in enumerate(suggestions):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{i+1}. {sug['solution_name']}** ({sug['modality']})")
                                st.markdown(sug["justification"])
                            
                            with col2:
                                st.button(f"Adicionar ao Plano #{i+1}", key=f"add_suggestion_{i}")
                            
                            st.divider()
                    else:
                        st.info("Não foi possível gerar sugestões para esta regional. Tente novamente ou selecione outra regional.")
        else:
            st.warning("Não foi possível obter dados agregados da regional selecionada.")

# Verificar se o arquivo de logo existe, caso contrário, criar um placeholder
def check_logo_file():
    if not os.path.exists("logo_ali360.png"):
        # Criar um placeholder para o logo
        plt.figure(figsize=(3, 1))
        plt.text(0.5, 0.5, "ALI 360", fontsize=24, ha='center', va='center', color=ALI_BLUE)
        plt.axis('off')
        plt.savefig("logo_ali360.png", bbox_inches='tight', pad_inches=0.1, transparent=True)
        plt.close()

# Executar a aplicação
if __name__ == "__main__":
    check_logo_file()
    main()
