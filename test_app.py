import streamlit as st
import pandas as pd
import os
import sys
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_app')

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa os módulos necessários
try:
    from data_integration_improved import DataIntegration
    from recommendation_system_improved import RecommendationSystem
    logger.info("Módulos importados com sucesso")
except Exception as e:
    logger.error(f"Erro ao importar módulos: {e}")

# Configuração da página
st.set_page_config(
    page_title="Teste do Radar ALI 360",
    page_icon="🧪",
    layout="wide"
)

# Cores do ALI 360
ALI_BLUE = "#0077B5"
ALI_LIGHT_BLUE = "#00A0DC"

# Estilo personalizado
st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    h1, h2, h3 {{
        color: {ALI_BLUE};
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
    .test-section {{
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }}
    .success {{
        color: green;
        font-weight: bold;
    }}
    .error {{
        color: red;
        font-weight: bold;
    }}
    .warning {{
        color: orange;
        font-weight: bold;
    }}
</style>
""", unsafe_allow_html=True)

# Função principal
def main():
    # Cabeçalho
    st.image("logo_ali360.png", width=150)
    st.title("Teste do Radar de Inovação ALI 360")
    st.markdown("### Ferramenta para testar os componentes da aplicação")
    
    # Verifica se a chave da API está configurada
    api_key_file = "openai_api_key.txt"
    api_key = ""
    
    if os.path.exists(api_key_file):
        with open(api_key_file, "r") as f:
            api_key = f.read().strip()
        
        if api_key:
            st.success("Chave da API da OpenAI configurada")
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            st.warning("Chave da API da OpenAI não configurada. Configure-a no arquivo setup.py")
    else:
        st.warning("Chave da API da OpenAI não configurada. Configure-a no arquivo setup.py")
    
    # Abas para diferentes testes
    tab1, tab2, tab3, tab4 = st.tabs(["Dados do Radar", "Soluções", "Recomendações", "Interface"])
    
    # Aba 1: Teste de dados do radar
    with tab1:
        st.markdown('<div class="test-section">', unsafe_allow_html=True)
        st.subheader("Teste de Dados do Radar")
        
        if st.button("Carregar Dados do Radar", key="load_radar"):
            with st.spinner("Carregando dados do radar..."):
                try:
                    # Inicializa a integração de dados
                    data_integration = DataIntegration(debug=True)
                    
                    # Carrega os dados do radar
                    radar_data = data_integration.load_radar_data_from_excel('/home/ubuntu/upload/')
                    
                    if radar_data is not None and not radar_data.empty:
                        st.success(f"Dados do radar carregados com sucesso! ({len(radar_data)} registros)")
                        
                        # Exibe informações sobre os dados
                        st.markdown("#### Informações dos Dados")
                        st.write(f"Número de registros: {len(radar_data)}")
                        st.write(f"Colunas: {', '.join(radar_data.columns.tolist())}")
                        
                        # Exibe uma amostra dos dados
                        st.markdown("#### Amostra dos Dados")
                        st.dataframe(radar_data.head())
                        
                        # Exibe estatísticas básicas
                        st.markdown("#### Estatísticas Básicas")
                        
                        # Verifica quais colunas usar
                        regional_column = 'Regional' if 'Regional' in radar_data.columns else 'Escritório Regional'
                        challenge_column = 'Desafio priorizado' if 'Desafio priorizado' in radar_data.columns else 'Categoria do Problema'
                        
                        # Contagem por regional
                        st.markdown("**Contagem por Regional:**")
                        st.write(radar_data[regional_column].value_counts())
                        
                        # Contagem por setor
                        st.markdown("**Contagem por Setor:**")
                        st.write(radar_data['Setor'].value_counts())
                        
                        # Contagem por desafio
                        st.markdown("**Contagem por Desafio:**")
                        st.write(radar_data[challenge_column].value_counts())
                    else:
                        st.error("Não foi possível carregar os dados do radar.")
                
                except Exception as e:
                    st.error(f"Erro ao carregar dados do radar: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aba 2: Teste de soluções
    with tab2:
        st.markdown('<div class="test-section">', unsafe_allow_html=True)
        st.subheader("Teste de Soluções")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Carregar Soluções da Planilha", key="load_solutions"):
                with st.spinner("Carregando soluções da planilha..."):
                    try:
                        # Inicializa a integração de dados
                        data_integration = DataIntegration(debug=True)
                        
                        # Carrega os dados das soluções
                        solutions_data = data_integration.load_solutions_from_excel('/home/ubuntu/upload/')
                        
                        if solutions_data is not None and not solutions_data.empty:
                            st.success(f"Soluções carregadas com sucesso! ({len(solutions_data)} registros)")
                            
                            # Exibe informações sobre os dados
                            st.markdown("#### Informações das Soluções")
                            st.write(f"Número de soluções: {len(solutions_data)}")
                            st.write(f"Colunas: {', '.join(solutions_data.columns.tolist())}")
                            
                            # Exibe uma amostra dos dados
                            st.markdown("#### Amostra das Soluções")
                            st.dataframe(solutions_data.head())
                            
                            # Exibe estatísticas básicas
                            st.markdown("#### Estatísticas Básicas")
                            
                            # Contagem por fonte
                            if 'Fonte' in solutions_data.columns:
                                st.markdown("**Contagem por Fonte:**")
                                st.write(solutions_data['Fonte'].value_counts())
                            
                            # Contagem por modalidade
                            if 'Modalidade' in solutions_data.columns:
                                st.markdown("**Contagem por Modalidade:**")
                                st.write(solutions_data['Modalidade'].value_counts())
                            
                            # Contagem por tema
                            if 'Tema' in solutions_data.columns:
                                st.markdown("**Contagem por Tema:**")
                                st.write(solutions_data['Tema'].value_counts())
                        else:
                            st.error("Não foi possível carregar as soluções da planilha.")
                    
                    except Exception as e:
                        st.error(f"Erro ao carregar soluções da planilha: {e}")
        
        with col2:
            if st.button("Coletar Soluções da Web", key="scrape_solutions"):
                with st.spinner("Coletando soluções da web (isso pode levar alguns minutos)..."):
                    try:
                        # Inicializa a integração de dados
                        data_integration = DataIntegration(debug=True)
                        
                        # Coleta soluções da web
                        web_solutions = data_integration.scrape_web_solutions()
                        
                        if web_solutions is not None and len(web_solutions) > 0:
                            st.success(f"Soluções coletadas da web com sucesso! ({len(web_solutions)} soluções)")
                            
                            # Converte para DataFrame para exibição
                            web_df = pd.DataFrame(web_solutions)
                            
                            # Exibe informações sobre os dados
                            st.markdown("#### Informações das Soluções Web")
                            st.write(f"Número de soluções: {len(web_df)}")
                            st.write(f"Colunas: {', '.join(web_df.columns.tolist())}")
                            
                            # Exibe uma amostra das soluções
                            st.markdown("#### Amostra das Soluções Web")
                            st.dataframe(web_df.head())
                            
                            # Exibe estatísticas básicas
                            st.markdown("#### Estatísticas Básicas")
                            
                            # Contagem por fonte
                            if 'Fonte' in web_df.columns:
                                st.markdown("**Contagem por Fonte:**")
                                st.write(web_df['Fonte'].value_counts())
                            
                            # Contagem por modalidade
                            if 'Modalidade' in web_df.columns:
                                st.markdown("**Contagem por Modalidade:**")
                                st.write(web_df['Modalidade'].value_counts())
                            
                            # Contagem por tema
                            if 'Tema' in web_df.columns:
                                st.markdown("**Contagem por Tema:**")
                                st.write(web_df['Tema'].value_counts())
                        else:
                            st.warning("Nenhuma solução foi coletada da web.")
                    
                    except Exception as e:
                        st.error(f"Erro ao coletar soluções da web: {e}")
        
        # Botão para combinar soluções
        if st.button("Combinar Todas as Soluções", key="combine_solutions"):
            with st.spinner("Combinando soluções..."):
                try:
                    # Inicializa a integração de dados
                    data_integration = DataIntegration(debug=True)
                    
                    # Carrega os dados das soluções
                    data_integration.load_solutions_from_excel('/home/ubuntu/upload/')
                    
                    # Coleta soluções da web
                    data_integration.scrape_web_solutions()
                    
                    # Combina as soluções
                    combined_solutions = data_integration.combine_solutions()
                    
                    if combined_solutions is not None and not combined_solutions.empty:
                        st.success(f"Soluções combinadas com sucesso! ({len(combined_solutions)} soluções)")
                        
                        # Exibe informações sobre os dados
                        st.markdown("#### Informações das Soluções Combinadas")
                        st.write(f"Número de soluções: {len(combined_solutions)}")
                        st.write(f"Colunas: {', '.join(combined_solutions.columns.tolist())}")
                        
                        # Exibe uma amostra das soluções
                        st.markdown("#### Amostra das Soluções Combinadas")
                        st.dataframe(combined_solutions.head())
                        
                        # Exibe estatísticas básicas
                        st.markdown("#### Estatísticas Básicas")
                        
                        # Contagem por fonte
                        if 'Fonte' in combined_solutions.columns:
                            st.markdown("**Contagem por Fonte:**")
                            st.write(combined_solutions['Fonte'].value_counts())
                        
                        # Contagem por modalidade
                        if 'Modalidade' in combined_solutions.columns:
                            st.markdown("**Contagem por Modalidade:**")
                            st.write(combined_solutions['Modalidade'].value_counts())
                        
                        # Contagem por tema
                        if 'Tema' in combined_solutions.columns:
                            st.markdown("**Contagem por Tema:**")
                            st.write(combined_solutions['Tema'].value_counts())
                    else:
                        st.error("Não foi possível combinar as soluções.")
                
                except Exception as e:
                    st.error(f"Erro ao combinar soluções: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aba 3: Teste de recomendações
    with tab3:
        st.markdown('<div class="test-section">', unsafe_allow_html=True)
        st.subheader("Teste de Recomendações")
        
        # Verifica se a chave da API está configurada
        if not api_key:
            st.warning("Configure a chave da API da OpenAI para testar as recomendações.")
        else:
            # Carrega os dados para o teste
            if st.button("Preparar Dados para Teste", key="prepare_data"):
                with st.spinner("Preparando dados..."):
                    try:
                        # Inicializa a integração de dados
                        data_integration = DataIntegration(debug=True)
                        
                        # Carrega os dados do radar
                        radar_data = data_integration.load_radar_data_from_excel('/home/ubuntu/upload/')
                        
                        # Carrega os dados das soluções
                        data_integration.load_solutions_from_excel('/home/ubuntu/upload/')
                        
                        # Coleta soluções da web
                        data_integration.scrape_web_solutions()
                        
                        # Combina as soluções
                        combined_solutions = data_integration.combine_solutions()
                        
                        if radar_data is not None and not radar_data.empty and combined_solutions is not None and not combined_solutions.empty:
                            st.success("Dados preparados com sucesso!")
                            
                            # Armazena os dados na sessão
                            st.session_state.radar_data = radar_data
                            st.session_state.solutions_data = combined_solutions
                            
                            # Determina qual coluna usar para o nome da empresa
                            company_column = 'Nome da empresa' if 'Nome da empresa' in radar_data.columns else 'Nome Empresa'
                            
                            # Lista de empresas para seleção
                            empresas = sorted(radar_data[company_column].unique().tolist())
                            st.session_state.empresas = empresas
                            
                            st.markdown(f"**{len(empresas)} empresas disponíveis para teste**")
                        else:
                            st.error("Não foi possível preparar os dados para teste.")
                    
                    except Exception as e:
                        st.error(f"Erro ao preparar dados para teste: {e}")
            
            # Se os dados estiverem preparados, exibe o seletor de empresa
            if 'empresas' in st.session_state and 'radar_data' in st.session_state and 'solutions_data' in st.session_state:
                # Seleção de empresa
                selected_empresa = st.selectbox("Selecione uma empresa para teste", st.session_state.empresas)
                
                # Botão para testar recomendações
                if st.button("Testar Recomendações", key="test_recommendations"):
                    with st.spinner("Gerando recomendações..."):
                        try:
                            # Inicializa o sistema de recomendação
                            recommendation_system = RecommendationSystem(api_key=api_key, debug=True)
                            
                            # Determina qual coluna usar para o nome da empresa
                            company_column = 'Nome da empresa' if 'Nome da empresa' in st.session_state.radar_data.columns else 'Nome Empresa'
                            
                            # Obter dados da empresa selecionada
                            company_data = st.session_state.radar_data[st.session_state.radar_data[company_column] == selected_empresa].iloc[0].to_dict()
                            
                            # Obter recomendações
                            recommendations = recommendation_system.get_recommendations(
                                company_data, 
                                st.session_state.solutions_data.to_dict('records')
                            )
                            
                            if recommendations and len(recommendations) > 0:
                                st.success(f"Recomendações geradas com sucesso! ({len(recommendations)} recomendações)")
                                
                                # Exibe as recomendações
                                st.markdown("#### Recomendações Geradas")
                                
                                for i, rec in enumerate(recommendations):
                                    st.markdown(f"**{i+1}. {rec.get('solution_name', '')}**")
                                    st.markdown(f"*Justificativa:* {rec.get('justification', '')}")
                                    
                                    # Exibe dados adicionais da solução
                                    solution_data = rec.get('solution_data', {})
                                    if solution_data:
                                        with st.expander("Detalhes da Solução"):
                                            st.write(f"**Fonte:** {solution_data.get('Fonte', 'Não informado')}")
                                            st.write(f"**Modalidade:** {solution_data.get('Modalidade', 'Não informado')}")
                                            st.write(f"**Tema:** {solution_data.get('Tema', 'Não informado')}")
                                            
                                            if 'Link' in solution_data and solution_data['Link']:
                                                st.write(f"**Link:** [{solution_data['Link']}]({solution_data['Link']})")
                                            
                                            st.write(f"**Descrição:** {solution_data.get('Descrição', 'Não informado')}")
                                    
                                    st.markdown("---")
                                
                                # Exibe informações de depuração
                                with st.expander("Informações de Depuração"):
                                    st.json(recommendations)
                            else:
                                st.warning("Nenhuma recomendação foi gerada.")
                        
                        except Exception as e:
                            st.error(f"Erro ao gerar recomendações: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aba 4: Teste da interface
    with tab4:
        st.markdown('<div class="test-section">', unsafe_allow_html=True)
        st.subheader("Teste da Interface")
        
        st.markdown("""
        Para testar a interface completa, execute o seguinte comando no terminal:
        ```
        streamlit run app_improved.py
        ```
        
        Isso iniciará a aplicação principal com todas as funcionalidades.
        """)
        
        # Botão para iniciar a aplicação principal
        if st.button("Iniciar Aplicação Principal", key="start_app"):
            try:
                # Verifica se o arquivo existe
                if os.path.exists("app_improved.py"):
                    # Inicia a aplicação em um novo processo
                    import subprocess
                    process = subprocess.Popen(["streamlit", "run", "app_improved.py"])
                    
                    st.success("Aplicação principal iniciada! Acesse-a em uma nova aba do navegador.")
                    st.markdown("URL: http://localhost:8501")
                else:
                    st.error("Arquivo app_improved.py não encontrado.")
            
            except Exception as e:
                st.error(f"Erro ao iniciar a aplicação principal: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# Executa a aplicação
if __name__ == "__main__":
    main()
