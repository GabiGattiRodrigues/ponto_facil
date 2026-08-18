"""Tela: cadastro de empresas."""

from datetime import date

import streamlit as st

import db
import holidays_br
import ponto_logic

st.title("🏢 Cadastrar Empresa")
st.caption(
    "Ao cadastrar, o app já identifica automaticamente os feriados "
    "nacionais e do estado escolhido — e os finais de semana."
)

with st.form("form_cadastro_empresa", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome da empresa *")
        cidade = st.text_input("Cidade *")
    with col2:
        uf = st.selectbox(
            "Estado (UF) *",
            options=holidays_br.UFS_BRASIL,
            format_func=lambda sigla: f"{sigla} — {holidays_br.NOMES_UF[sigla]}",
        )
        carga_horaria = st.number_input(
            "Carga horária diária TRABALHADA (horas) *",
            min_value=1.0, max_value=12.0, value=8.0, step=0.5,
            help="Ex: 8.0 para 8 horas, 8.5 para 8h30, 6.0 para 6 horas. "
                 "Não inclui o intervalo de almoço, que é somado à parte abaixo.",
        )

    intervalo_sugerido = ponto_logic.sugerir_intervalo_almoco_minutos(carga_horaria)
    intervalo_almoco = st.number_input(
        "Intervalo de almoço (minutos)",
        min_value=0, max_value=180, value=intervalo_sugerido, step=5,
        help=(
            "Pela CLT (art. 71): jornadas acima de 6h têm direito a no mínimo "
            "1h (60 min) de intervalo; entre 4h e 6h, 15 min; até 4h, não é "
            "obrigatório. Ajuste se a sua empresa tiver uma regra diferente. "
            "Esse tempo é somado à carga horária para calcular o horário de "
            "saída previsto (ex: entrada 08:00 + 8h de trabalho + 1h de "
            "almoço = saída prevista às 17:00)."
        ),
    )
    enviado = st.form_submit_button("Cadastrar empresa")

if enviado:
    if not nome.strip() or not cidade.strip():
        st.error("Preencha nome e cidade da empresa.")
    else:
        empresa_id = db.criar_empresa(nome, cidade, uf, carga_horaria, intervalo_almoco)
        st.success(
            f"Empresa **{nome}** cadastrada! Já pode ir em "
            "**🕒 Bater Ponto** para registrar o dia."
        )
        st.balloons()

st.divider()

st.subheader("Empresas cadastradas")
empresas = db.listar_empresas()
if not empresas:
    st.info("Nenhuma empresa cadastrada ainda.")
else:
    for empresa in empresas:
        with st.expander(f"{empresa['nome']} — {empresa['cidade']}/{empresa['uf']}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(f"**Carga horária:** {empresa['carga_horaria_diaria']}h trabalhadas")
                st.write(f"**Intervalo de almoço:** {empresa['intervalo_almoco_minutos']} min")
            with c2:
                st.write(f"**Cadastrada em:** {empresa['criado_em'][:10]}")
            with c3:
                if st.button("🗑️ Excluir", key=f"excluir_{empresa['id']}"):
                    db.excluir_empresa(empresa["id"])
                    st.warning(f"Empresa {empresa['nome']} excluída (junto com pontos e feriados).")
                    st.rerun()

            # Pré-visualização dos feriados nacionais/estaduais do ano atual
            ano_atual = date.today().year
            feriados = holidays_br.feriados_nacionais_estaduais(empresa["uf"], ano_atual)
            st.write(f"**Feriados nacionais/estaduais detectados automaticamente em {ano_atual}:**")
            for d in sorted(feriados):
                st.caption(f"📅 {d.strftime('%d/%m/%Y')} — {feriados[d]}")
