# Ponto Fácil 🕒

App de controle de ponto em Python (Streamlit), com detecção automática de
feriados nacionais e estaduais, cálculo de hora extra / hora devida e
dashboard diário/mensal.

## O que o app faz

- Cadastro de empresas (nome, cidade, estado, carga horária diária,
  intervalo de almoço).
- Ao cadastrar a empresa, os feriados **nacionais e estaduais** do ano já são
  detectados automaticamente (usando a biblioteca `holidays`), além dos
  **finais de semana**.
- Feriados **municipais** são cadastrados manualmente (uma vez por cidade) —
  não existe uma base pública gratuita cobrindo os ~5.570 municípios do
  Brasil, então essa parte é manual mesmo.
- Tela de "Bater Ponto": você digita o horário de entrada e o app já calcula
  o horário de saída previsto (entrada + carga horária **+ intervalo de
  almoço**, ex: entrada 08:00 + 8h de trabalho + 1h de almoço = saída
  prevista 17:00 — como prevê a CLT).
- Se a saída real for diferente da prevista:
  - até 5 minutos de diferença (para mais ou para menos) → considerado normal;
  - saiu **antes** do previsto (além dos 5 min): se você informar uma
    justificativa (ex: consulta médica), não conta como hora devida; sem
    justificativa, conta como **hora devida** (em minutos);
  - saiu **depois** do previsto (além dos 5 min) → conta como **hora extra**
    (em minutos).
- Ao justificar uma saída antecipada, dá pra **anexar um comprovante**
  (foto de atestado, PDF etc.) — fica salvo junto com o registro do dia e
  pode ser visto depois pelo dashboard.
- **Banco de horas acumulado**: saldo de hora extra − hora devida
  considerando todo o histórico da empresa, sempre visível na tela inicial
  e no topo do dashboard.
- Dashboard diário e mensal, com gráfico de saldo (hora extra − hora devida)
  por dia e tendência dos últimos 6 meses.
- Lembrete automático na tela inicial quando um dia útil ficou sem ponto
  registrado — e, se você configurar (veja a seção 8), também pelo
  **Telegram**, mesmo sem abrir o site.
- Pode rodar só no seu computador (modo local, pra simular) OU publicado
  como um site de verdade, protegido por senha, funcionando sozinho e
  independente do seu PC (veja a seção 8).

---

## 1. Onde criar a pasta (e por que isso importa)

No Windows, caminhos de arquivo muito longos (mais de ~260 caracteres) podem
dar erro ao instalar pacotes Python, principalmente se a pasta do projeto já
estiver várias pastas dentro de `Documentos`, `OneDrive` ou "Área de
Trabalho". Para evitar isso:

**Windows:** crie a pasta bem perto da raiz do disco, por exemplo:

```
C:\dev\ponto_app
```

(Pode ser `C:\projetos\ponto_app` também — o importante é ficar perto da
raiz, fora de pastas sincronizadas com OneDrive.)

**macOS / Linux:** não costuma ter esse problema, mas por organização, use
algo como:

```
~/dev/ponto_app
```

### Passo a passo

1. Abra o **Explorador de Arquivos** (Windows) ou o **Finder** (Mac).
2. Vá até o disco `C:\` (Windows) ou sua pasta pessoal (Mac).
3. Crie uma pasta chamada `dev` (se ainda não existir).
4. Dentro dela, crie a pasta `ponto_app` — é aí que você vai extrair os
   arquivos que eu te enviei.

Se preferir fazer isso pelo terminal:

```bash
# Windows (PowerShell)
mkdir C:\dev\ponto_app

# macOS / Linux
mkdir -p ~/dev/ponto_app
```

Depois, **extraia o .zip que eu te mandei dentro dessa pasta** (o conteúdo
do zip, não a pasta zip em si — os arquivos `app.py`, `db.py` etc. devem
ficar direto dentro de `ponto_app/`).

---

## 2. Abrindo no Cursor

1. Abra o Cursor.
2. Vá em **File → Open Folder...** (Arquivo → Abrir Pasta).
3. Selecione a pasta `C:\dev\ponto_app` (ou `~/dev/ponto_app` no Mac).
4. Abra o terminal integrado do Cursor: menu **Terminal → New Terminal**
   (ou atalho `` Ctrl+` ``).

