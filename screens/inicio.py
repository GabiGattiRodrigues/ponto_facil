"""Tela: início — lembretes e visão geral das empresas."""

import streamlit as st

import db
import theme
import utils

st.title("🕒 Ponto Fácil")
st.caption("Controle de ponto simples, com feriados automáticos e acompanhamento em dashboard.")

empresas = db.listar_empresas()

if not empresas:
    st.info(
        "Você ainda não cadastrou nenhuma empresa. "
        "Vá até **🏢 Cadastrar Empresa**, no menu à esquerda, para começar."
    )
    st.stop()

# --- Lembretes de ponto não registrado -------------------------------------
st.subheader("🔔 Lembretes")
algum_alerta = False
for empresa in empresas:
    faltando = utils.dias_uteis_sem_registro(empresa, janela_dias=14)
    if faltando:
        algum_alerta = True
        dias_fmt = ", ".join(utils.formatar_data_br(d) for d in faltando[-5:])
        a_mais = f" (+{len(faltando) - 5} dia(s) anterior(es))" if len(faltando) > 5 else ""
        st.warning(
            f"**{empresa['nome']}** está sem registro de ponto em: {dias_fmt}{a_mais}. "
            "Não esqueça de bater o ponto!"
        )
if not algum_alerta:
    st.success("Tudo em dia! Nenhum ponto pendente nos últimos 14 dias úteis. ✅")

st.divider()

# --- Visão geral das empresas ------------------------------------------------
st.subheader("🏢 Suas empresas")
cols = st.columns(min(3, len(empresas)) or 1)
for i, empresa in enumerate(empresas):
    banco = db.banco_de_horas(empresa["id"])
    with cols[i % len(cols)]:
        st.markdown(
            f"""
            <div class="ponto-card">
                <h4 style="margin-top:0;">{empresa['nome']}</h4>
                <p style="margin:0;color:#52514e;">📍 {empresa['cidade']}/{empresa['uf']}</p>
                <p style="margin:0 0 0.75rem 0;color:#52514e;">⏱️ {empresa['carga_horaria_diaria']}h por dia + {empresa['intervalo_almoco_minutos']}min de almoço</p>
                {theme.saldo_banco_horas_html(banco['saldo'])}
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()
st.markdown(
    "Use o menu à esquerda para **bater o ponto do dia**, "
    "**cadastrar feriados municipais** ou **ver o dashboard** diário/mensal."
)
