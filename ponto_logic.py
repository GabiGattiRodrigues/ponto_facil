"""
ponto_logic.py — Regras de negócio do controle de ponto.

Regras (definidas pelo usuário):
  1. Saída prevista = entrada + carga horária diária da empresa.
  2. Tolerância de 5 minutos (para mais ou para menos) em torno da saída
     prevista: dentro dessa janela, não conta hora extra nem hora devida.
  3. Saída ANTES do previsto (além da tolerância):
       - COM justificativa -> não conta como hora devida.
       - SEM justificativa -> conta como hora devida (em minutos).
  4. Saída DEPOIS do previsto (além da tolerância) -> hora extra (em minutos).
  5. Horas extra e horas devidas são sempre computadas em MINUTOS.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

TOLERANCIA_MINUTOS = 5

STATUS_ABERTO = "aberto"                                   # só bateu entrada
STATUS_NORMAL = "normal"                                    # dentro da tolerância
STATUS_HORA_EXTRA = "hora_extra"                             # saiu depois do previsto
STATUS_HORA_DEVIDA = "hora_devida"                           # saiu antes, sem justificativa
STATUS_SAIDA_JUSTIFICADA = "saida_antecipada_justificada"    # saiu antes, com justificativa

STATUS_LABELS = {
    STATUS_ABERTO: "Aguardando saída",
    STATUS_NORMAL: "Normal",
    STATUS_HORA_EXTRA: "Hora extra",
    STATUS_HORA_DEVIDA: "Hora devida",
    STATUS_SAIDA_JUSTIFICADA: "Saída antecipada justificada",
}


def calcular_saida_prevista(entrada: time, carga_horaria_horas: float,
                             intervalo_almoco_minutos: int = 0) -> time:
    """Soma a carga horária diária (horas decimais, ex: 8.5 = 8h30) MAIS o
    intervalo de almoço (em minutos) à entrada.

    Exemplo: entrada 08:00, carga horária 8h, intervalo de almoço 60 min
    -> saída prevista 17:00 (8h trabalhadas + 1h de almoço, como prevê a
    CLT para jornadas acima de 6h).

    Usa uma data-âncora arbitrária só para poder somar timedelta e depois
    volta a extrair o horário. Não trata virada de dia (carga horária > 24h
    não faz sentido de qualquer forma).
    """
    ancora = datetime.combine(date(2000, 1, 1), entrada)
    minutos_totais = round(carga_horaria_horas * 60) + int(intervalo_almoco_minutos)
    resultado = ancora + timedelta(minutes=minutos_totais)
    return resultado.time()


def sugerir_intervalo_almoco_minutos(carga_horaria_horas: float) -> int:
    """Sugestão de intervalo obrigatório conforme a CLT (art. 71):
      - jornada > 6h: mínimo 1h (60 min) de intervalo;
      - jornada entre 4h e 6h: 15 min;
      - jornada até 4h: sem intervalo obrigatório.
    É só uma sugestão de partida — o valor pode ser ajustado livremente no
    cadastro da empresa, já que acordos/convenções podem mudar isso.
    """
    if carga_horaria_horas > 6:
        return 60
    elif carga_horaria_horas >= 4:
        return 15
    return 0


def _diferenca_em_minutos(previsto: time, real: time) -> int:
    """real - previsto, em minutos (positivo = saiu depois, negativo = saiu antes)."""
    ancora = date(2000, 1, 1)
    dt_previsto = datetime.combine(ancora, previsto)
    dt_real = datetime.combine(ancora, real)
    delta = dt_real - dt_previsto
    return round(delta.total_seconds() / 60)


@dataclass
class ResultadoPonto:
    status: str
    minutos_extra: int
    minutos_devidos: int
    diferenca_minutos: int  # real - previsto (pode ser negativo)


def avaliar_saida(saida_prevista: time, saida_real: time | None,
                   justificativa: str | None) -> ResultadoPonto:
    """Aplica as regras de negócio e devolve o status + minutos extra/devidos."""
    if saida_real is None:
        return ResultadoPonto(STATUS_ABERTO, 0, 0, 0)

    diff = _diferenca_em_minutos(saida_prevista, saida_real)
    justificativa = (justificativa or "").strip()

    if abs(diff) <= TOLERANCIA_MINUTOS:
        return ResultadoPonto(STATUS_NORMAL, 0, 0, diff)

    if diff > TOLERANCIA_MINUTOS:
        # saiu depois do previsto -> hora extra
        return ResultadoPonto(STATUS_HORA_EXTRA, diff, 0, diff)

    # diff < -TOLERANCIA_MINUTOS -> saiu antes do previsto
    if justificativa:
        return ResultadoPonto(STATUS_SAIDA_JUSTIFICADA, 0, 0, diff)
    else:
        return ResultadoPonto(STATUS_HORA_DEVIDA, 0, abs(diff), diff)


def formatar_minutos(minutos: int) -> str:
    """Formata minutos como 'Xh Ymin' (ex: 90 -> '1h 30min')."""
    if minutos == 0:
        return "0min"
    horas, resto = divmod(abs(minutos), 60)
    sinal = "-" if minutos < 0 else ""
    partes = []
    if horas:
        partes.append(f"{horas}h")
    if resto or not horas:
        partes.append(f"{resto}min")
    return sinal + " ".join(partes)


def eh_dia_util_sem_feriado(eh_fim_de_semana: bool, eh_feriado: bool) -> bool:
    """Dia útil = não é fim de semana nem feriado. Só nesses dias cobramos ponto."""
    return not eh_fim_de_semana and not eh_feriado
