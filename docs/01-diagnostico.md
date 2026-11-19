# 01 — Diagnóstico técnico (Fase 1)

> Data da análise: 15/11/2026.
> Analisei dois projetos: **o seu projeto atual** (bot do Discord, hoje em `legado/`; a tabela 1.1 descreve a pasta como estava antes da limpeza) e **o projeto de referência** (`bot-ofertas-telegram.zip`). Todos os 29 arquivos do ZIP foram lidos, exceto o `uv.lock` (arquivo gerado automaticamente, só lista versões de bibliotecas).

## Resumo em 1 minuto

- **Seu projeto atual** é um único arquivo (`main.py`, 239 linhas) que abre o Chrome, lê a página de ofertas do Mercado Livre e posta no Discord. Ele funciona como prova de conceito, mas **não gera comissão** (não usa link de afiliado) e **reposta tudo a cada 10 minutos** (o controle de duplicidade não está ligado).
- **O projeto de referência** é bem mais maduro (2.700 linhas, modular) e já resolve boa parte do que você quer: Telegram, 4 plataformas, banco anti-repetição, filtros. Vamos aproveitar a **arquitetura e a lógica** dele.
- **Ponto de atenção principal:** as partes de Mercado Livre e Amazon da referência dependem de *scraping* com técnicas para se disfarçar de usuário humano, o que traz risco para a conta de afiliado. **Você decidiu seguir por esse caminho** quando não houver API oficial — veja a [seção 4](#4-decisões-registradas) para a decisão e as proteções que vamos adotar.
- **Nenhum dos dois projetos tem:** IA, cupons, vários canais, fila de publicação, métricas, testes automatizados ou deploy em servidor. Essas são as partes que vamos construir do zero.

---

## 1. Seu projeto atual (Discord)

### 1.1 Estrutura

| Arquivo / pasta | O que é | Situação |
|---|---|---|
| `main.py` | Todo o bot: coleta + envio ao Discord | Código principal |
| `config.py` | Token do Discord e ID do canal | ⚠️ Segredo escrito direto no código |
| `.env` | Arquivo para segredos | Vazio (não é usado) |
| `.gitignore` | Lista do que o Git deve ignorar | OK, mas incompleto |
| `package.json`, `package-lock.json`, `temp/node_modules/` | Dependências de **Node.js** | ❌ Não servem para nada (o projeto é Python) |
| `chromedriver.exe` | Driver do Chrome (12 MB, de 2023) | ❌ Desnecessário e está versionado no Git |
| `mercado_livre.html`, `promocoes.json`, `diagnostico.png` | Arquivos de teste/depuração | Sobras; estão versionadas no Git |
| `.venv/` | Ambiente virtual Python 3.12 | OK |

Bibliotecas instaladas no `.venv`: `discord.py 2.7`, `selenium 4.52`, `webdriver-manager`, `python-dotenv`, `requests`. **Não existe `requirements.txt`** — ou seja, não há registro de quais bibliotecas o projeto precisa.

### 1.2 Como funciona hoje

```
A cada 10 minutos (tasks.loop do discord.py)
   │
   ├─ 1. Abre um Chrome visível com Selenium
   ├─ 2. Acessa mercadolivre.com.br/ofertas e espera 5 segundos
   ├─ 3. Para cada cartão de produto com mais de 20% OFF:
   │      extrai nome, preço antigo, preço novo, link e imagem
   ├─ 4. Fecha o Chrome
   └─ 5. Envia cada produto ao canal do Discord como um "embed" com botão
```

Conceitos que você já usou corretamente e que vamos manter:

- **`asyncio.to_thread(coletar_promocoes)`** ([main.py:215](../legado/main.py#L215)): a coleta é lenta e "trava" o programa; rodá-la em uma thread separada deixa o bot livre para responder. A referência usa exatamente a mesma técnica.
- **`try/finally` com `driver.quit()`** ([main.py:141-143](../legado/main.py#L141-L143)): garante que o navegador feche mesmo quando dá erro.
- **Separar coleta e envio em funções diferentes**: é o embrião da arquitetura modular.

### 1.3 Problemas encontrados

Ordenados do mais grave para o menos grave.

| # | Problema | Onde | Por que importa |
|---|---|---|---|
| 1 | **Não há link de afiliado.** O link postado é o link comum do produto. | [main.py:107-110](../legado/main.py#L107-L110) | O objetivo do projeto é comissão. Hoje, uma venda feita pelo bot rende R$ 0. |
| 2 | **Duplicidade não funciona.** `links_enviados` recebe os links, mas nunca é consultado antes de enviar. Além disso vive só na memória (some ao reiniciar). | [main.py:18](../legado/main.py#L18), [main.py:217-223](../legado/main.py#L217-L223) | O bot reposta as mesmas ofertas a cada 10 minutos. |
| 3 | **Token do Discord escrito no código.** | `config.py` | Boa notícia: verifiquei o histórico do Git e esse arquivo **nunca foi commitado**. Mesmo assim ele está em uma pasta do OneDrive (sincronizada na nuvem). Recomendo gerar um token novo no portal do Discord quando puder e nunca mais guardar segredos em `.py`. |
| 4 | **Limpeza do link quebra links patrocinados.** O código remove tudo depois do `?`. Em links do tipo `click1.mercadolivre.com.br/mclics/...`, o destino está justamente nesses parâmetros. | [main.py:153-155](../legado/main.py#L153-L155) | Parte dos botões leva a uma página de erro. |
| 5 | **Scraping com disfarce anti-detecção.** O código esconde que é um robô (`navigator.webdriver`, `AutomationControlled`). | [main.py:35-48](../legado/main.py#L35-L48) | Contornar o bloqueio de robôs fere os termos de uso do site e tende a parar de funcionar sem aviso. |
| 6 | **Precisa de um Chrome com janela aberta.** O modo invisível (*headless*) foi desativado porque o ML bloqueia. | [main.py:26](../legado/main.py#L26) | Um servidor (VPS) não tem tela. Do jeito que está, o bot só roda no seu PC ligado. |
| 7 | **`except:` vazio.** Qualquer erro em um produto é engolido em silêncio. | [main.py:133-134](../legado/main.py#L133-L134) | Se o ML mudar o layout, o bot passa a achar 0 produtos e você não fica sabendo o motivo. |
| 8 | **Preço perde os centavos e é guardado como texto.** Só a parte inteira é lida (`R$ 189` em vez de `R$ 189,99`). | [main.py:91-105](../legado/main.py#L91-L105) | "Não inventar preços" começa por capturar o preço certo. Texto também não permite calcular desconto. |
| 9 | **Código morto depois de `roxo.run()`.** A linha `resultado = coletar_promocoes()` só executa quando o bot é encerrado — e aí abre o Chrome de novo. | [main.py:239](../legado/main.py#L239) | Comportamento inesperado ao fechar o bot. |
| 10 | **Espera fixa de 5 segundos.** | [main.py:62](../legado/main.py#L62) | Em internet lenta falha; em internet rápida desperdiça tempo. O certo é esperar *até o elemento aparecer*. |
| 11 | **Sem logs, sem testes, sem documentação, sem lista de dependências.** | — | Impossível diagnosticar falhas ou reinstalar o projeto em outra máquina. |
| 12 | **Dependências de Node.js em projeto Python.** `npm install selenium discord.py` instalou pacotes JavaScript homônimos, que o Python não usa. | `package.json`, `temp/` | 10 mil arquivos inúteis na pasta. |

### 1.4 O que dá para reaproveitar do seu projeto

| Item | Reaproveitamento |
|---|---|
| A ideia do fluxo coletar → filtrar por desconto → enviar | ✅ É a espinha dorsal do novo sistema |
| `asyncio.to_thread` para tarefas lentas | ✅ Mantemos |
| Filtro de desconto mínimo (20%) | ✅ Vira configuração, em vez de número fixo no código |
| Seletores CSS do ML (`.poly-card`, `poly-component__title`…) | ✅ Servem de ponto de partida para a leitura da página de ofertas (a referência tem versões mais completas) |
| Código do Discord (`discord.Embed`, `PromoBot`) | ❌ Substituído pelo Telegram. Guardamos em uma pasta `legado/` para consulta |
| Selenium + `chromedriver.exe` | ❌ Trocado por Playwright, que a referência usa e é mais estável. O `chromedriver.exe` deixa de ser necessário |

---

## 2. Projeto de referência (`bot-ofertas-telegram.zip`)

### 2.1 Estrutura completa

```
bot-ofertas-telegram/
├── COMECE_AQUI.txt        Instruções rápidas para leigos
├── README.md              Manual de instalação e uso
├── PAINEL.bat             Abre o painel gráfico (Windows)
├── run.bat                Roda o bot e reinicia se cair (Windows)
├── .env.example           Modelo do arquivo de segredos (vem em branco ✅)
├── .gitignore             Ignora .env, .venv, data/
├── .python-version        3.14
├── pyproject.toml         Lista de dependências
├── uv.lock                Versões exatas travadas (gerado pelo uv)
├── config.yaml            Ajustes que não são segredo (intervalos, filtros, nichos)
└── ofertas/               O pacote Python
    ├── __main__.py        Permite rodar com "python -m ofertas"
    ├── main.py            Comandos de terminal (check, run, ciclo, converter, postar, testar…)
    ├── config.py          Lê .env + config.yaml e monta o objeto de configuração
    ├── models.py          A classe Oferta (formato padrão de um produto)
    ├── db.py              Banco SQLite: registro do que já foi postado
    ├── utils.py           Funções pequenas (converter "R$ 1.234,56" em número, etc.)
    ├── formatter.py       Monta o texto do post
    ├── telegram_poster.py Envia o post (foto + legenda + botão)
    ├── pipeline.py        O ciclo: coletar → filtrar → escolher → gerar link → postar
    ├── bot_interativo.py  O bot do Telegram (comandos + conversor de link + agendador)
    ├── nichos.py          Catálogo de categorias por plataforma
    ├── painel.py          Servidor web local do painel de controle
    ├── painel_html.py     A página HTML do painel
    └── sources/           Uma "fonte" por plataforma
        ├── mercadolivre.py
        ├── amazon.py
        ├── shopee.py
        └── aliexpress.py
```

### 2.2 Tecnologias

| Tecnologia | Para que serve na referência |
|---|---|
| Python ≥ 3.12 | Linguagem |
| `uv` | Gerenciador de ambiente e dependências (substituto moderno do `pip` + `venv`) |
| `python-telegram-bot` v21 (com `job-queue`) | Falar com o Telegram e agendar os ciclos |
| `requests` | Chamadas HTTP às APIs (Shopee, Amazon, AliExpress) |
| `beautifulsoup4` + `lxml` | Ler HTML de páginas (scraping) |
| `playwright` | Controlar um navegador real (Mercado Livre e Amazon) |
| `python-dotenv` | Ler o arquivo `.env` |
| `PyYAML` | Ler o `config.yaml` |
| `sqlite3` (já vem no Python) | Banco de dados local |
| `http.server` (já vem no Python) | Servidor do painel gráfico |

### 2.3 Arquitetura e fluxo

```
                    ┌──────────────────────── bot_interativo.py ───────────────────────┐
                    │  Agendador (a cada 45 min)        Conversor (link colado no privado) │
                    └──────────────┬──────────────────────────────┬────────────────────┘
                                   ▼                              ▼
                             pipeline.py                  sources/<plataforma>.converter()
   ┌───────────────────────────────────────────────┐              │
   │ coletar()  → pede ofertas a cada fonte ativa  │              │
   │ filtrar()  → desconto, preço, palavras, banco │              │
   │ escolher() → top N alternando plataformas     │              │
   │ gerar links de afiliado (só das escolhidas)   │              │
   └──────────────────────┬────────────────────────┘              │
                          ▼                                       ▼
                 telegram_poster.py  ←── formatter.py (monta o texto)
                          │
                          ▼
                    db.registrar()  →  data/ofertas.db
```

A ideia central — e a melhor lição da referência — é a classe **`Oferta`** (`models.py`). Pense nela como uma **ficha padronizada**: não importa se o produto veio da Shopee, da Amazon ou do Mercado Livre, toda fonte devolve a mesma ficha (`titulo`, `preco`, `preco_original`, `url_afiliado`, `imagem`…). O resto do sistema só conhece a ficha, nunca os detalhes de cada loja. É isso que permite adicionar uma plataforma nova sem mexer no pipeline.

### 2.4 Funcionalidades, uma a uma

Para cada uma: como funciona, se aproveitamos e o que muda.

| Funcionalidade (arquivo) | Como funciona na referência | Decisão | O que muda no nosso projeto |
|---|---|---|---|
| **Modelo `Oferta`** (`models.py`) | *Dataclass* com os dados do produto; calcula o desconto se a loja não informar | ✅ Reaproveitar | Acrescentar cupom, forma de pagamento (Pix), categoria e data da coleta |
| **Contrato das fontes** (`sources/*.py`) | Todo módulo tem as mesmas 3 funções: `e_link()`, `buscar_ofertas()`, `converter()` | ✅ Reaproveitar a ideia | Formalizar o contrato (uma classe-base), para o Python avisar se uma fonte esquecer alguma função |
| **Detectar plataforma pelo link** (`sources/__init__.py`) | Percorre as fontes perguntando "este link é seu?" | ✅ Reaproveitar | Sem mudanças relevantes |
| **Pipeline** (`pipeline.py`) | Um ciclo completo em uma função | 🔧 Adaptar | Separar em etapas e colocar uma **fila** no meio: hoje a oferta é postada na hora; passaremos a enfileirar e publicar no ritmo certo |
| **Filtros** (`pipeline.filtrar`) | Desconto mínimo, faixa de preço, palavras bloqueadas, já postada | ✅ Reaproveitar | Acrescentar validação de dados (preço presente, desconto coerente) |
| **Seleção** (`pipeline.escolher`) | Ordena por desconto, alterna plataformas e pula variações do mesmo produto (compara as 5 primeiras palavras do título) | ✅ Reaproveitar | Depois, a IA ajuda a pontuar a qualidade da oferta |
| **Anti-repetição** (`db.py`) | Tabela `postadas` com `uid` = `plataforma:id`; não repete dentro de 7 dias | 🔧 Adaptar | Guardar histórico completo (não só a última vez), por canal, e permitir repostar quando o preço cair mais |
| **Formatação** (`formatter.py`) | Modelo fixo: `🔥 título / ❌ De / ✅ Por / loja` | 🔧 Adaptar | Seu padrão é outro (chamada comercial, "De \| Por no Pix 👑", cupom, link). A chamada virá da IA; os números, sempre do código |
| **Envio** (`telegram_poster.py`) | Envia foto com legenda e botão; se a foto falhar, envia só texto | ✅ Reaproveitar | Enviar para **vários** canais e tratar limites de envio do Telegram |
| **Bot interativo** (`bot_interativo.py`) | Comandos `/start`, `/id`, `/status`, `/ciclo`; você cola um link e ele mostra a prévia com botões Postar/Descartar | ✅ Reaproveitar | Acrescentar comandos de cupom (`/cupom`, `/esgotado`) e de canais |
| **Alerta ao dono** (`pipeline.avisar_dono`) | Se algo quebra, o bot manda mensagem no seu privado | ✅ Reaproveitar | Base do nosso monitoramento |
| **Horário ativo** (`config.dentro_do_horario`) | Não posta de madrugada | ✅ Reaproveitar | Usar fuso horário de Brasília explícito (o servidor pode estar em outro fuso) |
| **Configuração** (`config.py` + `config.yaml`) | Segredos no `.env`; ajustes no YAML | ✅ Reaproveitar a separação | Validar na inicialização e não usar objeto global (dificulta testes) |
| **Shopee** (`sources/shopee.py`) | **API oficial** de afiliados (GraphQL). Assina cada chamada com SHA-256. O link retornado já é o de afiliado | ✅ Reaproveitar | Corrigir a montagem da consulta (ver problema R4) |
| **AliExpress** (`sources/aliexpress.py`) | **API oficial** (Portals). Assina com HMAC-SHA256 | ⏸ Fora do escopo inicial | Você priorizou ML, Amazon e Shopee. Fica como expansão (Fase 10) |
| **Amazon** (`sources/amazon.py`) | Tenta a API oficial (Creators API); se a conta não for elegível, cai para scraping da busca com navegador | ✅ Reaproveitar | Mesma estratégia: API oficial primeiro, scraping como reserva. Ver seção 4 |
| **Mercado Livre** (`sources/mercadolivre.py`) | Scraping da página de ofertas em Chrome real logado + chamada a uma API **interna** do Linkbuilder para gerar o `meli.la` | ✅ Reaproveitar | Portar com proteções extras (ritmo baixo, alerta de sessão expirada, isolamento de falhas). Ver seção 4 |
| **Catálogo de nichos** (`nichos.py`) | Um nicho ("esporte") vira categorias do ML, departamentos da Amazon e palavras-chave da Shopee | ✅ Reaproveitar | Associar nichos a canais (canal de tecnologia, canal de moda…) |
| **Painel web** (`painel.py`, `painel_html.py`) | Página local para preencher o `.env` e ligar/desligar o bot | ❌ Não portar agora | Foi feito para leigos no Windows. Em servidor não se aplica, e você administrará pelo próprio Telegram. Reavaliamos na Fase 10 |
| **`.bat` e `winreg`** | Atalhos do Windows | ❌ Descartar | Em produção usaremos Linux |

### 2.5 Boas práticas da referência que vamos copiar

1. **Segredos fora do código**, com `.env.example` em branco como modelo.
2. **Uma ficha padrão (`Oferta`)** entre as lojas e o resto do sistema.
3. **Logs com nome por módulo** (`logging.getLogger("ofertas.shopee")`), em vez de `print`.
4. **Falha isolada por fonte**: se a Shopee cair, a Amazon continua (cada fonte tem seu `try/except` com log do erro).
5. **Degradar em vez de quebrar**: sem foto, posta texto; sem credencial, pula a fonte e avisa.
6. **Gerar o link de afiliado só das ofertas escolhidas**, não de todas (economiza chamadas).
7. **Comandos de teste por fonte** (`testar shopee`) que não postam nada.
8. **Texto escapado antes de enviar em HTML** (`html.escape`), evitando que um título com `<` quebre a mensagem.

### 2.6 Problemas e limitações da referência

| # | Problema | Onde | Impacto |
|---|---|---|---|
| R1 | **Mercado Livre usa API interna + disfarce de navegador.** O arquivo abre um Chrome "fora da tela", remove as marcas de automação e chama um endereço interno do painel de afiliados usando os cookies da sua sessão. | `sources/mercadolivre.py` | Não é um método autorizado. Risco de suspensão da conta de afiliado (e perda das comissões pendentes). Quebra quando o ML muda algo — os próprios comentários do código registram duas quebras em 2026. Exige um computador com tela. |
| R2 | **Amazon cai para scraping driblando o anti-robô.** | `sources/amazon.py` (linhas 151-330) | O contrato do programa de Associados proíbe coletar dados do site por robô. Risco de encerramento da conta. |
| R3 | **Nenhum teste automatizado.** | projeto todo | Qualquer alteração pode quebrar algo sem ninguém perceber. |
| R4 | **Consulta da Shopee montada colando texto.** O termo de busca entra direto na consulta; um termo com aspas quebra a chamada. | `sources/shopee.py:88` | Erro difícil de diagnosticar. Correção simples (usar `json.dumps`, como o próprio arquivo já faz na linha 144). |
| R5 | **"Preço original" da Shopee é calculado, não lido.** A API dá preço e % de desconto; o código faz a conta inversa. | `sources/shopee.py:61-62` | Pode divergir alguns centavos do que o cliente vê. Precisa ser tratado com cuidado por causa da regra "não inventar preços". |
| R6 | **Um único canal.** Só existe um `TELEGRAM_CHAT_ID`. | `config.py` | Não atende "gerenciar vários grupos e canais". |
| R7 | **Sem cupons.** Só a Amazon captura um texto "Cupom de X", sem validar nada. | — | Não atende os Exemplos 1 e 2 do seu padrão de mensagem. |
| R8 | **Sem IA.** Texto 100% fixo. | `formatter.py` | Não atende a seção 6 do seu pedido. |
| R9 | **Banco mínimo.** Uma tabela, uma linha por produto, sem histórico, sem métricas. | `db.py` | Não dá para gerar relatórios nem saber o que performa melhor. |
| R10 | **Sem fila.** Coleta e publica no mesmo passo; o intervalo entre posts é um `sleep`. | `pipeline.py` | Se o programa cair no meio, as ofertas escolhidas se perdem. |
| R11 | **Prévias pendentes só na memória.** | `bot_interativo.py:21` | Reiniciou o bot, as prévias aguardando aprovação "expiram". |
| R12 | **Configuração global criada ao importar.** | `config.py:87` | Dificulta testar e impede recarregar ajustes sem reiniciar. |
| R13 | **Painel web sem proteção contra requisições de outros sites.** O servidor local aceita comandos de qualquer página aberta no mesmo navegador. | `painel.py` | Uma página maliciosa poderia alterar o `.env` ou ligar o bot. Como não vamos portar o painel, o risco não nos afeta. |
| R14 | **Preso ao Windows.** `.bat`, registro do Windows, janela posicionada fora da tela. | vários | Não roda em VPS Linux sem adaptação. |
| R15 | **Horário pelo relógio do computador**, sem fuso definido. | `config.py`, `db.py` | Em servidor fora do Brasil, o "horário ativo" fica errado. |

**Segredos:** procurei tokens, chaves e senhas em todos os arquivos do ZIP. **Não há nenhum** — o `.env.example` vem em branco. 👍

---

## 3. Comparação: atual × referência × proposta

| Aspecto | Seu projeto atual | Referência (ZIP) | Proposta |
|---|---|---|---|
| Destino | Discord, 1 canal | Telegram, 1 canal | Telegram, **N canais** com nichos |
| Organização | 1 arquivo | Pacote modular | Pacote modular com camadas e contratos |
| Plataformas | Mercado Livre | ML, Amazon, Shopee, AliExpress | ML, Amazon, Shopee (extensível) |
| Link de afiliado | ❌ Não tem | ✅ | ✅ API oficial quando existir; senão API interna do painel |
| Captura | Selenium + disfarce | APIs oficiais + scraping com disfarce | APIs oficiais; onde não houver, scraping com ritmo baixo e alertas |
| Duplicidade | Não funciona | SQLite, 7 dias | SQLite com histórico por canal |
| Cupons | ❌ | ❌ | ✅ Cadastro, validade e aviso de esgotado |
| Texto do post | Embed fixo | Modelo fixo | Seu padrão + chamadas geradas por IA |
| IA | ❌ | ❌ | ✅ Chamadas, classificação, relatório |
| Fila | ❌ | ❌ (`sleep`) | ✅ Fila persistente no banco |
| Segredos | No código | `.env` | `.env` validado ao iniciar |
| Logs / alertas | `print` | `logging` + alerta ao dono | `logging` em arquivo + alertas + sinal de vida |
| Métricas | ❌ | Contador total | Histórico de publicações e relatórios |
| Testes | ❌ | ❌ | ✅ pytest desde a primeira aula |
| Onde roda | Seu PC com tela | Seu PC com tela | Servidor Linux 24/7 (com tela virtual para o navegador) |
| Documentação | ❌ | README de uso | Documentação por fase (esta pasta `docs/`) |

---

## 4. Decisões registradas

### Decisão 1 — Mercado Livre: automatizar com a API interna do painel ✅ (decidido em 15/11/2026)

**Sua decisão:** automatizar totalmente. Regra geral para todas as plataformas: **se existir API oficial, usamos; se não existir, seguimos com API interna do painel e scraping**, como na referência. O projeto é de estudo pessoal, com a sua própria conta.

O que isso significa na prática:

- **Ofertas:** leitura da página `mercadolivre.com.br/ofertas` com navegador real (Playwright), como em `sources/mercadolivre.py`.
- **Links `meli.la`:** chamada à API interna do Linkbuilder, de dentro de uma página logada com a sua sessão.
- **Antes de portar**, a Fase 4 começa com uma pesquisa em fontes oficiais: se o ML tiver API autorizada para afiliados, ela entra no lugar.

**Riscos que você aceitou** (registrados para não serem esquecidos):

| Risco | Como vamos reduzir |
|---|---|
| Suspensão da conta de afiliado por uso automatizado | Ritmo baixo de acessos (poucas páginas por ciclo, pausas entre elas), nada de acessos paralelos |
| Quebra quando o ML mudar o layout ou a API interna (aconteceu duas vezes em 2026, segundo os comentários da referência) | Testes com HTML salvo, log claro de "0 ofertas parseadas" e alerta no seu privado |
| Sessão de login expira | Detecção automática e alerta pedindo novo login |
| Uma falha do ML derrubar o resto | A fonte do ML fica isolada: se cair, Shopee e Amazon continuam |
| O ML bloqueia navegador invisível, então é preciso "tela" | No servidor Linux usaremos uma tela virtual (Xvfb). Detalhes na Fase 9 |

Nenhuma dessas proteções garante que a conta não será bloqueada.

### Decisão 2 — Amazon: API oficial primeiro, scraping como reserva ✅

Pela mesma regra: a Creators API é usada quando a conta for elegível; enquanto não for, entra o scraping das páginas de busca, como na referência. O link de afiliado usa a sua tag nos dois casos. O contrato de Associados proíbe coleta automatizada, então vale o mesmo aviso de risco de conta.

### Decisão 3 — Limpeza da pasta ✅ (feita em 15/11/2026)

- Apagados: `temp/`, `package.json`, `package-lock.json`, `chromedriver.exe` e a pasta de cache `__pycache__/`.
- O bot do Discord foi movido para `legado/` (`legado/main.py` e `legado/config.py`), preservado para consulta. Para rodá-lo, entre na pasta `legado/` antes.
- `mercado_livre.html` e `promocoes.json` continuam na pasta, mas saíram do controle do Git.
- O `.gitignore` foi reescrito. Antes ele ignorava qualquer arquivo chamado `config.py`, o que esconderia do Git o nosso futuro `ofertas/config.py`; agora ignora só `legado/config.py`, que contém o token.

As alterações estão preparadas no Git, mas **ainda não foram commitadas**.

---

Próximo documento: [02 — Arquitetura e plano](02-arquitetura-e-plano.md).
