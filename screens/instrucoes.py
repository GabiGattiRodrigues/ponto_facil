"""Tela: instruções — mostra o conteúdo do README.md direto no app,
pra não precisar sair daqui pra consultar o passo a passo."""

from pathlib import Path

import streamlit as st

st.title("📖 Instruções")

readme_path = Path(__file__).parent.parent / "README.md"

if readme_path.exists():
    conteudo = readme_path.read_text(encoding="utf-8")
    st.markdown(conteudo, unsafe_allow_html=True)
else:
    st.warning(
        "Não encontrei o arquivo README.md na pasta do projeto. "
        "Confira se ele está junto dos outros arquivos (app.py, db.py etc.)."
    )
