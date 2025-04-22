# Documentação do Radar de Inovação ALI 360

## Visão Geral

O Radar de Inovação ALI 360 é uma aplicação web interativa desenvolvida para o Sebrae Minas Gerais, que utiliza inteligência artificial para recomendar soluções (cursos, consultorias, programas, etc.) com base nos dados do programa Radar de Inovação ALI 360 e na base de Soluções Agendadas.

A aplicação integra-se com o Google Sheets para obter dados em tempo real, utiliza a API da OpenAI para gerar recomendações personalizadas, e apresenta uma interface amigável e intuitiva desenvolvida com Streamlit.

## Funcionalidades Principais

### 1. Dashboard Visual
- Visualização de empresas por estágio do diagnóstico
- Mapa de desafios por região
- Distribuição de maturidade em inovação
- Mapa de calor de desafios por setor

### 2. Recomendação Inteligente de Soluções
- Análise de desafios e necessidades das empresas
- Recomendação personalizada de cursos e consultorias
- Verificação de duplicidade com soluções já agendadas
- Justificativa detalhada para cada recomendação

### 3. Cadastro de Ações e Análise de Aderência
- Interface para cadastro de novos cursos
- Análise automática de aderência às empresas da regional
- Justificativa baseada em palavras-chave e estágios

### 4. Curadoria Inteligente
- Sugestão proativa de cursos não previstos
- Identificação de tendências e padrões de desafios
- Recomendação de ações para áreas descobertas

## Requisitos Técnicos

### Pré-requisitos
- Conta no Google Cloud Platform com API do Google Sheets habilitada
- Arquivo de credenciais JSON para autenticação com o Google Sheets
- Chave da API da OpenAI
- Acesso às planilhas do Google Sheets (Radar de Inovação ALI 360 e Soluções Agendadas)

### Dependências
- Python 3.7+
- Streamlit
- Pandas
- Plotly
- Matplotlib
- gspread
- oauth2client
- OpenAI Python SDK
- BeautifulSoup4
- Requests

## Instalação e Configuração

### 1. Instalação das Dependências
```bash
pip install streamlit pandas plotly matplotlib gspread oauth2client openai beautifulsoup4 requests
```

### 2. Configuração Inicial
Execute o script de configuração para configurar o acesso às planilhas do Google Sheets e à API da OpenAI:
```bash
streamlit run setup.py
```

Siga as instruções na interface para:
- Fazer upload do arquivo de credenciais do Google
- Configurar a chave da API da OpenAI
- Definir as URLs das planilhas do Google Sheets

### 3. Execução da Aplicação
Após a configuração inicial, execute a aplicação principal:
```bash
streamlit run app.py
```

## Estrutura do Projeto

```
radar-inovacao-ali360/
├── app.py                    # Aplicação principal
├── setup.py                  # Script de configuração
├── google_sheets_integration.py  # Módulo de integração com Google Sheets
├── recommendation_system.py  # Sistema de recomendação com IA
├── logo_ali360.png           # Logo do ALI 360
├── credentials.json          # Arquivo de credenciais do Google (gerado na configuração)
├── config.json               # Arquivo de configuração (gerado na configuração)
└── requirements.txt          # Lista de dependências
```

## Implantação no Streamlit Cloud

Para implantar a aplicação no Streamlit Cloud:

1. Crie uma conta no [Streamlit Cloud](https://streamlit.io/cloud)
2. Crie um repositório no GitHub com os arquivos do projeto
3. Conecte o repositório ao Streamlit Cloud
4. Configure as variáveis de ambiente necessárias (OPENAI_API_KEY)
5. Faça upload do arquivo de credenciais do Google como um arquivo secreto

## Uso da Aplicação

### Filtros Regionais
Use os filtros na barra lateral para selecionar a regional de interesse e visualizar dados específicos.

### Visualização de Dados
Navegue pelas abas para acessar diferentes visualizações e funcionalidades:
- **Dashboard**: Visualizações gráficas e lista de empresas
- **Recomendações**: Recomendações personalizadas para empresas selecionadas
- **Cadastro de Ações**: Cadastro de novas soluções e análise de aderência
- **Curadoria Inteligente**: Sugestões proativas de novas soluções

### Recomendações de Soluções
1. Selecione uma empresa na aba "Recomendações"
2. Visualize as informações da empresa
3. Analise as soluções recomendadas com suas justificativas
4. Verifique as soluções já agendadas na região

### Cadastro de Novas Soluções
1. Acesse a aba "Cadastro de Ações"
2. Preencha o formulário com os dados da nova solução
3. Clique em "Cadastrar Solução"
4. Analise a aderência da solução às empresas da regional

## Manutenção e Atualização

### Atualização de Dados
Os dados são atualizados automaticamente a partir das planilhas do Google Sheets. Não é necessário atualizar a aplicação quando os dados das planilhas são modificados.

### Atualização da Aplicação
Para atualizar a aplicação:
1. Modifique os arquivos necessários
2. Faça commit das alterações no repositório GitHub
3. O Streamlit Cloud atualizará automaticamente a aplicação

## Suporte e Contato

Para suporte técnico ou dúvidas sobre a aplicação, entre em contato com a equipe de desenvolvimento através do email: [contato@exemplo.com]

---

Desenvolvido para o Sebrae Minas Gerais - Programa ALI 360
