"""
db.py — Camada de acesso ao banco de dados do Ponto Fácil.

Funciona em dois modos, escolhidos automaticamente:

  - MODO LOCAL (padrão): usa um arquivo SQLite (data/ponto.db). É o que
    acontece quando você roda o app no seu computador via Cursor/venv, sem
    nenhuma configuração extra — bom pra simular e testar.

  - MODO NUVEM: usa um banco Postgres externo (ex: Supabase), quando existe
    uma connection string configurada em st.secrets["postgres"]["url"] (no
    Streamlit Community Cloud) ou na variável de ambiente DATABASE_URL
    (usado também pelo script de notificação, que roda fora do Streamlit).
    Isso é necessário para hospedar o app num site: o disco de serviços
    como o Streamlit Community Cloud NÃO é garantidamente persistente —
    arquivos locais (como um .db do SQLite) podem ser perdidos quando o
    app reinicia. Um banco externo resolve isso.

O resto do código do app (telas, lógica de negócio) não precisa saber qual
modo está ativo — chama sempre as mesmas funções deste módulo.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

try:
    import streamlit as st
except ImportError:  # o script de notificação roda fora do Streamlit
    st = None

DB_PATH = Path(__file__).parent / "data" / "ponto.db"


def _obter_url_postgres() -> str | None:
    if st is not None:
        try:
            return st.secrets["postgres"]["url"]
        except Exception:
            pass
    return os.environ.get("DATABASE_URL") or None


USANDO_POSTGRES = bool(_obter_url_postgres())

if USANDO_POSTGRES:
    import psycopg2
    import psycopg2.extras


def _traduzir_sql(sql: str) -> str:
    """SQLite usa '?' como placeholder, Postgres usa '%s'. Escrevemos o SQL
    sempre com '?' e traduzimos aqui quando estamos em modo Postgres."""
    return sql.replace("?", "%s") if USANDO_POSTGRES else sql


class _ConexaoPostgres:
    """Envelope fino em volta da conexão psycopg2 para que o resto do
    código possa chamar .execute(...)/.executescript(...) igualzinho ao
    jeito que o sqlite3.Connection funciona — assim as funções abaixo não
    precisam se importar com qual banco está por trás."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_traduzir_sql(sql), params)
        return cur

    def executescript(self, sql):
        cur = self._conn.cursor()
        cur.execute(sql)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


@contextmanager
def get_conn():
    """Abre uma conexão (SQLite ou Postgres, dependendo do modo), fecha ao sair."""
    if USANDO_POSTGRES:
        conn = _ConexaoPostgres(psycopg2.connect(_obter_url_postgres()))
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


_SCHEMA_SQLITE = """
    CREATE TABLE IF NOT EXISTS empresas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cidade TEXT NOT NULL,
        uf TEXT NOT NULL,
        carga_horaria_diaria REAL NOT NULL,
        intervalo_almoco_minutos INTEGER NOT NULL DEFAULT 60,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS feriados_municipais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
        data TEXT NOT NULL,
        descricao TEXT NOT NULL,
        recorrente_anual INTEGER NOT NULL DEFAULT 1,
        UNIQUE(empresa_id, data)
    );

    CREATE TABLE IF NOT EXISTS pontos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
        data TEXT NOT NULL,
        entrada TEXT NOT NULL,
        saida_prevista TEXT NOT NULL,
        saida_real TEXT,
        justificativa TEXT,
        anexo_dados BLOB,
        anexo_nome TEXT,
        status TEXT NOT NULL DEFAULT 'aberto',
        minutos_extra INTEGER NOT NULL DEFAULT 0,
        minutos_devidos INTEGER NOT NULL DEFAULT 0,
        eh_fim_de_semana INTEGER NOT NULL DEFAULT 0,
        eh_feriado INTEGER NOT NULL DEFAULT 0,
        feriado_descricao TEXT,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(empresa_id, data)
    );

    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    );
"""

