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
esse script lê as empresas/pontos E a configuração do Telegram de cada
destinatário, configurada na tela "⚙️ Configurações" do app.

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

    destinatarios = db.listar_destinatarios_telegram()
    if not destinatarios:
        print(
            "ERRO: Nenhum destinatário do Telegram configurado ainda. "
            "Configure ao menos um na tela '⚙️ Configurações' do app antes "
            "de agendar esse script.",
            file=sys.stderr,
        )
        sys.exit(1)

    empresas = db.listar_empresas()
    if not empresas:
        print("Nenhuma empresa cadastrada. Nada a notificar.")
        return
    empresas_por_id = {e["id"]: e for e in empresas}

    hoje = date.today()
    houve_erro = False

    for destinatario in destinatarios:
        ja_notificado_hoje = destinatario["ultima_notificacao_data"] == hoje.isoformat()
        if ja_notificado_hoje and not args.forcar:
            print(f"[{destinatario['nome']}] Já notificado hoje. Pulando (use --forcar para reenviar).")
            continue

        ids_str = destinatario["empresas_ids"] or ""
        ids_selecionados = {int(i) for i in ids_str.split(",") if i.strip().isdigit()}
        empresas_do_destinatario = [empresas_por_id[i] for i in ids_selecionados if i in empresas_por_id]
        if not empresas_do_destinatario:
            print(f"[{destinatario['nome']}] Nenhuma empresa selecionada pra ele(a). Nada a notificar.")
            continue

        blocos = []
        for empresa in empresas_do_destinatario:
            faltando = utils.dias_uteis_sem_registro(empresa, janela_dias=14)
            if faltando:
                dias_fmt = ", ".join(utils.formatar_data_br(d) for d in faltando[-5:])
                a_mais = f" (+{len(faltando) - 5} dia(s) anterior(es))" if len(faltando) > 5 else ""
                blocos.append(f"• *{empresa['nome']}*: {dias_fmt}{a_mais}")

        if not blocos:
            print(f"[{destinatario['nome']}] Tudo em dia. Nenhuma mensagem enviada.")
            continue

        saudacao = f"Oi {destinatario['nome']}! " if destinatario["nome"] else "Oi! "
        texto = (
            f"{saudacao}🔔 *Ponto Fácil* — você está sem registro de ponto em:\n\n"
            + "\n".join(blocos)
            + "\n\nNão esquece de bater o ponto! 🕒"
        )

        sucesso, erro = telegram_notify.enviar_mensagem(
            destinatario["bot_token"], destinatario["chat_id"], texto
        )
        if sucesso:
            db.definir_ultima_notificacao_destinatario(destinatario["id"], hoje.isoformat())
            print(f"[{destinatario['nome']}] Mensagem enviada com sucesso.")
        else:
            print(f"[{destinatario['nome']}] ERRO ao enviar mensagem: {erro}", file=sys.stderr)
            houve_erro = True

    if houve_erro:
        sys.exit(1)


if __name__ == "__main__":
    main()
