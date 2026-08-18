"""Tela: configurações gerais — notificação por Telegram."""

import streamlit as st

import db
import telegram_notify

st.title("⚙️ Configurações")

st.subheader("🔔 Lembrete por Telegram")
st.caption(
    "Quando configurado, o lembrete de ponto pendente também pode ser "
    "enviado pro seu Telegram automaticamente todo dia (via GitHub Actions "
    "— veja o passo a passo no README), mesmo sem abrir este site."
)

with st.expander("Como conseguir o token do bot e o chat ID (passo a passo)"):
    st.markdown(
        """
1. No Telegram, procure por **@BotFather** e inicie uma conversa com ele.
2. Mande o comando `/newbot` e siga as instruções (escolha um nome e um
   usuário terminado em `bot`, ex: `pontofacil_gabi_bot`).
3. O BotFather vai te dar um **token** (algo como
   `123456789:AAExemploDeTokenAquiXYZ`). Copie e cole no campo abaixo.
4. Procure o bot que você acabou de criar (pelo nome de usuário que
   escolheu) e mande **qualquer mensagem** pra ele (ex: "oi") — isso é
   necessário pra ele conseguir te responder depois.
5. No navegador, acesse (trocando `SEU_TOKEN` pelo token do passo 3):
   `https://api.telegram.org/botSEU_TOKEN/getUpdates`
6. Procure por `"chat":{"id":` no texto que aparecer — o número logo depois
   é o seu **chat ID**. Copie e cole no campo abaixo.
        """
    )

nome_atual = db.obter_config("nome_usuario", "")
token_atual = db.obter_config("telegram_bot_token", "")
chat_id_atual = db.obter_config("telegram_chat_id", "")

with st.form("form_config_telegram"):
    nome_usuario = st.text_input(
        "Seu nome (pra personalizar a mensagem, opcional)",
        value=nome_atual or "",
        placeholder="Ex: Gabi",
    )
    token = st.text_input(
        "Token do bot", value=token_atual or "", type="password",
        placeholder="123456789:AAExemploDeTokenAquiXYZ",
    )
    chat_id = st.text_input(
        "Chat ID", value=chat_id_atual or "", placeholder="Ex: 987654321",
    )
    salvar = st.form_submit_button("💾 Salvar configurações")

if salvar:
    db.definir_config("nome_usuario", nome_usuario.strip())
    db.definir_config("telegram_bot_token", token.strip())
    db.definir_config("telegram_chat_id", chat_id.strip())
    st.success("Configurações salvas!")
    st.rerun()

st.divider()

if st.button("📨 Enviar mensagem de teste agora"):
    token = db.obter_config("telegram_bot_token")
    chat_id = db.obter_config("telegram_chat_id")
    nome = db.obter_config("nome_usuario") or ""
    saudacao = f"Oi {nome}! " if nome else "Oi! "
    sucesso, erro = telegram_notify.enviar_mensagem(
        token, chat_id,
        f"{saudacao}🕒 Essa é uma mensagem de teste do *Ponto Fácil*. Se você "
        "recebeu isso, a configuração do Telegram está funcionando! ✅",
    )
    if sucesso:
        st.success("Mensagem enviada! Confira seu Telegram.")
    else:
        st.error(f"Não consegui enviar: {erro}")

st.divider()
st.caption(
    "Essas configurações ficam salvas no banco de dados do app (o mesmo "
    "que guarda empresas e pontos) — o script de lembrete automático "
    "(GitHub Actions) lê essas mesmas informações direto do banco, então "
    "só precisa configurar aqui uma vez."
)
