"""
anexos.py — Helpers para comprovantes (ex: foto de atestado médico)
anexados a um registro de ponto.

Os arquivos ficam guardados DENTRO do banco de dados (coluna anexo_dados,
BLOB no SQLite / BYTEA no Postgres) junto com o resto do registro do dia —
não soltos em disco. Isso é importante porque, quando o app está hospedado
(ex: Streamlit Community Cloud), o disco do servidor não é garantidamente
persistente entre reinicializações; o banco de dados (local ou Supabase) é
a única coisa que precisa sobreviver, e agora o anexo viaja junto com ele.
"""

from pathlib import Path

EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
TIPOS_ACEITOS = ["png", "jpg", "jpeg", "webp", "pdf"]


def eh_imagem(nome_arquivo: str) -> bool:
    return Path(nome_arquivo).suffix.lower() in EXTENSOES_IMAGEM
