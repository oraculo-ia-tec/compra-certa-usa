# COMPRA CERTA USA

Plataforma de redirecionamento de compras dos EUA para o Brasil, construida em Streamlit
com SQLAlchemy/SQLite e tools internas no padrao MCP (sem FastAPI, sem servidor separado).

## Como executar localmente

1. Crie um ambiente virtual e instale as dependencias:
   pip install -r requirements.txt

2. Copie o arquivo de secrets de exemplo:
   cp secrets.toml.example .streamlit/secrets.toml
   (ajuste ADMIN_PASSWORD e DATABASE_URL conforme necessario)

3. Execute o app:
   streamlit run app.py

## Estrutura do projeto

- models/ -> modelos SQLAlchemy e conexao com banco (Agente DBA-ARCH)
- services/ -> regras de negocio e contratos internos DTO (Agente CORE-LOGIC)
- tools/ -> tools internas estilo MCP, chamadas diretamente pelo Streamlit
- pages/ -> telas do sistema (Agente UI-SYSTEMS):
  1. Onboarding (cadastro/login)
  2. Novo Pedido
  3. Orcamento
  4. Meus Pedidos
  5. Detalhe do Pedido
  6. Administracao (protegida por senha de operador)
  7. Rastreamento (visao do cliente)
- app.py -> ponto de entrada do Streamlit

## Hipoteses assumidas (a validar com o time de negocio)

1. Cotacao do dolar fixa de fallback (5.4) quando API externa nao estiver configurada.
2. Regra de imposto simplificada (60% sobre valor que exceder USD 1000 convertido).
3. Divisao de pacotes por lote fixo de 3 itens.
4. Cotacao de frete FedEx/UPS/DHL simulada - substituir por integracao real via adapters.
5. Upload de fotos salvo localmente em uploads/ - migrar para storage externo (S3) antes de producao.
6. Hash de senha em SHA-256 simples - migrar para bcrypt antes de producao.

## Deploy no Streamlit Community Cloud

1. Suba este repositorio no GitHub.
2. Em share.streamlit.io, aponte para app.py como entrypoint.
3. Configure os secrets (ADMIN_PASSWORD, DATABASE_URL) no painel do Streamlit Cloud.
