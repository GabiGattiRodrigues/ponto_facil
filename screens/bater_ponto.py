"""Tela: bater o ponto (entrada / saída) de um dia para uma empresa."""

from datetime import date, time

import streamlit as st

import anexos
import db
import holidays_br
import ponto_logic
import utils

st.title("🕒 Bater Ponto")

labels, mapa_empresas = utils.empresas_como_opcoes()
if not labels:
    st.info("Cadastre uma empresa primeiro em **🏢 Cadastrar Empresa**.")
    st.stop()

col_sel1, col_sel2 = st.columns([2, 1])
with col_sel1:
    label_escolhido = st.selectbox("Empresa", labels)
    empresa = mapa_empresas[label_escolhido]
with col_sel2:
    data_selecionada = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")

# --- Classificação do dia (fim de semana / feriado) -------------------------
info_dia = holidays_br.verificar_dia(empresa["id"], empresa["uf"], data_selecionada)

if info_dia["eh_fim_de_semana"]:
    st.info(f"📅 {utils.formatar_data_br(data_selecionada)} é final de semana.")
elif info_dia["eh_feriado"]:
    st.info(f"📅 {utils.formatar_data_br(data_selecionada)} é feriado: **{info_dia['feriado_descricao']}**.")
else:
    st.caption(f"📅 {utils.formatar_data_br(data_selecionada)} — dia útil.")

st.divider()

ponto_existente = db.obter_ponto(empresa["id"], data_selecionada.isoformat())

col1, col2 = st.columns(2)
with col1:
    entrada_default = (
        time.fromisoformat(ponto_existente["entrada"]) if ponto_existente else time(8, 0)
    )
    entrada = st.time_input("Horário de entrada", value=entrada_default, step=300)

saida_prevista = ponto_logic.calcular_saida_prevista(
    entrada, empresa["carga_horaria_diaria"], empresa["intervalo_almoco_minutos"]
)

with col2:
    st.text_input(
        "Horário de saída previsto (calculado automaticamente)",
        value=saida_prevista.strftime("%H:%M"),
        disabled=True,
        help=(
            f"Entrada + {empresa['carga_horaria_diaria']}h trabalhadas + "
            f"{empresa['intervalo_almoco_minutos']}min de almoço."
        ),
    )

st.write("")
bateu_saida = st.checkbox(
    "Já bati a saída hoje",
    value=bool(ponto_existente and ponto_existente["saida_real"]),
)

saida_real = None
justificativa = None
resultado = None

# Anexo já salvo (se estiver editando um dia que já tem um comprovante)
anexo_dados_atual = bytes(ponto_existente["anexo_dados"]) if (ponto_existente and ponto_existente["anexo_dados"]) else None
anexo_nome_atual = ponto_existente["anexo_nome"] if ponto_existente else None
remover_anexo_atual = False
novo_anexo = None

if bateu_saida:
    saida_real_default = (
        time.fromisoformat(ponto_existente["saida_real"])
        if ponto_existente and ponto_existente["saida_real"]
        else saida_prevista
    )
    saida_real = st.time_input("Horário de saída real", value=saida_real_default, step=300)

    resultado = ponto_logic.avaliar_saida(saida_prevista, saida_real, None)

    if resultado.status == ponto_logic.STATUS_HORA_EXTRA:
        st.success(
            f"🔵 Saída depois do previsto: **hora extra de {ponto_logic.formatar_minutos(resultado.minutos_extra)}**."
        )
    elif resultado.diferenca_minutos < -ponto_logic.TOLERANCIA_MINUTOS:
        st.warning(
            "🟡 Você está saindo antes do horário previsto. "
            "Se tiver um motivo (ex: consulta médica), informe abaixo para não contar como hora devida."
        )
        justificativa_default = ponto_existente["justificativa"] if ponto_existente else ""
        justificativa = st.text_input(
            "Justificativa (opcional)",
            value=justificativa_default or "",
            placeholder="Ex: consulta médica, dispensa antecipada combinada com o gestor...",
        )

        st.write("")
        if anexo_dados_atual:
            st.caption("📎 Comprovante anexado atualmente:")
            if anexos.eh_imagem(anexo_nome_atual or ""):
                st.image(anexo_dados_atual, width=220)
            else:
                st.write(f"📄 {anexo_nome_atual}")
            remover_anexo_atual = st.checkbox("Remover comprovante atual", value=False)

        novo_anexo = st.file_uploader(
            "Anexar comprovante (opcional) — ex: foto do atestado médico",
            type=anexos.TIPOS_ACEITOS,
            help="Aceita imagens (png/jpg/webp) ou PDF. Fica salvo dentro do banco de dados, junto com o registro do dia.",
        )
    else:
        st.success("✅ Saída dentro do horário previsto (tolerância de 5 minutos).")

    # reavalia com a justificativa (se houver) para status final
    resultado = ponto_logic.avaliar_saida(saida_prevista, saida_real, justificativa)

st.divider()

if st.button("💾 Salvar ponto do dia", type="primary"):
    # Resolve o anexo final: mantém o atual, a menos que peçam pra remover
    # ou enviem um novo arquivo (que substitui o anterior).
    anexo_dados_final = anexo_dados_atual
    anexo_nome_final = anexo_nome_atual
    if remover_anexo_atual:
        anexo_dados_final = None
        anexo_nome_final = None
    if novo_anexo is not None:
        anexo_dados_final = novo_anexo.getvalue()
        anexo_nome_final = novo_anexo.name

    if resultado is None:
        # ainda não bateu saída -> registra só a entrada, status "aberto"
        db.salvar_ponto(
            empresa_id=empresa["id"],
            data=data_selecionada.isoformat(),
            entrada=entrada.strftime("%H:%M"),
            saida_prevista=saida_prevista.strftime("%H:%M"),
            saida_real=None,
            justificativa=None,
            status=ponto_logic.STATUS_ABERTO,
            minutos_extra=0,
            minutos_devidos=0,
            eh_fim_de_semana=info_dia["eh_fim_de_semana"],
            eh_feriado=info_dia["eh_feriado"],
            feriado_descricao=info_dia["feriado_descricao"],
            anexo_dados=anexo_dados_final,
            anexo_nome=anexo_nome_final,
        )
    else:
        db.salvar_ponto(
            empresa_id=empresa["id"],
            data=data_selecionada.isoformat(),
            entrada=entrada.strftime("%H:%M"),
            saida_prevista=saida_prevista.strftime("%H:%M"),
            saida_real=saida_real.strftime("%H:%M") if saida_real else None,
            justificativa=justificativa or None,
            status=resultado.status,
            minutos_extra=resultado.minutos_extra,
            minutos_devidos=resultado.minutos_devidos,
            eh_fim_de_semana=info_dia["eh_fim_de_semana"],
            eh_feriado=info_dia["eh_feriado"],
            feriado_descricao=info_dia["feriado_descricao"],
            anexo_dados=anexo_dados_final,
            anexo_nome=anexo_nome_final,
        )
    st.success("Ponto salvo com sucesso!")
    st.rerun()
