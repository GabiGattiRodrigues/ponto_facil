"""Tela: cadastro manual de feriados municipais.

Não existe uma base pública gratuita cobrindo feriados de todos os
municípios do Brasil, então esse cadastro é manual (feito uma vez por
cidade/empresa) — feriados nacionais e estaduais já são automáticos.
"""

from datetime import date

import streamlit as st

import db
import utils

st.title("📅 Feriados Municipais")
st.caption(
    "Feriados nacionais e estaduais já são detectados automaticamente. "
    "Aqui você cadastra feriados específicos do município (ex: aniversário "
    "da cidade, padroeiro/a) — é rapidinho e só precisa fazer uma vez."
)

labels, mapa_empresas = utils.empresas_como_opcoes()
if not labels:
    st.info("Cadastre uma empresa primeiro em **🏢 Cadastrar Empresa**.")
    st.stop()

label_escolhido = st.selectbox("Empresa", labels)
empresa = mapa_empresas[label_escolhido]

with st.form("form_feriado_municipal", clear_on_submit=True):
    col1, col2 = st.columns([1, 2])
    with col1:
        data_feriado = st.date_input("Data do feriado", value=date.today(), format="DD/MM/YYYY")
    with col2:
        descricao = st.text_input("Descrição", placeholder="Ex: Aniversário da cidade")
    recorrente = st.checkbox(
        "Repetir todo ano nesse dia/mês (recomendado)",
        value=True,
    )
    enviado = st.form_submit_button("Adicionar feriado municipal")

if enviado:
    if not descricao.strip():
        st.error("Informe uma descrição para o feriado.")
    else:
        db.adicionar_feriado_municipal(
            empresa["id"], data_feriado.isoformat(), descricao, recorrente
        )
        st.success(f"Feriado **{descricao}** adicionado para {empresa['nome']}.")

st.divider()
st.subheader(f"Feriados municipais de {empresa['nome']}")

feriados = db.listar_feriados_municipais(empresa["id"])
if not feriados:
    st.info("Nenhum feriado municipal cadastrado para essa empresa ainda.")
else:
    for f in feriados:
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        d = date.fromisoformat(f["data"])
        c1.write(d.strftime("%d/%m/%Y"))
        c2.write(f["descricao"])
        c3.write("🔁 Todo ano" if f["recorrente_anual"] else "Só esse ano")
        if c4.button("🗑️ Remover", key=f"del_feriado_{f['id']}"):
            db.excluir_feriado_municipal(f["id"])
            st.rerun()
