"""
auth.py — Proteção por senha simples (gate) pro app, usada quando ele está
hospedado publicamente (ex: Streamlit Community Cloud).

Só entra em ação se st.secrets["app_password"] estiver configurado — sem
isso (caso comum ao rodar localmente pra simular no Cursor), o app
funciona direto, sem pedir senha nenhuma.
"""

import streamlit as st


def _senha_configurada() -> str | None:
    try:
        return st.secrets.get("app_password")
    except Exception:
        return None


def exigir_senha():
    """Bloqueia o resto do app até a senha correta ser informada.

    Não faz nada (deixa passar direto) se nenhuma senha estiver configurada
    nos secrets — assim o app continua frictionless pra rodar localmente.
    """
    senha_correta = _senha_configurada()
    if not senha_correta:
        return

    if st.session_state.get("autenticado"):
        return

    st.title("🔒 Ponto Fácil")
    st.caption("Esse app é protegido por senha.")
    with st.form("form_login"):
        senha_digitada = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")
    if entrar:
        if senha_digitada == senha_correta:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()
