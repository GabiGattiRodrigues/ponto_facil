#!/usr/bin/env bash
# Cria (se preciso) e ativa o ambiente virtual, instala as dependências e
# roda o app. Uso: ./setup_e_rodar.sh  (ou: bash setup_e_rodar.sh)
set -e

# Sempre roda a partir da pasta onde este arquivo está.
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "[Ponto Fácil] Criando ambiente virtual em ./venv ..."
    PYTHON_BIN="python3"
    command -v python3 >/dev/null 2>&1 || PYTHON_BIN="python"
    "$PYTHON_BIN" -m venv venv
fi

source venv/bin/activate

echo "[Ponto Fácil] Instalando/atualizando dependências..."
pip install -q -r requirements.txt

echo ""
echo "[Ponto Fácil] Iniciando o app... uma aba do navegador deve abrir sozinha."
echo "Para PARAR o app, volte aqui neste terminal e aperte Ctrl+C."
echo ""
streamlit run app.py
