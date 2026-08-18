@echo off
setlocal

rem Sempre roda a partir da pasta onde este arquivo está, nao importa
rem de onde ele foi chamado.
cd /d "%~dp0"

if not exist venv (
    echo [Ponto Facil] Criando ambiente virtual em .\venv ...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERRO: nao consegui criar o ambiente virtual.
        echo Verifique se o Python esta instalado e no PATH.
        echo Teste rodando "python --version" numa outra janela de terminal.
        echo.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo [Ponto Facil] Instalando/atualizando dependencias...
pip install -q -r requirements.txt

echo.
echo [Ponto Facil] Iniciando o app... uma aba do navegador deve abrir sozinha.
echo Para PARAR o app, volte aqui nesta janela e aperte Ctrl+C.
echo.
streamlit run app.py

pause
