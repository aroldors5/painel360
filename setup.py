import streamlit as st
import os

# Configuração da página
st.set_page_config(
    page_title="Radar de Inovação ALI 360 - Configuração",
    page_icon="🔑",
    layout="centered"
)

st.image("logo_ali360.png", width=400)
st.title("Configuração do Radar de Inovação ALI 360")

st.markdown("""
## Bem-vindo à configuração inicial

Para utilizar o Radar de Inovação ALI 360, você precisa configurar o acesso às planilhas do Google Sheets e à API da OpenAI.

### 1. Configuração do Google Sheets

Para acessar as planilhas do Google Sheets, você precisa criar um projeto no Google Cloud Platform e habilitar a API do Google Sheets.

**Passos:**
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto
3. Habilite a API do Google Sheets
4. Crie uma conta de serviço e baixe o arquivo de credenciais JSON
5. Compartilhe suas planilhas com o email da conta de serviço
""")

# Área para upload do arquivo de credenciais
st.markdown("### Upload do arquivo de credenciais do Google")
credentials_file = st.file_uploader("Faça upload do arquivo JSON de credenciais", type=["json"])

if credentials_file is not None:
    credentials_content = credentials_file.getvalue().decode()
    st.success("Arquivo de credenciais carregado com sucesso!")
    
    # Salvar as credenciais em um arquivo
    with open("credentials.json", "w") as f:
        f.write(credentials_content)

# Configuração da API da OpenAI
st.markdown("""
### 2. Configuração da API da OpenAI

Para utilizar o sistema de recomendação baseado em IA, você precisa de uma chave da API da OpenAI.

**Passos:**
1. Acesse o [site da OpenAI](https://platform.openai.com/)
2. Crie uma conta ou faça login
3. Acesse a seção de API Keys
4. Crie uma nova chave de API
""")

# Campo para a chave da API
openai_api_key = st.text_input("Chave da API da OpenAI", type="password")

if openai_api_key:
    # Salvar a chave da API como variável de ambiente
    os.environ["OPENAI_API_KEY"] = openai_api_key
    st.success("Chave da API da OpenAI configurada com sucesso!")

# URLs das planilhas
st.markdown("""
### 3. URLs das planilhas do Google Sheets

Informe as URLs das planilhas que serão utilizadas pelo sistema.
""")

radar_url = st.text_input("URL da planilha do Radar de Inovação ALI 360", value="https://docs.google.com/spreadsheets/d/1FvYfui2M96HUAdzBblEydLu0w2Gs7qJBpJ42-1EVsCM/edit?usp=drive_link")
solutions_url = st.text_input("URL da planilha de Soluções Agendadas", value="https://docs.google.com/spreadsheets/d/13Vsvtlef6opTDHnzMzZ9V9lD7RlXRgp2/edit?usp=sharing&ouid=112135765612817780189&rtpof=true&sd=true")

if radar_url and solutions_url:
    # Salvar as URLs em um arquivo de configuração
    with open("config.json", "w") as f:
        import json
        json.dump({
            "radar_url": radar_url,
            "solutions_url": solutions_url
        }, f)
    st.success("URLs das planilhas configuradas com sucesso!")

# Botão para testar a configuração
if st.button("Testar Configuração"):
    if not os.path.exists("credentials.json"):
        st.error("Arquivo de credenciais não encontrado. Faça o upload do arquivo JSON.")
    elif not openai_api_key:
        st.error("Chave da API da OpenAI não configurada.")
    elif not radar_url or not solutions_url:
        st.error("URLs das planilhas não configuradas.")
    else:
        st.success("Configuração completa! Você pode iniciar o aplicativo principal agora.")
        
        # Adicionar link para o aplicativo principal
        st.markdown("""
        ### Próximos passos
        
        Agora você pode iniciar o aplicativo principal executando:
        
        ```
        streamlit run app.py
        ```
        
        Ou clique no botão abaixo para iniciar:
        """)
        
        if st.button("Iniciar Aplicativo Principal"):
            st.info("Redirecionando para o aplicativo principal...")
            # Em um ambiente real, isso redirecionaria para o app.py
            # Como estamos em um ambiente de demonstração, apenas exibimos a mensagem
