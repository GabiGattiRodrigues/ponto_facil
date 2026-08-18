#!/usr/bin/env python3
"""
notificar_pendencias.py — Script standalone (roda FORA do Streamlit) que
checa, pra cada empresa cadastrada, se há dias úteis sem ponto registrado
e manda um aviso pelo Telegram se houver.

Feito pra rodar de forma agendada e independente do seu computador — o
GitHub Actions (veja .github/workflows/lembrete_ponto.yml) executa esse
script todo dia num horário fixo, direto nos servidores do GitHub.

Pré-requisito: a variável de ambiente DATABASE_URL precisa apontar pro
banco Postgres (Supabase) que o app hospedado também usa — é de lá que
esse script lê as empresas/pontos E a configuração do Telegram (token,
chat ID, nome), configurada uma vez na tela "⚙️ Configurações" do app.

Uso manual (pra testar):
    DATABASE_URL="postgresql://..." python notificar_pendencias.py
    DATABASE_URL="postgresql://..." python notificar_pendencias.py --forcar
"""

import argparse
import sys
from datetime import date

import db
import ponto_logic
import telegram_notify
import utils


def main():
    parser = argparse.ArgumentParser(description="Notifica pendências de ponto pelo Telegram.")
    parser.add_argument(
        "--forcar", action="store_true",
        help="Envia mesmo se já tiver sido notificado hoje (útil pra testar).",
    )
    args = parser.parse_args()

    if not db.USANDO_POSTGRES:
        print(
            "ERRO: DATABASE_URL não está configurada. Esse script é pra rodar "
            "contra o banco Postgres (Supabase) do app hospedado, não faz "
            "sentido rodar contra um SQLite local vazio recém-criado.",
            file=sys.stderr,
        )
        sys.exit(1)

    db.init_db()

    token = db.obter_config("telegram_bot_token")
    chat_id = db.obter_config("telegram_chat_id")
    nome = db.obter_config("nome_usuario") or ""

    if not token or not chat_id:
        print(
            "ERRO: Telegram não configurado ainda. Configure o token e o "
            "chat ID na tela '⚙️ Configurações' do app antes de agendar "
            "esse script.",
            file=sys.stderr,
        )
        sys.exit(1)

    hoje = date.today()
    ja_notificado_hoje = db.obter_config("ultima_notificacao_data") == hoje.isoformat()
    if ja_notificado_hoje and not args.forcar:
        print(f"Já notificado hoje ({hoje.isoformat()}). Nada a fazer. Use --forcar para reenviar.")
        return

    empresas = db.listar_empresas()
    if not empresas:
        print("Nenhuma empresa cadastrada. Nada a notificar.")
        return

    ids_selecionados_str = db.obter_config("telegram_empresas_ids")  # None = todas
    if ids_selecionados_str is not None:
        ids_selecionados = {int(i) for i in ids_selecionados_str.split(",") if i.strip().isdigit()}
        empresas = [e for e in empresas if e["id"] in ids_selecionados]
        if not empresas:
            print("Nenhuma empresa selecionada pra receber alerta (veja Configurações no app). Nada a notificar.")
            return

    blocos = []
    for empresa in empresas:
        faltando = utils.dias_uteis_sem_registro(empresa, janela_dias=14)
        if faltando:
            dias_fmt = ", ".join(utils.formatar_data_br(d) for d in faltando[-5:])
            a_mais = f" (+{len(faltando) - 5} dia(s) anterior(es))" if len(faltando) > 5 else ""
            blocos.append(f"• *{empresa['nome']}*: {dias_fmt}{a_mais}")

    if not blocos:
        print("Tudo em dia em todas as empresas. Nenhuma mensagem enviada (só avisamos quando falta algo).")
        return

    saudacao = f"Oi {nome}! " if nome else "Oi! "
    texto = (
        f"{saudacao}🔔 *Ponto Fácil* — você está sem registro de ponto em:\n\n"
        + "\n".join(blocos)
        + "\n\nNão esquece de bater o ponto! 🕒"
    )

    sucesso, erro = telegram_notify.enviar_mensagem(token, chat_id, texto)
    if sucesso:
        db.definir_config("ultima_notificacao_data", hoje.isoformat())
        print("Mensagem enviada com sucesso.")
    else:
        print(f"ERRO ao enviar mensagem: {erro}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
