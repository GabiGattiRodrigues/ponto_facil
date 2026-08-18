"""
utils.py — Funções auxiliares compartilhadas entre as páginas do app.
"""

from datetime import date, timedelta

import db
import holidays_br
import ponto_logic

DIAS_SEMANA_PT = {
    0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
    3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo",
}

MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio",
    6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro",
    11: "Novembro", 12: "Dezembro",
}


def nome_dia_semana(d: date) -> str:
    return DIAS_SEMANA_PT[d.weekday()]


def formatar_data_br(d: date) -> str:
    return f"{d.strftime('%d/%m/%Y')} ({nome_dia_semana(d)})"


def dias_uteis_sem_registro(empresa, janela_dias: int = 14) -> list[date]:
    """Retorna dias úteis (não fim de semana, não feriado) dos últimos `janela_dias`
    dias em que a empresa não tem ponto registrado (e a empresa já existia)."""
    hoje = date.today()
    criado_em = date.fromisoformat(empresa["criado_em"][:10])
    inicio = max(criado_em, hoje - timedelta(days=janela_dias))

    faltando = []
    d = inicio
    while d <= hoje:
        info = holidays_br.verificar_dia(empresa["id"], empresa["uf"], d)
        if ponto_logic.eh_dia_util_sem_feriado(info["eh_fim_de_semana"], info["eh_feriado"]):
            ponto = db.obter_ponto(empresa["id"], d.isoformat())
            if ponto is None:
                faltando.append(d)
        d += timedelta(days=1)
    return faltando


def empresas_como_opcoes():
    """Retorna (lista_labels, dict label->empresa) para usar em selectbox."""
    empresas = db.listar_empresas()
    labels = [f"{e['nome']} — {e['cidade']}/{e['uf']}" for e in empresas]
    mapa = {label: empresa for label, empresa in zip(labels, empresas)}
    return labels, mapa