_SCHEMA_POSTGRES = """
    CREATE TABLE IF NOT EXISTS empresas (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        cidade TEXT NOT NULL,
        uf TEXT NOT NULL,
        carga_horaria_diaria REAL NOT NULL,
        intervalo_almoco_minutos INTEGER NOT NULL DEFAULT 60,
        criado_em TEXT NOT NULL DEFAULT to_char(now(), 'YYYY-MM-DD HH24:MI:SS')
    );

    CREATE TABLE IF NOT EXISTS feriados_municipais (
        id SERIAL PRIMARY KEY,
        empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
        data TEXT NOT NULL,
        descricao TEXT NOT NULL,
        recorrente_anual INTEGER NOT NULL DEFAULT 1,
        UNIQUE(empresa_id, data)
    );

    CREATE TABLE IF NOT EXISTS pontos (
        id SERIAL PRIMARY KEY,
        empresa_id INTEGER NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
        data TEXT NOT NULL,
        entrada TEXT NOT NULL,
        saida_prevista TEXT NOT NULL,
        saida_real TEXT,
        justificativa TEXT,
        anexo_dados BYTEA,
        anexo_nome TEXT,
        status TEXT NOT NULL DEFAULT 'aberto',
        minutos_extra INTEGER NOT NULL DEFAULT 0,
        minutos_devidos INTEGER NOT NULL DEFAULT 0,
        eh_fim_de_semana INTEGER NOT NULL DEFAULT 0,
        eh_feriado INTEGER NOT NULL DEFAULT 0,
        feriado_descricao TEXT,
        criado_em TEXT NOT NULL DEFAULT to_char(now(), 'YYYY-MM-DD HH24:MI:SS'),
        UNIQUE(empresa_id, data)
    );

    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    );
"""


def init_db():
    """Cria as tabelas do banco caso ainda não existam. Chamar no início do app."""
    with get_conn() as conn:
        conn.executescript(_SCHEMA_POSTGRES if USANDO_POSTGRES else _SCHEMA_SQLITE)
        _migrar_colunas_antigas(conn)


def _colunas_existentes(conn, tabela: str) -> set[str]:
    if USANDO_POSTGRES:
        linhas = conn.execute(
            "SELECT column_name AS name FROM information_schema.columns WHERE table_name = ?",
            (tabela,),
        ).fetchall()
    else:
        linhas = conn.execute(f"PRAGMA table_info({tabela})").fetchall()
    return {row["name"] for row in linhas}


def _migrar_colunas_antigas(conn):
    """Adiciona colunas novas em bancos criados por versões anteriores do app
    (nem SQLite nem Postgres têm 'ADD COLUMN IF NOT EXISTS' universal, então
    checamos manualmente)."""
    colunas_empresas = _colunas_existentes(conn, "empresas")
    if "intervalo_almoco_minutos" not in colunas_empresas:
        conn.execute(
            "ALTER TABLE empresas ADD COLUMN intervalo_almoco_minutos INTEGER NOT NULL DEFAULT 60"
        )

    colunas_pontos = _colunas_existentes(conn, "pontos")
    if "anexo_dados" not in colunas_pontos:
        tipo_blob = "BYTEA" if USANDO_POSTGRES else "BLOB"
        conn.execute(f"ALTER TABLE pontos ADD COLUMN anexo_dados {tipo_blob}")
    if "anexo_nome" not in colunas_pontos:
        conn.execute("ALTER TABLE pontos ADD COLUMN anexo_nome TEXT")
    if "anexo_path" in colunas_pontos:
        # coluna de uma versão antiga (guardava caminho em disco); não é mais
        # usada, mas deixamos ela existir sem problema (não apagamos dados).
        pass


# ---------------------------------------------------------------------------
# Empresas
# ---------------------------------------------------------------------------

def criar_empresa(nome: str, cidade: str, uf: str, carga_horaria_diaria: float,
                   intervalo_almoco_minutos: int = 60) -> int:
    with get_conn() as conn:
        if USANDO_POSTGRES:
            cur = conn.execute(
                "INSERT INTO empresas (nome, cidade, uf, carga_horaria_diaria, intervalo_almoco_minutos) "
                "VALUES (?, ?, ?, ?, ?) RETURNING id",
                (nome.strip(), cidade.strip(), uf.strip().upper(), carga_horaria_diaria,
                 intervalo_almoco_minutos),
            )
            return cur.fetchone()["id"]
        else:
            cur = conn.execute(
                "INSERT INTO empresas (nome, cidade, uf, carga_horaria_diaria, intervalo_almoco_minutos) "
                "VALUES (?, ?, ?, ?, ?)",
                (nome.strip(), cidade.strip(), uf.strip().upper(), carga_horaria_diaria,
                 intervalo_almoco_minutos),
            )
            return cur.lastrowid


def listar_empresas():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM empresas ORDER BY nome").fetchall()


def obter_empresa(empresa_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM empresas WHERE id = ?", (empresa_id,)).fetchone()


def atualizar_empresa(empresa_id: int, nome: str, cidade: str, uf: str, carga_horaria_diaria: float,
                       intervalo_almoco_minutos: int = 60):
    with get_conn() as conn:
        conn.execute(
            "UPDATE empresas SET nome=?, cidade=?, uf=?, carga_horaria_diaria=?, "
            "intervalo_almoco_minutos=? WHERE id=?",
            (nome.strip(), cidade.strip(), uf.strip().upper(), carga_horaria_diaria,
             intervalo_almoco_minutos, empresa_id),
        )


def excluir_empresa(empresa_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))