---

## 3. Instalando e rodando

O projeto já vem com um script que faz tudo sozinho: cria o ambiente
virtual (venv) na primeira vez, ativa ele, instala as dependências e roda o
app. **Sempre roda dentro do venv, nunca mexe nos pacotes globais da sua
máquina.**

### Caminho fácil (recomendado): usar o script pronto

No terminal do Cursor (já dentro da pasta do projeto):

```bash
# Windows (PowerShell ou prompt de comando)
setup_e_rodar.bat

# macOS / Linux
chmod +x setup_e_rodar.sh   # só precisa fazer isso uma vez
./setup_e_rodar.sh
```

No Windows também dá pra simplesmente **dar duplo clique** no arquivo
`setup_e_rodar.bat` pelo Explorador de Arquivos.

Da próxima vez que quiser rodar o app, é só executar o mesmo script de
novo — ele percebe que o venv já existe e pula direto para instalar (se
houver algo novo) e abrir o app.

### Caminho manual (se preferir entender/controlar cada passo)

```bash
# 1. Crie um ambiente virtual (mantém os pacotes isolados do resto da máquina)
python -m venv venv

# 2. Ative o ambiente virtual
#   Windows:
venv\Scripts\activate
#   macOS/Linux:
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Rode o app
streamlit run app.py
```

Se algum dia abrir o app e aparecer um aviso amarelo no topo dizendo que
ele não está rodando dentro de um ambiente virtual, é porque o Python
usado foi o global da máquina (por exemplo, rodou `streamlit run app.py`
sem ativar o venv antes) — use o script `setup_e_rodar` para corrigir.

Em qualquer um dos dois caminhos, o Streamlit abre automaticamente uma aba
no navegador em `http://localhost:8501`. Se não abrir sozinho, copie esse
endereço e cole no navegador. Para parar o app, volte ao terminal e aperte
`Ctrl+C`.

---

## 4. Como os dados são guardados

O app funciona em dois modos, escolhidos automaticamente:

- **Modo local** (o que você está usando ao rodar pelo Cursor, sem
  configurar nada extra): tudo fica salvo num arquivo `data/ponto.db`
  (SQLite), incluindo os comprovantes anexados. Não precisa instalar
  nenhum banco separado.
  - **Backup:** basta copiar esse arquivo `ponto.db` para outro lugar.
  - **Zerar tudo:** feche o app e apague o arquivo `data/ponto.db` — na
    próxima vez que rodar, ele cria um banco novo do zero.
- **Modo nuvem** (quando publicado como site — seção 8): os dados ficam num
  banco Postgres externo (Supabase), não no disco do servidor que hospeda
  o site. Isso é necessário porque serviços como o Streamlit Community
  Cloud não garantem que arquivos locais sobrevivam a reinicializações do
  app — testei e confirmei que isso é um problema real relatado por
  bastante gente, então um controle de ponto de verdade não pode depender
  disso.

Você não precisa escolher manualmente qual modo usar: o app detecta
sozinho, baseado em ter (modo nuvem) ou não ter (modo local) uma
configuração de banco Postgres nos secrets.

---

## 5. Usando o app

1. **🏢 Cadastrar Empresa** — cadastre a empresa com cidade, estado, carga
   horária diária TRABALHADA (ex: 8.0 para 8h, 6.0 para 6h) e o intervalo de
   almoço em minutos (o app já sugere 60 min para jornadas acima de 6h, 15
   min entre 4h e 6h, conforme a CLT — pode ajustar se for diferente). Os
   feriados nacionais/estaduais do ano aparecem automaticamente logo abaixo
   do cadastro, para você conferir.
2. **📅 Feriados Municipais** *(opcional, mas recomendado)* — cadastre os
   feriados específicos da cidade da empresa (aniversário da cidade,
   padroeiro/a etc.), uma vez só. Marque "repetir todo ano" para não
   precisar recadastrar anualmente.
3. **🕒 Bater Ponto** — escolha a empresa e a data, informe o horário de
   entrada (a saída prevista já aparece calculada, incluindo o almoço) e,
   quando bater a saída, marque "Já bati a saída hoje" e informe o horário
   real. Se você saiu antes do previsto, o app pede uma justificativa
   opcional e permite anexar um comprovante (foto/PDF do atestado, por
   exemplo).
