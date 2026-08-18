"""Tela: configurações gerais — notificação por Telegram.

Suporta mais de uma pessoa recebendo alerta (ex: você e seu marido, cada
um com seu próprio chat do Telegram e suas próprias empresas) — cada
"destinatário" tem seu nome, token do bot, chat ID e a lista de empresas
que ele quer ser avisado.
"""

import streamlit as st

import db
import telegram_notify

st.title("⚙️ Configurações")

st.subheader("🔔 Lembrete por Telegram")
st.caption(
    "Quando configurado, o lembrete de ponto pendente também pode ser "
    "enviado pro Telegram de cada pessoa automaticamente todo dia (via "
    "GitHub Actions — veja o passo a passo no README), mesmo sem abrir "
    "este site. Dá pra cadastrar mais de um destinatário — por exemplo, "
    "você e seu marido, cada um recebendo alerta só das empresas dele."
)

with st.expander("Como conseguir o token do bot e o chat ID (passo a passo)"):
    st.markdown(
        """
1. No Telegram, procure por **@BotFather** e inicie uma conversa com ele.
2. Mande o comando `/newbot` e siga as instruções (escolha um nome e um
   usuário terminado em `bot`, ex: `pontofacil_gabi_bot`). **Esse mesmo
   bot pode ser usado por mais de uma pessoa** — não precisa criar um bot
   novo pra cada destinatário, só descobrir o chat ID de cada um (próximo
   passo).
3. O BotFather vai te dar um **token** (algo como
   `123456789:AAExemploDeTokenAquiXYZ`). Copie e cole no campo abaixo.
4. Cada pessoa que quiser receber alerta deve procurar o bot (pelo nome de
   usuário escolhido) e mandar **qualquer mensagem** pra ele (ex: "oi") —
   isso é necessário pra ele conseguir responder depois.
5. No navegador, acesse (trocando `SEU_TOKEN` pelo token do passo 3):
   `https://api.telegram.org/botSEU_TOKEN/getUpdates`
6. Procure por `"chat":{"id":` no texto que aparecer — pode ter mais de uma
   ocorrência, uma pra cada pessoa que já mandou mensagem. O número logo
   depois de cada uma é o **chat ID** daquela pessoa.
        """
    )

st.divider()

empresas = db.listar_empresas()
destinatarios = db.listar_destinatarios_telegram()


def _form_destinatario(destinatario=None):
    """Formulário de criar/editar um destinatário. `destinatario=None` = novo."""
    eh_novo = destinatario is None
    prefixo_key = "novo" if eh_novo else str(destinatario["id"])

    ids_atuais = set()
    if not eh_novo:
        ids_str = destinatario["empresas_ids"] or ""
        ids_atuais = {int(i) for i in ids_str.split(",") if i.strip().isdigit()}
    empresas_padrao = [e for e in empresas if e["id"] in ids_atuais] if not eh_novo else []

    with st.form(f"form_destinatario_{prefixo_key}"):
        nome = st.text_input(
            "Nome (pra personalizar a mensagem)",
            value="" if eh_novo else destinatario["nome"],
            placeholder="Ex: Gabi, Marido...",
            key=f"nome_{prefixo_key}",
        )
        token = st.text_input(
            "Token do bot", value="" if eh_novo else destinatario["bot_token"],
            type="password",
            placeholder="123456789:AAExemploDeTokenAquiXYZ",
            key=f"token_{prefixo_key}",
        )
        chat_id = st.text_input(
            "Chat ID", value="" if eh_novo else destinatario["chat_id"],
            placeholder="Ex: 987654321",
            key=f"chat_id_{prefixo_key}",
        )
        if empresas:
            empresas_escolhidas = st.multiselect(
                "De quais empresas essa pessoa quer receber alerta?",
                options=empresas,
                default=empresas_padrao,
                format_func=lambda e: (
                    f"{e['nome']} ({e['responsavel']})" if e["responsavel"] else e["nome"]
                ),
                key=f"empresas_{prefixo_key}",
            )
        else:
            empresas_escolhidas = []
            st.caption("Cadastre uma empresa primeiro (tela 🏢 Cadastrar Empresa) pra poder escolher aqui.")

        rotulo_botao = "➕ Adicionar destinatário" if eh_novo else "💾 Salvar"
        salvar = st.form_submit_button(rotulo_botao, key=f"salvar_{prefixo_key}")

    if salvar:
        if not nome.strip() or not token.strip() or not chat_id.strip():
            st.error("Preencha nome, token e chat ID.")
        else:
            ids_escolhidos = ",".join(str(e["id"]) for e in empresas_escolhidas)
            if eh_novo:
                db.criar_destinatario_telegram(nome, token, chat_id, ids_escolhidos)
                st.success(f"{nome} adicionado(a)!")
            else:
                db.atualizar_destinatario_telegram(
                    destinatario["id"], nome, token, chat_id, ids_escolhidos
                )
                st.success("Configurações salvas!")
            st.rerun()


st.subheader("👤 Destinatários cadastrados")
if not destinatarios:
    st.info("Nenhum destinatário cadastrado ainda. Adicione um abaixo.")
else:
    for destinatario in destinatarios:
        with st.expander(f"🔔 {destinatario['nome']}"):
            _form_destinatario(destinatario)

            col_teste, col_excluir = st.columns(2)
            with col_teste:
                if st.button("📨 Enviar mensagem de teste", key=f"teste_{destinatario['id']}"):
                    saudacao = f"Oi {destinatario['nome']}! " if destinatario['nome'] else "Oi! "
                    sucesso, erro = telegram_notify.enviar_mensagem(
                        destinatario["bot_token"], destinatario["chat_id"],
                        f"{saudacao}🕒 Essa é uma mensagem de teste do *Ponto Fácil*. Se você "
                        "recebeu isso, a configuração do Telegram está funcionando! ✅",
                    )
                    if sucesso:
                        st.success("Mensagem enviada! Confira o Telegram.")
                    else:
                        st.error(f"Não consegui enviar: {erro}")
            with col_excluir:
                if st.button("🗑️ Remover destinatário", key=f"excluir_{destinatario['id']}"):
                    db.excluir_destinatario_telegram(destinatario["id"])
                    st.warning(f"{destinatario['nome']} removido(a).")
                    st.rerun()

st.divider()
st.subheader("➕ Adicionar novo destinatário")
_form_destinatario(None)

st.divider()
st.caption(
    "Essas configurações ficam salvas no banco de dados do app (o mesmo "
    "que guarda empresas e pontos) — o script de lembrete automático "
    "(GitHub Actions) lê essas mesmas informações direto do banco, então "
    "só precisa configurar aqui uma vez por pessoa."
)
