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

# Importando os módulos personalizados
from google_sheets_integration import GoogleSheetsIntegration
from recommendation_system import RecommendationSystem

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

# Função para carregar a imagem do logo
def get_logo_base64():
    with open("logo_ali360.png", "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

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
def display_recommendation_card(title, body, col):
    with col:
        st.markdown(f"""
        <div class="recommendation-card">
            <div class="recommendation-title">{title}</div>
            <div class="recommendation-body">{body}</div>
        </div>
        """, unsafe_allow_html=True)

# Função para exibir o nível de aderência
def display_adherence(score):
    if score >= 8:
        return f'<span class="adherence-high">{score}/10 (Alta)</span>'
    elif score >= 4:
        return f'<span class="adherence-medium">{score}/10 (Média)</span>'
    else:
        return f'<span class="adherence-low">{score}/10 (Baixa)</span>'

# Função para carregar dados das planilhas
@st.cache_data(ttl=600)
def load_data():
    # Simulação de dados para desenvolvimento
    # Em produção, isso seria substituído pela integração real com Google Sheets
    
    # Dados do Radar de Inovação ALI 360
    radar_data = pd.DataFrame({
        'Nome da empresa': ['Empresa A', 'Empresa B', 'Empresa C', 'Empresa D', 'Empresa E'],
        'Cidade': ['Belo Horizonte', 'Uberlândia', 'Juiz de Fora', 'Belo Horizonte', 'Montes Claros'],
        'Regional': ['Central', 'Triângulo', 'Zona da Mata', 'Central', 'Norte'],
        'Setor': ['Comércio', 'Indústria', 'Serviços', 'Tecnologia', 'Agronegócio'],
        'Desafio priorizado': ['Vendas', 'Produção', 'Marketing Digital', 'Inovação', 'Gestão'],
        'Maturidade em inovação': ['Baixa', 'Média', 'Alta', 'Média', 'Baixa'],
        'Necessidade específica': ['Atrair clientes', 'Otimizar processos', 'Presença digital', 'Novos produtos', 'Controle financeiro'],
        'Estágio do diagnóstico': ['Nomear', 'Elaborar', 'Nomear', 'Elaborar', 'Nomear']
    })
    
    # Dados de Soluções Agendadas
    solutions_data = pd.DataFrame({
        'Nome da solução': ['Curso de Vendas', 'Consultoria em Processos', 'Workshop de Marketing Digital', 'Programa de Inovação', 'Gestão Financeira'],
        'Modalidade': ['Curso', 'Consultoria', 'Workshop', 'Programa', 'Curso'],
        'Cidade': ['Belo Horizonte', 'Uberlândia', 'Juiz de Fora', 'Belo Horizonte', 'Montes Claros'],
        'Regional': ['Central', 'Triângulo', 'Zona da Mata', 'Central', 'Norte'],
        'Tema': ['Vendas', 'Produção', 'Marketing', 'Inovação', 'Finanças'],
        'Data prevista': ['2025-05-10', '2025-05-15', '2025-05-20', '2025-05-25', '2025-05-30'],
        'Público-alvo': ['Comércio', 'Indústria', 'Serviços', 'Tecnologia', 'Agronegócio'],
        'Consultor responsável': ['João Silva', 'Maria Oliveira', 'Pedro Santos', 'Ana Costa', 'Carlos Souza']
    })
    
    return radar_data, solutions_data

# Função para filtrar dados por regional
def filter_data_by_regional(radar_data, solutions_data, selected_regional):
    if selected_regional == "Todas":
        return radar_data, solutions_data
    else:
        filtered_radar = radar_data[radar_data['Regional'] == selected_regional]
        filtered_solutions = solutions_data[solutions_data['Regional'] == selected_regional]
        return filtered_radar, filtered_solutions

# Função para gerar gráfico de empresas por estágio
def plot_companies_by_stage(radar_data):
    stage_counts = radar_data['Estágio do diagnóstico'].value_counts().reset_index()
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
    challenge_region = radar_data.groupby(['Regional', 'Desafio priorizado']).size().reset_index(name='count')
    
    fig = px.bar(
        challenge_region,
        x='Regional',
        y='count',
        color='Desafio priorizado',
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
    maturity_counts = radar_data['Maturidade em inovação'].value_counts().reset_index()
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
    challenge_sector = pd.crosstab(radar_data['Setor'], radar_data['Desafio priorizado'])
    
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

# Função principal da aplicação
def main():
    # Aplicar estilo personalizado
    apply_custom_style()
    
    # Exibir cabeçalho
    display_header()
    
    # Carregar dados
    radar_data, solutions_data = load_data()
    
    # Sidebar para filtros
    st.sidebar.header("Filtros")
    
    # Lista de regionais para o filtro
    regionais = ["Todas"] + sorted(radar_data['Regional'].unique().tolist())
    selected_regional = st.sidebar.selectbox("Regional", regionais)
    
    # Filtrar dados com base na regional selecionada
    filtered_radar, filtered_solutions = filter_data_by_regional(radar_data, solutions_data, selected_regional)
    
    # Exibir métricas principais
    st.markdown("## Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    
    display_metric_card("Empresas", len(filtered_radar), col1)
    display_metric_card("Soluções Agendadas", len(filtered_solutions), col2)
    display_metric_card("Desafios Únicos", filtered_radar['Desafio priorizado'].nunique(), col3)
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
        st.dataframe(
            filtered_radar[['Nome da empresa', 'Cidade', 'Setor', 'Desafio priorizado', 'Maturidade em inovação', 'Estágio do diagnóstico']],
            use_container_width=True
        )
    
    # Aba 2: Recomendações
    with tab2:
        st.markdown("### Recomendação Inteligente de Soluções")
        
        # Seleção de empresa
        selected_company = st.selectbox(
            "Selecione uma empresa para ver recomendações personalizadas:",
            filtered_radar['Nome da empresa'].tolist()
        )
        
        # Dados da empresa selecionada
        company_data = filtered_radar[filtered_radar['Nome da empresa'] == selected_company].iloc[0].to_dict()
        
        # Exibir informações da empresa
        st.markdown(f"#### Informações da Empresa: {selected_company}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Cidade/Regional:** {company_data['Cidade']}/{company_data['Regional']}")
            st.markdown(f"**Setor:** {company_data['Setor']}")
            st.markdown(f"**Maturidade em inovação:** {company_data['Maturidade em inovação']}")
        
        with col2:
            st.markdown(f"**Desafio priorizado:** {company_data['Desafio priorizado']}")
            st.markdown(f"**Necessidade específica:** {company_data['Necessidade específica']}")
            st.markdown(f"**Estágio do diagnóstico:** {company_data['Estágio do diagnóstico']}")
        
        # Simulação de recomendações (em produção, seria chamada a API da OpenAI)
        st.markdown("#### Soluções Recomendadas")
        
        # Recomendações simuladas
        recommendations = [
            {
                "solution_name": "Curso de Estratégias de Vendas",
                "justification": "Este curso aborda técnicas modernas de vendas e atração de clientes, alinhado com o desafio priorizado da empresa. O conteúdo é adaptado para empresas com baixa maturidade em inovação, oferecendo soluções práticas e de rápida implementação."
            },
            {
                "solution_name": "Consultoria em Marketing Digital",
                "justification": "A consultoria ajudará a empresa a estabelecer presença online efetiva, criando canais digitais para atrair novos clientes. Esta solução é especialmente relevante para o setor de comércio e complementa o desafio de vendas identificado."
            },
            {
                "solution_name": "Workshop de Experiência do Cliente",
                "justification": "Este workshop focado em melhorar a experiência do cliente pode ajudar a aumentar a retenção e fidelização, complementando as estratégias de atração. Aborda aspectos práticos que podem ser implementados mesmo com baixa maturidade em inovação."
            }
        ]
        
        # Exibir recomendações em cards
        for rec in recommendations:
            col1, _ = st.columns([3, 1])
            display_recommendation_card(rec["solution_name"], rec["justification"], col1)
        
        # Soluções já agendadas
        st.markdown("#### Soluções já agendadas na região")
        
        if not filtered_solutions.empty:
            st.dataframe(
                filtered_solutions[['Nome da solução', 'Modalidade', 'Tema', 'Data prevista']],
                use_container_width=True
            )
        else:
            st.info("Não há soluções agendadas para esta região.")
    
    # Aba 3: Cadastro de Ações
    with tab3:
        st.markdown("### Cadastro de Ações e Análise de Aderência")
        
        # Formulário para cadastro de nova solução
        with st.form("cadastro_solucao"):
            st.markdown("#### Cadastre uma nova solução")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome_solucao = st.text_input("Nome da solução")
                modalidade = st.selectbox("Modalidade", ["Curso", "Consultoria", "Workshop", "Programa", "Evento"])
                tema = st.text_input("Tema")
            
            with col2:
                cidade = st.text_input("Cidade")
                regional = st.selectbox("Regional", sorted(radar_data['Regional'].unique().tolist()))
                data_prevista = st.date_input("Data prevista")
            
            publico_alvo = st.text_input("Público-alvo")
            consultor = st.text_input("Consultor responsável")
            
            submitted = st.form_submit_button("Cadastrar Solução")
        
        if submitted:
            st.success(f"Solução '{nome_solucao}' cadastrada com sucesso!")
            
            # Simulação de análise de aderência
            st.markdown("#### Análise de Aderência às Empresas da Regional")
            
            # Empresas da regional selecionada
            regional_companies = filtered_radar[filtered_radar['Regional'] == regional]
            
            # Simulação de scores de aderência
            adherence_scores = {
                company: {
                    "score": np.random.randint(1, 11),
                    "justification": f"Análise de aderência para {company} baseada no tema '{tema}' e modalidade '{modalidade}'."
                } for company in regional_companies['Nome da empresa']
            }
            
            # Ordenar empresas por score de aderência
            sorted_companies = sorted(adherence_scores.items(), key=lambda x: x[1]["score"], reverse=True)
            
            # Exibir resultados de aderência
            for company, data in sorted_companies:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{company}**")
                    st.markdown(data["justification"])
                
                with col2:
                    st.markdown(f"Aderência: {display_adherence(data['score'])}", unsafe_allow_html=True)
                
                st.divider()
    
    # Aba 4: Curadoria Inteligente
    with tab4:
        st.markdown("### Curadoria Inteligente de Soluções")
        
        # Análise regional
        st.markdown(f"#### Análise da Regional: {selected_regional if selected_regional != 'Todas' else 'Todas as Regionais'}")
        
        # Desafios mais comuns
        top_challenges = filtered_radar['Desafio priorizado'].value_counts().reset_index()
        top_challenges.columns = ['Desafio', 'Quantidade']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Desafios mais comuns")
            st.dataframe(top_challenges, use_container_width=True)
        
        with col2:
            # Setores mais comuns
            top_sectors = filtered_radar['Setor'].value_counts().reset_index()
            top_sectors.columns = ['Setor', 'Quantidade']
            
            st.markdown("##### Setores mais comuns")
            st.dataframe(top_sectors, use_container_width=True)
        
        # Simulação de sugestões de cursos (em produção, seria chamada a API da OpenAI)
        st.markdown("#### Sugestões de Novas Soluções")
        
        # Sugestões simuladas
        suggestions = [
            {
                "solution_name": "Programa de Transformação Digital para Comércio",
                "modality": "Programa",
                "justification": "Com base na alta concentração de empresas do setor de comércio e desafios relacionados a vendas, este programa ajudaria a digitalizar operações e aumentar competitividade."
            },
            {
                "solution_name": "Workshop de Gestão da Inovação para Iniciantes",
                "modality": "Workshop",
                "justification": "Considerando o alto percentual de empresas com baixa maturidade em inovação, este workshop introduziria conceitos básicos e práticas simples de inovação."
            },
            {
                "solution_name": "Consultoria em Otimização de Processos",
                "modality": "Consultoria",
                "justification": "Atenderia às necessidades de empresas dos setores industrial e de serviços que enfrentam desafios de produtividade e eficiência operacional."
            },
            {
                "solution_name": "Curso de Marketing Digital para Pequenos Negócios",
                "modality": "Curso",
                "justification": "Alinhado com os desafios de vendas e marketing identificados, este curso ofereceria ferramentas práticas e acessíveis para empresas com recursos limitados."
            },
            {
                "solution_name": "Jornada de Experiência do Cliente",
                "modality": "Programa",
                "justification": "Focado em melhorar a retenção e satisfação de clientes, este programa complementaria as estratégias de vendas e marketing, abordando um aspecto frequentemente negligenciado."
            }
        ]
        
        # Exibir sugestões
        for i, sug in enumerate(suggestions):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{i+1}. {sug['solution_name']}** ({sug['modality']})")
                st.markdown(sug["justification"])
            
            with col2:
                st.button(f"Adicionar ao Plano #{i+1}", key=f"add_suggestion_{i}")
            
            st.divider()

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