4. **📊 Dashboard** — acompanhe por dia ou por mês: banco de horas
   acumulado, total de hora extra, hora devida, saldo, dias sem registro,
   o gráfico de saldo e os comprovantes anexados no período.

---

## 6. Estrutura dos arquivos

```
ponto_app/
├── app.py                          # ponto de entrada: config + senha + navegação
├── screens/
│   ├── inicio.py                   # lembretes + visão geral das empresas
│   ├── cadastrar_empresa.py
│   ├── bater_ponto.py
│   ├── feriados_municipais.py
│   ├── dashboard.py
│   └── configuracoes.py            # configuração do lembrete por Telegram
├── db.py                           # acesso ao banco (SQLite local OU Postgres na nuvem)
├── holidays_br.py                  # feriados nacionais/estaduais + municipais
├── ponto_logic.py                  # regras de hora extra / hora devida / almoço
├── anexos.py                       # helpers pros comprovantes anexados
├── auth.py                         # tela de senha (só ativa se configurada)
├── telegram_notify.py              # envio de mensagens pelo Telegram
├── notificar_pendencias.py         # script standalone rodado pelo GitHub Actions
├── charts.py                       # gráficos do dashboard (Plotly)
├── theme.py                        # cores e CSS (tema azul)
├── utils.py                        # funções auxiliares
├── env_check.py                    # detecta se está rodando fora do venv
├── setup_e_rodar.bat               # script de setup + execução (Windows)
├── setup_e_rodar.sh                # script de setup + execução (macOS/Linux)
├── requirements.txt
├── .github/workflows/lembrete_ponto.yml  # agendamento do lembrete (GitHub Actions)
├── .streamlit/
│   ├── config.toml                 # tema visual do Streamlit
│   └── secrets.toml.example        # modelo de configuração (copiar e preencher)
└── data/ponto.db                   # banco de dados local (criado automaticamente)
```

> Nota técnica: as telas ficam em `screens/` com nomes de arquivo simples
> (sem emoji) de propósito — numa versão anterior, os emojis no nome do
> arquivo (ex: `1_🏢_Cadastrar_Empresa.py`) ficavam corrompidos dependendo
> de como o zip era extraído no Windows, e o menu lateral aparecia com
> caracteres estranhos. Agora o ícone de cada aba é só texto dentro do
> código Python (`app.py`), o que funciona em qualquer sistema.

---

## 8. Publicando como site (deploy) — opcional

Isso é só necessário se você quiser que o app fique rodando sozinho, num
endereço da internet, independente do seu computador estar ligado. Pra só
simular/usar localmente, pode pular esta seção inteira.

São 4 partes, cada uma configurada **uma vez só**: banco de dados
(Supabase), hospedagem do site (Streamlit Community Cloud), senha de
acesso, e o lembrete automático (Telegram + GitHub Actions).

### 8.1. Criar o banco de dados (Supabase)

