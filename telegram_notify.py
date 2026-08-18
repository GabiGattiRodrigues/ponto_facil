"""
telegram_notify.py — Envio de mensagens pelo Telegram (usado para lembretes
de ponto pendente, sem precisar abrir o app).

Usa só a biblioteca padrão do Python (urllib), então não precisa instalar
nada além do que já está no requirements.txt.

Como conseguir o token e o chat ID: veja o passo a passo no README, seção
"Notificação por Telegram" — resumindo: crie um bot com o @BotFather e
descubra seu chat ID mandando uma mensagem pro bot e consultando a API
getUpdates (ou o app faz isso por você na tela de Configurações).
"""

import json
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_SEGUNDOS = 10


def enviar_mensagem(token: str, chat_id: str, texto: str) -> tuple[bool, str | None]:
    """Envia uma mensagem de texto pelo bot do Telegram.

    Retorna (sucesso, erro). Nunca lança exceção — problemas de rede ou
    configuração errada viram um erro explicado em texto, para o script
    (ou a tela de Configurações) poder mostrar pro usuário.
    """
    if not token or not chat_id:
        return False, "Token do bot ou chat ID não configurados."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    dados = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    try:
        requisicao = urllib.request.Request(url, data=dados, method="POST")
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT_SEGUNDOS) as resposta:
            corpo = json.loads(resposta.read().decode("utf-8"))
            if corpo.get("ok"):
                return True, None
            return False, corpo.get("description", "Erro desconhecido retornado pelo Telegram.")
    except urllib.error.HTTPError as e:
        try:
            corpo = json.loads(e.read().decode("utf-8"))
            descricao = corpo.get("description", str(e))
        except Exception:
            descricao = str(e)
        if e.code == 401:
            descricao = "Token do bot inválido (erro 401). Confira o token na tela de Configurações."
        elif e.code == 400 and "chat not found" in descricao.lower():
            descricao = (
                "Chat não encontrado (erro 400). Confira o chat ID — e lembre-se de "
                "mandar pelo menos uma mensagem para o bot antes de configurar."
            )
        return False, descricao
    except urllib.error.URLError as e:
        return False, f"Não consegui conectar ao Telegram: {e.reason}"
    except Exception as e:
        return False, f"Erro inesperado ao enviar mensagem: {e}"
