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
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Importando os módulos personalizados melhorados
from data_integration_improved import DataIntegration
from recommendation_system_improved import RecommendationSystem
from sebrae_scraper_improved import SebraeScraper

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
        .solution-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .solution-table th {{
            background-color: {ALI_BLUE};
            color: white;
            padding: 8px;
            text-align: left;
        }}
        .solution-table td {{
            padding: 8px;
            border-bottom: 1px solid {ALI_LIGHT_GRAY};
        }}
        .solution-table tr:nth-child(even) {{
            background-color: {ALI_LIGHT_GRAY};
        }}
        .solution-table tr:hover {{
            background-color: #e6f2ff;
        }}
        .filter-section {{
            background-color: {ALI_LIGHT_GRAY};
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .debug-info {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 0.8rem;
            color: #666;
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
def display_recommendation_card(recommendation, col=None):
    title = recommendation.get("solution_name", "")
    body = recommendation.get("justification", "")
    
    # Obter dados adicionais da solução
    solution_data = recommendation.get("solution_data", {})
    source = solution_data.get("Fonte", "")
    link = solution_data.get("Link", "")
    modalidade = solution_data.get("Modalidade", "")
    tema = solution_data.get("Tema", "")
    
    # Criar tags para fonte, modalidade e tema
    source_tag = f'<span class="source-tag">{source}</span>' if source else ''
    modalidade_tag = f'<span class="source-tag">{modalidade}</span>' if modalidade else ''
    tema_tag = f'<span class="source-tag">{tema}</span>' if tema else ''
    
    # Criar link para detalhes
    link_html = f'<a href="{link}" target="_blank" class="solution-link">Ver detalhes</a>' if link else ''
    
    card_html = f"""
    <div class="recommendation-card">
        <div class="recommendation-title">{title} {source_tag}</div>
        <div style="margin-top: 5px;">{modalidade_tag} {tema_tag}</div>
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
def load_data(debug=False):
    try:
        # Inicializa a integração de dados
        data_integration = DataIntegration(debug=debug)
        
        # Carrega e processa os dados
        logger.info("Carregando dados do radar...")
        radar_data = data_integration.load_radar_data_from_excel('/home/ubuntu/upload/')
        
        logger.info("Carregando dados de soluções...")
        solutions_data = data_integration.load_solutions_from_excel('/home/ubuntu/upload/')
        
        # Coleta soluções da web
        logger.info("Coletando soluções da web...")
        try:
            web_solutions = data_integration.scrape_web_solutions()
            logger.info(f"Coletadas {len(web_solutions) if web_solutions is not None else 0} soluções da web")
        except Exception as e:
            logger.error(f"Erro ao coletar soluções da web: {e}")
            st.warning(f"Não foi possível coletar soluções da web: {e}")
            web_solutions = None
        
        # Combina as soluções
        logger.info("Combinando soluções...")
        combined_solutions = data_integration.combine_solutions()
        
        # Pré-processa os dados
        logger.info("Pré-processando dados...")
        radar_processed = data_integration.preprocess_radar_data()
        solutions_processed = data_integration.preprocess_solutions_data()
        
        logger.info("Dados carregados com sucesso")
        return radar_processed, solutions_processed, data_integration
    
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        st.error(f"Erro ao carregar dados: {e}")
        return None, None, None

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

# Função para filtrar dados por setor
def filter_data_by_sector(radar_data, solutions_data, selected_sector):
    if selected_sector == "Todos":
        return radar_data, solutions_data
    else:
        filtered_radar = radar_data[radar_data['Setor'] == selected_sector]
        
        # Para soluções, verifica se tem a coluna Setor
        if 'Setor' in solutions_data.columns:
            filtered_solutions = solutions_data[
                (solutions_data['Setor'] == selected_sector) | 
                (solutions_data['Setor'].isna())
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
        logger.info(f"Obtendo recomendações para a empresa {company_data.get('Nome da empresa', '')}")
        recommendations = recommendation_system.get_recommendations(
            company_data, 
            solutions_data.to_dict('records')
        )
        logger.info(f"Obtidas {len(recommendations)} recomendações")
        return recommendations
    except Exception as e:
        logger.error(f"Erro ao obter recomendações: {e}")
        st.error(f"Erro ao obter recomendações: {e}")
        return []

# Função para exibir detalhes de uma solução
def display_solution_details(solution):
    st.subheader(solution.get('Nome da solução', 'Solução'))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Fonte:**")
        st.write(solution.get('Fonte', 'Não informado'))
        
        st.markdown("**Modalidade:**")
        st.write(solution.get('Modalidade', 'Não informado'))
        
        st.markdown("**Tema:**")
        st.write(solution.get('Tema', 'Não informado'))
        
        if 'Regional' in solution:
            st.markdown("**Regional:**")
            st.write(solution.get('Regional', 'Não informado'))
        
        if 'Cidade' in solution:
            st.markdown("**Cidade:**")
            st.write(solution.get('Cidade', 'Não informado'))
    
    with col2:
        if 'Link' in solution and solution['Link']:
            st.markdown("**Link:**")
            st.markdown(f"[Acessar]({solution['Link']})")
        
        if 'Data de coleta' in solution:
            st.markdown("**Data de coleta:**")
            st.write(solution.get('Data de coleta', 'Não informado'))
        
        if 'Preço' in solution:
            st.markdown("**Preço:**")
            st.write(solution.get('Preço', 'Não informado'))
    
    st.markdown("**Descrição:**")
    st.write(solution.get('Descrição', 'Sem descrição disponível'))

# Função para exibir tabela de soluções
def display_solutions_table(solutions_data, filters=None):
    # Aplica filtros se fornecidos
    filtered_data = solutions_data.copy()
    
    if filters:
        if filters.get('fonte') and filters['fonte'] != 'Todas':
            filtered_data = filtered_data[filtered_data['Fonte'] == filters['fonte']]
        
        if filters.get('modalidade') and filters['modalidade'] != 'Todas':
            filtered_data = filtered_data[filtered_data['Modalidade'] == filters['modalidade']]
        
        if filters.get('tema') and filters['tema'] != 'Todos':
            filtered_data = filtered_data[filtered_data['Tema'] == filters['tema']]
        
        if filters.get('busca'):
            busca = filters['busca'].lower()
            filtered_data = filtered_data[
                filtered_data['Nome da solução'].str.lower().str.contains(busca) | 
                filtered_data['Descrição'].str.lower().str.contains(busca)
            ]
    
    # Seleciona colunas para exibição
    display_columns = ['Nome da solução', 'Modalidade', 'Tema', 'Fonte']
    
    # Adiciona coluna de link se existir
    if 'Link' in filtered_data.columns:
        filtered_data['Ver'] = filtered_data['Link'].apply(
            lambda x: f'<a href="{x}" target="_blank">🔗</a>' if pd.notna(x) and x else ''
        )
        display_columns.append('Ver')
    
    # Exibe a tabela
    st.dataframe(
        filtered_data[display_columns],
        use_container_width=True,
        hide_index=True
    )
    
    # Exibe contagem
    st.info(f"Total de {len(filtered_data)} soluções encontradas")
    
    return filtered_data

# Função principal da aplicação
def main():
    # Aplicar estilo personalizado
    apply_custom_style()
    
    # Exibir cabeçalho
    display_header()
    
    # Verificar se a chave da API da OpenAI está configurada
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = ""
    
    # Verificar se o modo de depuração está ativado
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False
    
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
        
        # Opção de modo de depuração
        st.session_state.debug_mode = st.checkbox("Modo de depuração", value=st.session_state.debug_mode)
    
    # Verificar se a chave da API está configurada
    if not st.session_state.openai_api_key:
        st.warning("Por favor, configure a chave da API da OpenAI no menu lateral para habilitar o sistema de recomendação.")
    
    # Inicializar o sistema de recomendação
    recommendation_system = RecommendationSystem(
        api_key=st.session_state.openai_api_key,
        debug=st.session_state.debug_mode
    )
    
    # Carregar dados com indicador de progresso
    with st.spinner("Carregando dados..."):
        radar_data, solutions_data, data_integration = load_data(debug=st.session_state.debug_mode)
    
    # Verificar se os dados foram carregados com sucesso
    if radar_data is None or solutions_data is None or data_integration is None:
        st.error("Erro ao carregar dados. Por favor, verifique os arquivos de entrada e tente novamente.")
        return
    
    # Exibir informações de depuração se o modo estiver ativado
    if st.session_state.debug_mode:
        with st.expander("Informações de Depuração"):
            st.subheader("Dados do Radar")
            st.write(f"Número de registros: {len(radar_data)}")
            st.write(f"Colunas: {radar_data.columns.tolist()}")
            st.dataframe(radar_data.head())
            
            st.subheader("Dados de Soluções")
            st.write(f"Número de registros: {len(solutions_data)}")
            st.write(f"Colunas: {solutions_data.columns.tolist()}")
            st.dataframe(solutions_data.head())
    
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
        
        selected_estagio = st.selectbox("Estágio", estagios)
    
    # Aplicar filtros
    filtered_radar = radar_data.copy()
    filtered_solutions = solutions_data.copy()
    
    # Filtro por regional
    if selected_regional != "Todas":
        filtered_radar = filtered_radar[filtered_radar[regional_column] == selected_regional]
    
    # Filtro por setor
    if selected_setor != "Todos":
        filtered_radar = filtered_radar[filtered_radar['Setor'] == selected_setor]
    
    # Filtro por estágio
    if selected_estagio != "Todos":
        if stage_column == 'Encontro':
            # Encontra o valor numérico correspondente ao estágio selecionado
            stage_value = next((k for k, v in stage_mapping.items() if v == selected_estagio), None)
            if stage_value:
                filtered_radar = filtered_radar[filtered_radar[stage_column] == stage_value]
        else:
            filtered_radar = filtered_radar[filtered_radar[stage_column] == selected_estagio]
    
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Recomendações", "Soluções", "Análise"])
    
    # Aba 1: Dashboard
    with tab1:
        # Métricas principais
        st.subheader("Métricas Principais")
        col1, col2, col3, col4 = st.columns(4)
        
        # Total de empresas
        display_metric_card("Total de Empresas", len(filtered_radar), col1)
        
        # Total de soluções
        display_metric_card("Total de Soluções", len(solutions_data), col2)
        
        # Média de maturidade
        maturity_column = 'Maturidade em inovação' if 'Maturidade em inovação' in radar_data.columns else 'Média diagnóstico inicial'
        try:
            avg_maturity = filtered_radar[maturity_column].astype(float).mean()
            display_metric_card("Média de Maturidade", f"{avg_maturity:.2f}", col3)
        except:
            display_metric_card("Média de Maturidade", "N/A", col3)
        
        # Total de regionais
        display_metric_card("Total de Regionais", filtered_radar[regional_column].nunique(), col4)
        
        # Gráficos
        st.subheader("Visualizações")
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de empresas por estágio
            fig1 = plot_companies_by_stage(filtered_radar)
            st.plotly_chart(fig1, use_container_width=True)
            
            # Mapa de calor de desafios por setor
            fig3 = plot_challenges_by_sector(filtered_radar)
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            # Gráfico de distribuição de maturidade
            fig2 = plot_maturity_distribution(filtered_radar)
            st.plotly_chart(fig2, use_container_width=True)
            
            # Gráfico de desafios por região
            fig4 = plot_challenges_by_region(filtered_radar)
            st.plotly_chart(fig4, use_container_width=True)
    
    # Aba 2: Recomendações
    with tab2:
        st.subheader("Recomendações de Soluções")
        
        # Verifica se a chave da API está configurada
        if not st.session_state.openai_api_key:
            st.warning("Configure a chave da API da OpenAI no menu lateral para habilitar o sistema de recomendação.")
        else:
            # Determina qual coluna usar para o nome da empresa
            company_column = 'Nome da empresa' if 'Nome da empresa' in radar_data.columns else 'Nome Empresa'
            
            # Lista de empresas para seleção
            empresas = sorted(filtered_radar[company_column].unique().tolist())
            
            if not empresas:
                st.warning("Nenhuma empresa encontrada com os filtros selecionados.")
            else:
                # Seleção de empresa
                selected_empresa = st.selectbox("Selecione uma empresa", empresas)
                
                # Obter dados da empresa selecionada
                company_data = filtered_radar[filtered_radar[company_column] == selected_empresa].iloc[0].to_dict()
                
                # Exibir informações da empresa
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### Informações da Empresa")
                    st.markdown(f"**Empresa:** {selected_empresa}")
                    st.markdown(f"**Cidade/Regional:** {company_data.get('Cidade', company_data.get('Município', ''))} / {company_data.get('Regional', company_data.get('Escritório Regional', ''))}")
                    st.markdown(f"**Setor:** {company_data.get('Setor', '')}")
                
                with col2:
                    challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in radar_data.columns else 'Categoria do Problema'
                    need_column = 'Necessidade específica' if 'Necessidade específica' in radar_data.columns else 'Descrição do Problema'
                    maturity_column = 'Maturidade em inovação' if 'Maturidade em inovação' in radar_data.columns else 'Média diagnóstico inicial'
                    
                    st.markdown(f"**Desafio priorizado:** {company_data.get(challenge_column, '')}")
                    st.markdown(f"**Necessidade específica:** {company_data.get(need_column, '')}")
                    st.markdown(f"**Maturidade em inovação:** {company_data.get(maturity_column, '')}")
                
                # Botão para gerar recomendações
                if st.button("Gerar Recomendações"):
                    with st.spinner("Gerando recomendações..."):
                        # Obter recomendações
                        recommendations = get_recommendations_for_company(
                            company_data, 
                            solutions_data, 
                            recommendation_system
                        )
                        
                        if not recommendations:
                            st.warning("Não foi possível gerar recomendações para esta empresa. Tente novamente ou selecione outra empresa.")
                        else:
                            st.success(f"Foram encontradas {len(recommendations)} recomendações para {selected_empresa}")
                            
                            # Exibir recomendações
                            for recommendation in recommendations:
                                display_recommendation_card(recommendation)
                            
                            # Exibir informações de depuração se o modo estiver ativado
                            if st.session_state.debug_mode:
                                with st.expander("Detalhes das Recomendações (Debug)"):
                                    st.json(recommendations)
    
    # Aba 3: Soluções
    with tab3:
        st.subheader("Catálogo de Soluções")
        
        # Filtros para soluções
        with st.container():
            st.markdown("### Filtros de Soluções")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Filtro por fonte
                fontes = ["Todas"] + sorted(solutions_data['Fonte'].unique().tolist())
                selected_fonte = st.selectbox("Fonte", fontes)
            
            with col2:
                # Filtro por modalidade
                modalidades = ["Todas"] + sorted(solutions_data['Modalidade'].unique().tolist())
                selected_modalidade = st.selectbox("Modalidade", modalidades)
            
            with col3:
                # Filtro por tema
                temas = ["Todos"] + sorted(solutions_data['Tema'].unique().tolist())
                selected_tema = st.selectbox("Tema", temas)
            
            # Busca por texto
            busca = st.text_input("Buscar por nome ou descrição")
        
        # Aplicar filtros às soluções
        solution_filters = {
            'fonte': selected_fonte,
            'modalidade': selected_modalidade,
            'tema': selected_tema,
            'busca': busca
        }
        
        # Exibir tabela de soluções
        filtered_solutions = display_solutions_table(solutions_data, solution_filters)
        
        # Exibir detalhes de uma solução selecionada
        if len(filtered_solutions) > 0:
            st.markdown("### Detalhes da Solução")
            
            # Seleção de solução
            solution_names = filtered_solutions['Nome da solução'].unique().tolist()
            selected_solution_name = st.selectbox("Selecione uma solução para ver detalhes", solution_names)
            
            # Exibir detalhes da solução selecionada
            selected_solution = filtered_solutions[filtered_solutions['Nome da solução'] == selected_solution_name].iloc[0].to_dict()
            display_solution_details(selected_solution)
    
    # Aba 4: Análise
    with tab4:
        st.subheader("Análise de Necessidades e Tendências")
        
        # Verifica se a chave da API está configurada
        if not st.session_state.openai_api_key:
            st.warning("Configure a chave da API da OpenAI no menu lateral para habilitar a análise.")
        else:
            # Análise de necessidades de uma empresa
            st.markdown("### Análise de Necessidades da Empresa")
            
            # Determina qual coluna usar para o nome da empresa
            company_column = 'Nome da empresa' if 'Nome da empresa' in radar_data.columns else 'Nome Empresa'
            
            # Lista de empresas para seleção
            empresas = sorted(filtered_radar[company_column].unique().tolist())
            
            if not empresas:
                st.warning("Nenhuma empresa encontrada com os filtros selecionados.")
            else:
                # Seleção de empresa
                selected_empresa = st.selectbox("Selecione uma empresa para análise", empresas, key="analysis_company")
                
                # Obter dados da empresa selecionada
                company_data = filtered_radar[filtered_radar[company_column] == selected_empresa].iloc[0].to_dict()
                
                # Botão para analisar necessidades
                if st.button("Analisar Necessidades"):
                    with st.spinner("Analisando necessidades..."):
                        # Analisar necessidades da empresa
                        analysis = recommendation_system.analyze_company_needs(company_data)
                        
                        if not analysis:
                            st.warning("Não foi possível analisar as necessidades desta empresa. Tente novamente.")
                        else:
                            # Exibir análise
                            st.markdown("#### Resumo das Necessidades")
                            st.write(analysis.get('resumo', 'Não disponível'))
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### Pontos Fortes")
                                for point in analysis.get('pontos_fortes', []):
                                    st.markdown(f"- {point}")
                            
                            with col2:
                                st.markdown("#### Pontos Fracos")
                                for point in analysis.get('pontos_fracos', []):
                                    st.markdown(f"- {point}")
                            
                            st.markdown("#### Áreas Prioritárias")
                            for area in analysis.get('areas_prioritarias', []):
                                st.markdown(f"- {area}")
                            
                            st.markdown("#### Tipos de Soluções Recomendadas")
                            for tipo in analysis.get('tipos_solucoes', []):
                                st.markdown(f"- {tipo}")
            
            # Sugestão de novos cursos
            st.markdown("### Sugestão de Novos Cursos")
            
            # Obter dados regionais
            regional_data = data_integration.get_regional_data(selected_regional if selected_regional != "Todas" else None)
            
            # Botão para sugerir novos cursos
            if st.button("Sugerir Novos Cursos"):
                with st.spinner("Gerando sugestões..."):
                    # Obter soluções já existentes
                    existing_solutions = solutions_data.to_dict('records')
                    
                    # Sugerir novos cursos
                    suggestions = recommendation_system.suggest_new_courses(regional_data, existing_solutions)
                    
                    if not suggestions:
                        st.warning("Não foi possível gerar sugestões de novos cursos. Tente novamente.")
                    else:
                        st.success(f"Foram geradas {len(suggestions)} sugestões de novos cursos")
                        
                        # Exibir sugestões
                        for suggestion in suggestions:
                            st.markdown(f"### {suggestion.get('number')}. {suggestion.get('name')}")
                            st.markdown(f"**Modalidade:** {suggestion.get('modalidade')}")
                            st.markdown(f"**Tema:** {suggestion.get('tema')}")
                            st.markdown(f"**Descrição:** {suggestion.get('descricao')}")
                            st.markdown(f"**Justificativa:** {suggestion.get('justificativa')}")
                            st.markdown("---")

# Executar a aplicação
if __name__ == "__main__":
    main()