1. Crie uma conta grátis em [supabase.com](https://supabase.com) e um novo
   projeto (escolha uma senha forte pro banco quando pedir — anote ela).
2. Dentro do projeto, clique no botão verde **Connect**, no topo da tela
   (fica ao lado do seletor de branch/"main"). A Supabase mudou de lugar
   essa opção algumas vezes — hoje ela não fica mais dentro de "Project
   Settings", é esse botão no topo mesmo.
3. Vai abrir uma janela com várias abas: **Framework**, **Server**,
   **Direct**, **ORM**, **MCP**. Ela abre por padrão na aba "Framework"
   (mostra código pra Next.js etc.) — **clique na aba "Direct"** (tem um
   ícone de banco de dados, e o texto "Connection string" embaixo do
   nome), que é a que interessa pra gente.
4. Dentro da aba "Direct", escolha o modo **Session pooler** (funciona
   melhor com o Streamlit Community Cloud) e copie a connection string no
   formato **URI** — algo como
   `postgresql://postgres.xxxxxxxxxxxx:[SUA-SENHA]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres`.
5. Troque `[SUA-SENHA]` (ou `[YOUR-PASSWORD]`) pela senha que você definiu
   no passo 1.
6. Guarde essa string — você vai colar ela no passo 8.3.

> Se o botão **Connect** não aparecer do jeito descrito acima, é porque a
> Supabase mudou a interface de novo (eles fazem isso com uma certa
> frequência). Nesse caso, procure por "Connect" ou "Connection string" na
> busca do dashboard (`Ctrl+K` / `Cmd+K`) — o destino é sempre a mesma
> informação: a URI de conexão do Postgres.

Você não precisa criar as tabelas manualmente: o app cria tudo sozinho na
primeira vez que conectar.

### 8.2. Subir o projeto pro GitHub

O Streamlit Community Cloud publica direto a partir de um repositório
GitHub.

1. Crie uma conta no [github.com](https://github.com) se ainda não tiver.
2. Crie um repositório novo (pode ser privado) e suba a pasta `ponto_app`
   inteira pra lá — pelo Cursor mesmo (aba de controle de versão / Git) ou
   pelo terminal:
   ```bash
   git init
   git add .
   git commit -m "Primeira versão do Ponto Fácil"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/ponto-facil.git
   git push -u origin main
   ```
   (O `.gitignore` já garante que `secrets.toml`, o `venv/` e o `ponto.db`
   local não vão parar no GitHub por engano.)

### 8.3. Publicar no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) e entre com sua
   conta GitHub.
2. Clique em **New app**, escolha o repositório que você acabou de criar,
   o branch `main` e o arquivo principal `app.py`.
3. Antes de clicar em "Deploy", vá em **Advanced settings → Secrets** e
   cole (ajustando com seus valores reais):
   ```toml
   app_password = "escolha-uma-senha-forte-aqui"

   [postgres]
   url = "postgresql://postgres:SUASENHA@db.xxxxxxxxxxxx.supabase.co:5432/postgres"
   ```
4. Clique em **Deploy**. Em alguns minutos o app fica no ar, num endereço
   tipo `https://seu-app.streamlit.app`.

A partir daqui, sempre que você der `git push` de novo, o Streamlit Cloud
atualiza o site sozinho.

### 8.4. Configurar o lembrete automático por Telegram

1. No próprio site (já publicado), acesse **⚙️ Configurações**, siga o
   passo a passo ali pra criar o bot e pegar o chat ID, preencha e salve.
   Teste com o botão "Enviar mensagem de teste agora".
2. No GitHub, vá nas configurações do repositório: **Settings → Secrets
   and variables → Actions → New repository secret**.
3. Crie um secret chamado `DATABASE_URL` com a MESMA connection string do
   Supabase que você usou no passo 8.3 (com a senha já preenchida).
4. Pronto — o workflow `.github/workflows/lembrete_ponto.yml` já está
   configurado pra rodar todo dia às 18h (horário de Brasília), de segunda
   a sexta, e manda a mensagem pro Telegram se faltar algum ponto. Pra
   testar na hora, sem esperar o horário: vá na aba **Actions** do
   repositório no GitHub, clique em "Lembrete de ponto (Telegram)" na
   lista à esquerda, depois em **Run workflow**.
5. Quer mudar o horário? Edite a linha `cron: "0 21 * * 1-5"` no arquivo
   `.github/workflows/lembrete_ponto.yml` — o horário é sempre em UTC
   (Brasília = UTC − 3h, então 18h em Brasília = 21h UTC).

### Resumo de quem fala com quem

- O **site** (Streamlit Cloud) lê e grava dados no **Supabase**.
- O **GitHub Actions** roda o script `notificar_pendencias.py` todo dia,
  lendo os mesmos dados do **Supabase** (inclusive a configuração do
  Telegram, salva pela tela Configurações) e mandando a mensagem.
- Nenhum dos dois depende do seu computador estar ligado.

---

## 9. Ideias para evoluir depois (não implementado ainda)

- Múltiplas entradas/saídas no mesmo dia (ex: registrar a saída/volta do
  almoço também, não só entrada e saída final).
- Exportar o relatório mensal em PDF ou Excel.
- Login para mais de uma pessoa usar o mesmo app com contas separadas
  (hoje a senha é única, compartilhada, sem multiusuário).

Qualquer uma dessas é só pedir que a gente implementa — o código foi
organizado em módulos separados (regras de negócio, banco de dados,
feriados, telas) justamente para facilitar mexer em uma parte sem
bagunçar as outras.
