"""
app.py — Ponto Fácil: ponto de entrada do app (roteador das telas).

Roda com:  streamlit run app.py

Esse arquivo só cuida de configuração compartilhada (tema, aviso de venv,
banco de dados) e da navegação entre telas. O conteúdo de cada tela mora em
screens/ — arquivos com nomes simples (sem emoji), para não depender da
forma como o sistema de arquivos/zip lida com nomes de arquivo com
caracteres especiais (isso já causou nomes de aba corrompidos numa versão
anterior). O emoji de cada aba agora vive só como texto dentro do código
Python (seguro em qualquer sistema), não no nome do arquivo.
"""

import streamlit as st

import auth
import db
import env_check
import theme

st.set_page_config(
    page_title="Ponto Fácil",
    page_icon="🕒",
    layout="wide",
)

auth.exigir_senha()

db.init_db()
theme.inject_css()

if not env_check.rodando_em_venv():
    st.caption(
        "⚠️ Este app não está rodando dentro de um ambiente virtual (venv). "
        "Recomendado: use o script `setup_e_rodar` (veja o README) para criar e "
        "ativar o venv automaticamente da próxima vez."
    )

pagina_inicio = st.Page("screens/inicio.py", title="Início", icon="🏠", default=True)
pagina_instrucoes = st.Page("screens/instrucoes.py", title="Instruções", icon="📖")
pagina_cadastro = st.Page("screens/cadastrar_empresa.py", title="Cadastrar Empresa", icon="🏢")
pagina_ponto = st.Page("screens/bater_ponto.py", title="Bater Ponto", icon="🕒")
pagina_feriados = st.Page("screens/feriados_municipais.py", title="Feriados Municipais", icon="📅")
pagina_dashboard = st.Page("screens/dashboard.py", title="Dashboard", icon="📊")
pagina_config = st.Page("screens/configuracoes.py", title="Configurações", icon="⚙️")

navegacao = st.navigation(
    [pagina_inicio, pagina_instrucoes, pagina_cadastro, pagina_ponto, pagina_feriados,
     pagina_dashboard, pagina_config]
)
navegacao.run()
