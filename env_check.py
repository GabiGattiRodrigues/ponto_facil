"""
env_check.py — Verifica se o app está rodando dentro de um ambiente virtual
(venv). Isso evita misturar os pacotes deste projeto com pacotes Python
instalados globalmente na sua máquina (o que costuma causar conflito de
versões com o tempo).
"""

import sys


def rodando_em_venv() -> bool:
    """True se o interpretador Python atual for de um ambiente virtual."""
    return (
        hasattr(sys, "real_prefix")  # virtualenv (biblioteca mais antiga)
        or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)  # venv nativo do Python 3
    )
