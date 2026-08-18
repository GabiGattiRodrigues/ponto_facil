"""Tela: dashboard de acompanhamento diário e mensal."""

from datetime import date, timedelta
import calendar

import pandas as pd
import streamlit as st

import anexos
import charts
import db
import holidays_br
import ponto_logic
import theme
import utils

st.title("📊 Dashboard")

labels, mapa_empresas = utils.empresas_como_opcoes()
if not labels:
    st.info("Cadastre uma empresa primeiro em **🏢 Cadastrar Empresa**.")
    st.stop()

label_escolhido = st.selectbox("Empresa", labels)
empresa = mapa_empresas[label_escolhido]

# --- Banco de horas acumulado (todo o histórico, não só o período abaixo) ---
banco = db.banco_de_horas(empresa["id"])
st.markdown(
    f"""
    <div class="ponto-card" style="max-width: 420px;">
        {theme.saldo_banco_horas_html(banco['saldo'], titulo="🏦 Banco de horas acumulado")}
        <p style="margin:0.5rem 0 0 0;color:#898781;font-size:0.85rem;">
            Extra: {ponto_logic.formatar_minutos(banco['total_extra'])} ·
            Devida: {ponto_logic.formatar_minutos(banco['total_devida'])}
            &nbsp;—&nbsp;considera todo o histórico da empresa.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

aba_diaria, aba_mensal = st.tabs(["📅 Diário", "🗓️ Mensal"])


def _linha_para_dict(row):
    return {
        "Data": date.fromisoformat(row["data"]),
        "Dia": utils.nome_dia_semana(date.fromisoformat(row["data"])),
        "Entrada": row["entrada"],
        "Saída prevista": row["saida_prevista"],
        "Saída real": row["saida_real"] or "—",
        "Status": f"{theme.STATUS_ICON_BY_LABEL.get(row['status'], '')} {ponto_logic.STATUS_LABELS.get(row['status'], row['status'])}",
        "Hora extra": row["minutos_extra"],
        "Hora devida": row["minutos_devidos"],
        "Justificativa": row["justificativa"] or "—",
        "Anexo": "📎" if row["anexo_dados"] else "—",
        "Feriado": row["feriado_descricao"] or ("Fim de semana" if row["eh_fim_de_semana"] else "—"),
    }


def _mostrar_visualizador_anexos(registros, key_prefix):
    """Mostra um seletor + preview dos comprovantes anexados no período."""
    registros_com_anexo = [r for r in registros if r["anexo_dados"]]
    if not registros_com_anexo:
        return
    st.subheader("📎 Comprovantes anexados")
    opcoes = {
        f"{date.fromisoformat(r['data']).strftime('%d/%m/%Y')} — {r['justificativa'] or 'sem justificativa'}": r
        for r in registros_com_anexo
    }
    escolha = st.selectbox("Ver comprovante do dia:", list(opcoes.keys()), key=f"{key_prefix}_anexo_sel")
    registro = opcoes[escolha]
    dados = bytes(registro["anexo_dados"])
    nome = registro["anexo_nome"] or "comprovante"
    if anexos.eh_imagem(nome):
        st.image(dados, width=320)
    else:
        st.download_button(
            "⬇️ Baixar comprovante (PDF)", dados, file_name=nome,
            key=f"{key_prefix}_download_{registro['id']}",
        )


# =============================================================================
# ABA DIÁRIA
# =============================================================================
with aba_diaria:
    col_a, col_b = st.columns(2)
    with col_a:
        data_inicio = st.date_input("De", value=date.today() - timedelta(days=30), key="d_ini", format="DD/MM/YYYY")
    with col_b:
        data_fim = st.date_input("Até", value=date.today(), key="d_fim", format="DD/MM/YYYY")

    registros = db.listar_pontos(empresa["id"], data_inicio.isoformat(), data_fim.isoformat())

    dias_faltando = [
        d for d in utils.dias_uteis_sem_registro(empresa, janela_dias=(date.today() - data_inicio).days + 1)
        if data_inicio <= d <= data_fim
    ]

    total_extra = sum(r["minutos_extra"] for r in registros)
    total_devida = sum(r["minutos_devidos"] for r in registros)
    saldo = total_extra - total_devida

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Dias registrados", len(registros))
    k2.metric("Dias sem registro", len(dias_faltando))
    k3.metric("Hora extra total", ponto_logic.formatar_minutos(total_extra))
    k4.metric("Hora devida total", ponto_logic.formatar_minutos(total_devida))
    k5.metric("Saldo", ponto_logic.formatar_minutos(saldo))

    if dias_faltando:
        st.warning(
            "Dias úteis sem ponto no período: "
            + ", ".join(utils.formatar_data_br(d) for d in dias_faltando)
        )

    if registros:
        st.plotly_chart(
            charts.grafico_saldo_por_dia(
                dias_labels=[date.fromisoformat(r["data"]).strftime("%d/%m") for r in registros],
                saldos_minutos=[r["minutos_extra"] - r["minutos_devidos"] for r in registros],
                extras_minutos=[r["minutos_extra"] for r in registros],
                devidas_minutos=[r["minutos_devidos"] for r in registros],
            ),
            use_container_width=True,
        )

        df = pd.DataFrame([_linha_para_dict(r) for r in registros])
        st.dataframe(df, use_container_width=True, hide_index=True)

        _mostrar_visualizador_anexos(registros, key_prefix="diario")
    else:
        st.info("Nenhum ponto registrado nesse período ainda.")

# =============================================================================
# ABA MENSAL
# =============================================================================
with aba_mensal:
    hoje = date.today()
    col_m, col_y = st.columns(2)
    with col_m:
        mes = st.selectbox(
            "Mês", options=list(range(1, 13)), index=hoje.month - 1,
            format_func=lambda m: utils.MESES_PT[m],
        )
    with col_y:
        ano = st.selectbox("Ano", options=list(range(hoje.year - 3, hoje.year + 1)), index=3)

    primeiro_dia = date(ano, mes, 1)
    ultimo_dia_num = calendar.monthrange(ano, mes)[1]
    ultimo_dia = date(ano, mes, ultimo_dia_num)

    registros_mes = db.listar_pontos(empresa["id"], primeiro_dia.isoformat(), ultimo_dia.isoformat())

    # dias úteis sem registro no mês (só até hoje, não faz sentido cobrar o futuro)
    fim_verificacao = min(ultimo_dia, hoje)
    dias_faltando_mes = []
    if primeiro_dia <= fim_verificacao:
        d = primeiro_dia
        while d <= fim_verificacao:
            info = holidays_br.verificar_dia(empresa["id"], empresa["uf"], d)
            if ponto_logic.eh_dia_util_sem_feriado(info["eh_fim_de_semana"], info["eh_feriado"]):
                if db.obter_ponto(empresa["id"], d.isoformat()) is None:
                    dias_faltando_mes.append(d)
            d += timedelta(days=1)

    total_extra_mes = sum(r["minutos_extra"] for r in registros_mes)
    total_devida_mes = sum(r["minutos_devidos"] for r in registros_mes)
    saldo_mes = total_extra_mes - total_devida_mes

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Dias registrados", len(registros_mes))
    k2.metric("Dias sem registro", len(dias_faltando_mes))
    k3.metric("Hora extra total", ponto_logic.formatar_minutos(total_extra_mes))
    k4.metric("Hora devida total", ponto_logic.formatar_minutos(total_devida_mes))
    k5.metric("Saldo do mês", ponto_logic.formatar_minutos(saldo_mes))

    if registros_mes:
        st.plotly_chart(
            charts.grafico_saldo_por_dia(
                dias_labels=[date.fromisoformat(r["data"]).strftime("%d/%m") for r in registros_mes],
                saldos_minutos=[r["minutos_extra"] - r["minutos_devidos"] for r in registros_mes],
                extras_minutos=[r["minutos_extra"] for r in registros_mes],
                devidas_minutos=[r["minutos_devidos"] for r in registros_mes],
                titulo=f"Saldo por dia — {utils.MESES_PT[mes]}/{ano}",
            ),
            use_container_width=True,
        )
        _mostrar_visualizador_anexos(registros_mes, key_prefix="mensal")
    else:
        st.info("Nenhum ponto registrado nesse mês ainda.")

    st.divider()
    st.subheader("Tendência dos últimos 6 meses")

    meses_labels = []
    saldos_tendencia = []
    ref = date(ano, mes, 1)
    referencias = []
    for i in range(5, -1, -1):
        m = ref.month - i
        a = ref.year
        while m <= 0:
            m += 12
            a -= 1
        referencias.append((a, m))

    for a, m in referencias:
        pd_ini = date(a, m, 1)
        pd_fim = date(a, m, calendar.monthrange(a, m)[1])
        regs = db.listar_pontos(empresa["id"], pd_ini.isoformat(), pd_fim.isoformat())
        s = sum(r["minutos_extra"] for r in regs) - sum(r["minutos_devidos"] for r in regs)
        meses_labels.append(f"{utils.MESES_PT[m][:3]}/{a}")
        saldos_tendencia.append(s)

    st.plotly_chart(
        charts.grafico_saldo_mensal(meses_labels, saldos_tendencia),
        use_container_width=True,
    )
