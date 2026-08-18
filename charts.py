"""
charts.py — Gráficos do dashboard (Plotly), seguindo a paleta azul do app.

Regra de cor usada aqui: o "saldo" do dia/mês (hora extra − hora devida, em
minutos) é uma medida com polaridade (positiva = crédito, negativa = débito),
então usamos o par divergente azul (crédito) ↔ vermelho (débito) com um
cinza neutro para zero — nunca um arco-íris, sempre um eixo só.
"""

import plotly.graph_objects as go

AZUL_POSITIVO = "#2a78d6"
VERMELHO_NEGATIVO = "#d03b3b"
CINZA_NEUTRO = "#c3c2b7"
GRIDLINE = "#e1e0d9"
INK_SECONDARY = "#52514e"

LAYOUT_BASE = dict(
    plot_bgcolor="#fcfcfb",
    paper_bgcolor="#fcfcfb",
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK_SECONDARY),
    margin=dict(l=10, r=10, t=40, b=10),
    hoverlabel=dict(bgcolor="white", font_size=13),
)


def grafico_saldo_por_dia(dias_labels, saldos_minutos, extras_minutos, devidas_minutos, titulo="Saldo por dia (minutos)"):
    """Gráfico de barras divergente: azul = crédito (hora extra), vermelho = débito (hora devida)."""
    cores = [AZUL_POSITIVO if s >= 0 else VERMELHO_NEGATIVO for s in saldos_minutos]

    hover = [
        f"Hora extra: {e} min<br>Hora devida: {d} min<br>Saldo: {s} min"
        for e, d, s in zip(extras_minutos, devidas_minutos, saldos_minutos)
    ]

    fig = go.Figure(
        go.Bar(
            x=dias_labels,
            y=saldos_minutos,
            marker_color=cores,
            marker_line_width=0,
            hovertext=hover,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title=titulo,
        yaxis_title="minutos",
        xaxis=dict(showgrid=False, tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor=GRIDLINE, zeroline=True, zerolinecolor="#898781", zerolinewidth=1.5),
        showlegend=False,
        **LAYOUT_BASE,
    )
    return fig


def grafico_saldo_mensal(meses_labels, saldos_minutos, titulo="Saldo por mês (minutos)"):
    cores = [AZUL_POSITIVO if s >= 0 else VERMELHO_NEGATIVO for s in saldos_minutos]
    fig = go.Figure(
        go.Bar(
            x=meses_labels,
            y=saldos_minutos,
            marker_color=cores,
            marker_line_width=0,
            hovertemplate="%{x}<br>Saldo: %{y} min<extra></extra>",
        )
    )
    fig.update_layout(
        title=titulo,
        yaxis_title="minutos",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRIDLINE, zeroline=True, zerolinecolor="#898781", zerolinewidth=1.5),
        showlegend=False,
        **LAYOUT_BASE,
    )
    return fig
