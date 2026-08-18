"""
holidays_br.py — Feriados nacionais e estaduais do Brasil (automático) +
integração com feriados municipais cadastrados manualmente pelo usuário.

Feriados nacionais e estaduais: usamos a biblioteca `holidays`
(https://pypi.org/project/holidays/), que já cobre certinho o calendário
oficial brasileiro por estado (UF).

Feriados municipais: não existe uma base pública gratuita e completa para
os ~5.570 municípios do Brasil, então esses são cadastrados manualmente
(ver página "Feriados Municipais" no app) e ficam salvos por empresa.
"""

from datetime import date
from functools import lru_cache

import holidays

import db

UFS_BRASIL = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
]

NOMES_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal",
    "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí",
    "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}


@lru_cache(maxsize=64)
def _feriados_nacionais_estaduais(uf: str, ano: int) -> dict:
    """Retorna {date: nome_do_feriado} para feriados nacionais + do estado (uf) em um ano."""
    return dict(holidays.country_holidays("BR", subdiv=uf, years=[ano]))


def feriados_nacionais_estaduais(uf: str, ano: int) -> dict:
    """Wrapper público (sem cache exposto para evitar mutação do dict cacheado)."""
    return dict(_feriados_nacionais_estaduais(uf, ano))


def feriados_municipais_por_ano(empresa_id: int, ano: int) -> dict:
    """Converte os feriados municipais cadastrados manualmente para o ano pedido.

    Feriados marcados como 'recorrente_anual' repetem todo ano no mesmo dia/mês.
    """
    resultado = {}
    for row in db.listar_feriados_municipais(empresa_id):
        d = date.fromisoformat(row["data"])
        if row["recorrente_anual"]:
            try:
                d_ano = d.replace(year=ano)
            except ValueError:
                # 29 de fevereiro em ano não bissexto, por exemplo
                continue
        else:
            if d.year != ano:
                continue
            d_ano = d
        resultado[d_ano] = row["descricao"]
    return resultado


def verificar_dia(empresa_id: int, uf: str, dia: date) -> dict:
    """Classifica um dia para uma empresa: fim de semana? feriado? qual?

    Retorna dict com:
      - eh_fim_de_semana (bool)
      - eh_feriado (bool)
      - feriado_descricao (str | None)
      - tipo_feriado ('nacional_estadual' | 'municipal' | None)
    """
    eh_fim_de_semana = dia.weekday() >= 5  # 5=sábado, 6=domingo

    nac_est = feriados_nacionais_estaduais(uf, dia.year)
    if dia in nac_est:
        return {
            "eh_fim_de_semana": eh_fim_de_semana,
            "eh_feriado": True,
            "feriado_descricao": nac_est[dia],
            "tipo_feriado": "nacional_estadual",
        }

    municipais = feriados_municipais_por_ano(empresa_id, dia.year)
    if dia in municipais:
        return {
            "eh_fim_de_semana": eh_fim_de_semana,
            "eh_feriado": True,
            "feriado_descricao": municipais[dia],
            "tipo_feriado": "municipal",
        }

    return {
        "eh_fim_de_semana": eh_fim_de_semana,
        "eh_feriado": False,
        "feriado_descricao": None,
        "tipo_feriado": None,
    }
