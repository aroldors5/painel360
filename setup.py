import streamlit as st
import pandas as pd
import os
import sys

# Adiciona o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa os módulos necessários
from data_integration_improved import DataIntegration
from recommendation_system_improved import RecommendationSystem

# Configuração da página
st.set_page_config(
    page_title="Configuração do Radar ALI 360",
    page_icon="⚙️",
    layout="centered"
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
        max-width: 800px;
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
    .config-section {{
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
    }}
</style>
""", unsafe_allow_html=True)

# Função principal
def main():
    # Cabeçalho
    st.image("logo_ali360.png", width=150)
    st.title("Configuração do Radar de Inovação ALI 360")
    st.markdown("### Configure os parâmetros necessários para o funcionamento do sistema")
    
    # Seção de configuração da API da OpenAI
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.subheader("1. Configuração da API da OpenAI")
    st.markdown("""
    O sistema de recomendação utiliza a API da OpenAI para gerar recomendações personalizadas.
    Você precisa fornecer uma chave de API válida para utilizar esta funcionalidade.
    """)
    
    # Verifica se a chave já está salva
    api_key_file = "openai_api_key.txt"
    saved_api_key = ""
    
    if os.path.exists(api_key_file):
        with open(api_key_file, "r") as f:
            saved_api_key = f.read().strip()
    
    # Campo para inserir a chave da API
    api_key = st.text_input(
        "Chave da API da OpenAI",
        value=saved_api_key,
        type="password",
        help="Insira sua chave da API da OpenAI. Ela será salva localmente para uso futuro."
    )
    
    # Botão para salvar a chave
    if st.button("Salvar Chave da API"):
        if api_key:
            with open(api_key_file, "w") as f:
                f.write(api_key)
            st.success("Chave da API salva com sucesso!")
            
            # Define a variável de ambiente
            os.environ["OPENAI_API_KEY"] = api_key
        else:
            st.error("Por favor, insira uma chave de API válida.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de teste de conexão
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.subheader("2. Teste de Conexão")
    st.markdown("""
    Verifique se a conexão com a API da OpenAI está funcionando corretamente.
    """)
    
    # Botão para testar a conexão
    if st.button("Testar Conexão"):
        if not api_key:
            st.error("Por favor, configure a chave da API primeiro.")
        else:
            try:
                # Inicializa o sistema de recomendação
                recommendation_system = RecommendationSystem(api_key=api_key)
                
                # Testa a conexão
                test_prompt = "Olá, estou testando a conexão com a API da OpenAI."
                response = recommendation_system.test_connection(test_prompt)
                
                if response:
                    st.success("Conexão com a API da OpenAI estabelecida com sucesso!")
                    st.markdown(f"**Resposta da API:** {response}")
                else:
                    st.error("Não foi possível obter uma resposta da API. Verifique sua chave e tente novamente.")
            except Exception as e:
                st.error(f"Erro ao conectar com a API da OpenAI: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de teste de dados
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.subheader("3. Verificação de Dados")
    st.markdown("""
    Verifique se os dados do radar e das soluções estão sendo carregados corretamente.
    """)
    
    # Botão para verificar dados
    if st.button("Verificar Dados"):
        with st.spinner("Verificando dados..."):
            try:
                # Inicializa a integração de dados
                data_integration = DataIntegration(debug=True)
                
                # Carrega os dados do radar
                radar_data = data_integration.load_radar_data_from_excel('/home/ubuntu/upload/')
                
                if radar_data is not None and not radar_data.empty:
                    st.success(f"Dados do radar carregados com sucesso! ({len(radar_data)} registros)")
                    
                    # Exibe uma amostra dos dados
                    st.markdown("**Amostra dos dados do radar:**")
                    st.dataframe(radar_data.head())
                else:
                    st.error("Não foi possível carregar os dados do radar.")
                
                # Carrega os dados das soluções
                solutions_data = data_integration.load_solutions_from_excel('/home/ubuntu/upload/')
                
                if solutions_data is not None and not solutions_data.empty:
                    st.success(f"Dados das soluções carregados com sucesso! ({len(solutions_data)} registros)")
                    
                    # Exibe uma amostra dos dados
                    st.markdown("**Amostra dos dados das soluções:**")
                    st.dataframe(solutions_data.head())
                else:
                    st.error("Não foi possível carregar os dados das soluções.")
                
                # Tenta coletar soluções da web
                st.markdown("**Coletando soluções da web (isso pode levar alguns minutos)...**")
                try:
                    web_solutions = data_integration.scrape_web_solutions()
                    
                    if web_solutions is not None and len(web_solutions) > 0:
                        st.success(f"Soluções coletadas da web com sucesso! ({len(web_solutions)} soluções)")
                        
                        # Converte para DataFrame para exibição
                        web_df = pd.DataFrame(web_solutions)
                        
                        # Exibe uma amostra das soluções
                        st.markdown("**Amostra das soluções coletadas da web:**")
                        st.dataframe(web_df.head())
                    else:
                        st.warning("Nenhuma solução foi coletada da web.")
                except Exception as e:
                    st.error(f"Erro ao coletar soluções da web: {e}")
            
            except Exception as e:
                st.error(f"Erro ao verificar dados: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Seção de inicialização da aplicação
    st.markdown('<div class="config-section">', unsafe_allow_html=True)
    st.subheader("4. Iniciar Aplicação")
    st.markdown("""
    Após configurar a API e verificar os dados, você pode iniciar a aplicação principal.
    """)
    
    # Botão para iniciar a aplicação
    if st.button("Iniciar Aplicação"):
        if not api_key:
            st.error("Por favor, configure a chave da API primeiro.")
        else:
            st.success("Configuração concluída! Você pode iniciar a aplicação principal agora.")
            st.markdown("""
            Para iniciar a aplicação, execute o seguinte comando no terminal:
            ```
            streamlit run app_improved.py
            ```
            """)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Adiciona método de teste de conexão ao RecommendationSystem
def add_test_connection_method():
    # Verifica se o arquivo existe
    if os.path.exists("recommendation_system_improved.py"):
        with open("recommendation_system_improved.py", "r") as f:
            content = f.read()
        
        # Verifica se o método já existe
        if "def test_connection" not in content:
            # Adiciona o método ao final da classe
            new_method = """
    def test_connection(self, test_prompt):
        \"\"\"
        Testa a conexão com a API da OpenAI.
        
        Args:
            test_prompt (str): Prompt de teste
            
        Returns:
            str: Resposta da API ou None em caso de erro
        \"\"\"
        try:
            # Verifica se a chave da API está configurada
            if not self.api_key:
                logger.error("API key não configurada")
                return None
            
            # Faz a chamada para a API da OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é um assistente de teste."},
                    {"role": "user", "content": test_prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            
            # Extrai o texto da resposta
            response_text = response.choices[0].message.content.strip()
            
            logger.info("Teste de conexão com a API realizado com sucesso")
            return response_text
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão com a API: {e}")
            return None"""
            
            # Adiciona o método antes do último fechamento de chave
            content = content.rstrip()
            if content.endswith("}"):
                content = content[:-1] + new_method + "\n}"
            else:
                content += new_method
            
            # Salva o arquivo modificado
            with open("recommendation_system_improved.py", "w") as f:
                f.write(content)

# Executa a função para adicionar o método de teste
add_test_connection_method()

# Executa a aplicação
if __name__ == "__main__":
    main()
