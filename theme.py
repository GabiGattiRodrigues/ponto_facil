"""
theme.py — Paleta de cores e CSS customizado do Ponto Fácil.

Segue uma paleta azul (pedido do usuário) com cores de status reservadas
(nunca usadas para outra coisa) para não misturar "identidade" com "estado":
  - azul       -> marca / dados neutros / hora extra (crédito)
  - verde      -> "good" / em dia
  - amarelo    -> "warning" / atenção (ex: saída justificada)
  - vermelho   -> "critical" / hora devida, falta de registro
"""

import streamlit as st

import ponto_logic

# Paleta sequencial azul (100 = quase transparente -> 700 = escuro)
AZUL = {
    100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
    300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
    500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281",
    700: "#0d366b",
}

BRAND = AZUL[450]        # #2a78d6 — cor principal da marca
BRAND_DARK = AZUL[650]
BRAND_LIGHT = AZUL[100]

# Cores de status (fixas — nunca reaproveitadas para outra coisa)
STATUS = {
    "good": "#0ca30c",       # em dia / hora extra
    "warning": "#c98500",    # justificada / atenção (step mais escuro p/ contraste no texto)
    "critical": "#d03b3b",   # hora devida / falta de registro
    "neutral": "#52514e",    # normal, sem desvio relevante
}

INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
SURFACE = "#fcfcfb"
SURFACE_2 = "#eaf1fb"
GRIDLINE = "#e1e0d9"

STATUS_COLOR_BY_LABEL = {
    "aberto": INK_MUTED,
    "normal": STATUS["neutral"],
    "hora_extra": STATUS["good"],
    "hora_devida": STATUS["critical"],
    "saida_antecipada_justificada": STATUS["warning"],
}

STATUS_ICON_BY_LABEL = {
    "aberto": "⏳",
    "normal": "✅",
    "hora_extra": "🔵",
    "hora_devida": "🔴",
    "saida_antecipada_justificada": "🟡",
}

# Par divergente usado para "saldo" (banco de horas): crédito x débito.
# Mesmas cores usadas nos gráficos do dashboard (charts.py), para o app
# falar a mesma "língua visual" em todo lugar que mostra saldo.
SALDO_POSITIVO = AZUL[450]   # #2a78d6 — crédito (mais hora extra que devida)
SALDO_NEGATIVO = "#d03b3b"   # débito (mais hora devida que extra)


def saldo_banco_horas_html(minutos: int, titulo: str = "Banco de horas") -> str:
    """Card compacto mostrando o saldo acumulado (banco de horas) de uma empresa."""
    cor = SALDO_POSITIVO if minutos >= 0 else SALDO_NEGATIVO
    sinal = "+" if minutos > 0 else ""
    texto = ponto_logic.formatar_minutos(minutos)
    rotulo = "de crédito" if minutos > 0 else ("em dia" if minutos == 0 else "devendo")
    return (
        f'<div>'
        f'<span style="color:{INK_MUTED};font-size:0.8rem;text-transform:uppercase;'
        f'letter-spacing:0.03em;">{titulo}</span><br>'
        f'<span style="color:{cor};font-weight:800;font-size:1.6rem;">{sinal}{texto}</span> '
        f'<span style="color:{INK_MUTED};font-size:0.85rem;">{rotulo}</span>'
        f'</div>'
    )


def inject_css():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {SURFACE};
        }}
        section[data-testid="stSidebar"] {{
            background-color: {BRAND_DARK};
        }}
        section[data-testid="stSidebar"] * {{
            color: #ffffff !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {{
            color: {INK_PRIMARY} !important;
        }}
        h1, h2, h3 {{
            color: {BRAND_DARK};
        }}
        div.stButton > button, div.stFormSubmitButton > button {{
            background-color: {BRAND};
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
        }}
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            background-color: {BRAND_DARK};
            color: white;
        }}
        .ponto-card {{
            background-color: {SURFACE_2};
            border: 1px solid {GRIDLINE};
            border-radius: 12px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
        }}
        .ponto-status-pill {{
            display: inline-block;
            padding: 0.15rem 0.6rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_pill_html(status: str, label: str) -> str:
    cor = STATUS_COLOR_BY_LABEL.get(status, INK_MUTED)
    icone = STATUS_ICON_BY_LABEL.get(status, "")
    return f'<span class="ponto-status-pill" style="background-color:{cor};">{icone} {label}</span>'