# ---------------------------------------------------------------------------
# Feriados municipais (cadastro manual)
# ---------------------------------------------------------------------------

def adicionar_feriado_municipal(empresa_id: int, data: str, descricao: str, recorrente_anual: bool = True):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO feriados_municipais (empresa_id, data, descricao, recorrente_anual)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(empresa_id, data) DO UPDATE SET
                descricao=excluded.descricao,
                recorrente_anual=excluded.recorrente_anual
            """,
            (empresa_id, data, descricao.strip(), int(recorrente_anual)),
        )


def listar_feriados_municipais(empresa_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM feriados_municipais WHERE empresa_id = ? ORDER BY data",
            (empresa_id,),
        ).fetchall()


def excluir_feriado_municipal(feriado_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM feriados_municipais WHERE id = ?", (feriado_id,))


# ---------------------------------------------------------------------------
# Pontos (registros de entrada/saída)
# ---------------------------------------------------------------------------

def salvar_ponto(empresa_id: int, data: str, entrada: str, saida_prevista: str,
                  saida_real: str | None, justificativa: str | None, status: str,
                  minutos_extra: int, minutos_devidos: int,
                  eh_fim_de_semana: bool, eh_feriado: bool, feriado_descricao: str | None,
                  anexo_dados: bytes | None = None, anexo_nome: str | None = None):
    anexo_param = psycopg2.Binary(anexo_dados) if (USANDO_POSTGRES and anexo_dados is not None) else anexo_dados
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO pontos (empresa_id, data, entrada, saida_prevista, saida_real,
                                 justificativa, anexo_dados, anexo_nome, status, minutos_extra,
                                 minutos_devidos, eh_fim_de_semana, eh_feriado, feriado_descricao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(empresa_id, data) DO UPDATE SET
                entrada=excluded.entrada,
                saida_prevista=excluded.saida_prevista,
                saida_real=excluded.saida_real,
                justificativa=excluded.justificativa,
                anexo_dados=excluded.anexo_dados,
                anexo_nome=excluded.anexo_nome,
                status=excluded.status,
                minutos_extra=excluded.minutos_extra,
                minutos_devidos=excluded.minutos_devidos,
                eh_fim_de_semana=excluded.eh_fim_de_semana,
                eh_feriado=excluded.eh_feriado,
                feriado_descricao=excluded.feriado_descricao
            """,
            (empresa_id, data, entrada, saida_prevista, saida_real, justificativa,
             anexo_param, anexo_nome, status, minutos_extra, minutos_devidos,
             int(eh_fim_de_semana), int(eh_feriado), feriado_descricao),
        )


def obter_ponto(empresa_id: int, data: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM pontos WHERE empresa_id = ? AND data = ?", (empresa_id, data)
        ).fetchone()


def listar_pontos(empresa_id: int, data_inicio: str | None = None, data_fim: str | None = None):
    query = "SELECT * FROM pontos WHERE empresa_id = ?"
    params = [empresa_id]
    if data_inicio:
        query += " AND data >= ?"
        params.append(data_inicio)
    if data_fim:
        query += " AND data <= ?"
        params.append(data_fim)
    query += " ORDER BY data"
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def excluir_ponto(ponto_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM pontos WHERE id = ?", (ponto_id,))


def banco_de_horas(empresa_id: int) -> dict:
    """Banco de horas acumulado (todo o histórico, não só um período).

    saldo = total de hora extra − total de hora devida, em minutos.
    Saídas antecipadas COM justificativa nunca entram como hora devida
    (isso já é garantido em ponto_logic.avaliar_saida — aqui só somamos
    o que foi gravado em cada ponto).
    """
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT COALESCE(SUM(minutos_extra), 0) AS total_extra,
                   COALESCE(SUM(minutos_devidos), 0) AS total_devida
            FROM pontos
            WHERE empresa_id = ?
            """,
            (empresa_id,),
        ).fetchone()
    total_extra = row["total_extra"]
    total_devida = row["total_devida"]
    return {
        "total_extra": total_extra,
        "total_devida": total_devida,
        "saldo": total_extra - total_devida,
    }


# ---------------------------------------------------------------------------
# Configurações gerais (chave/valor) — usado para os dados de notificação
# por Telegram e para a senha de acesso, mas serve pra qualquer config futura.
# ---------------------------------------------------------------------------

def definir_config(chave: str, valor: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO configuracoes (chave, valor) VALUES (?, ?) "
            "ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
            (chave, valor),
        )


def obter_config(chave: str, padrao: str | None = None) -> str | None:
    with get_conn() as conn:
        row = conn.execute("SELECT valor FROM configuracoes WHERE chave = ?", (chave,)).fetchone()
    return row["valor"] if row else padrao
