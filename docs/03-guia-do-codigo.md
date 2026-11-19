# 03 — Guia do código

Explicação resumida de cada arquivo do **gabarito** (`gabarito/ofertas/`): o que faz, por que existe e de onde veio. Serve de mapa do que você vai construir nas aulas e de consulta depois de tentar.

## O caminho de uma oferta

```
fontes/  →  processamento  →  fontes (link)  →  ia + mensagens  →  banco (fila)  →  publicador
 busca       valida, filtra     gera o link       monta o texto      guarda a pauta    envia ao
             e escolhe          de afiliado       do post                              Telegram
```

Quem coordena tudo isso é o `pipeline.py`. Quem dispara o pipeline de tempos em tempos e recebe seus comandos é o `bot.py`.

## Arquivos, um a um

### Base

| Arquivo | O que faz | Conceito que vale aprender |
|---|---|---|
| [`config.py`](../gabarito/ofertas/config.py) | Lê o `.env` (segredos) e o `config.yaml` (ajustes) e devolve um objeto `Config`. Se faltar algo obrigatório, para o programa com mensagem clara. | **Falhar cedo**: melhor o bot recusar-se a ligar do que quebrar horas depois. A função recebe um dicionário, o que permite testá-la sem tocar no `.env` real. |
| [`modelos.py`](../gabarito/ofertas/modelos.py) | Define `Oferta` e `Cupom`. | **Ficha padrão**: toda loja devolve o mesmo formato, então o resto do sistema não precisa saber de qual loja veio. `@dataclass` cria a classe sem você escrever o `__init__`. |
| [`utils.py`](../gabarito/ofertas/utils.py) | Funções pequenas: converter `"R$ 1.234,56"` em número, formatar preço, checar horário ativo. | **Função pura**: mesma entrada, mesma saída, sem depender de nada externo. São as mais fáceis de testar. |
| [`logs.py`](../gabarito/ofertas/logs.py) | Registra os eventos no terminal e em `dados/logs/ofertas.log`. | O arquivo "gira": guarda no máximo 5 arquivos de 1 MB, então nunca enche o disco. |

### Fontes de ofertas — pasta [`fontes/`](../gabarito/ofertas/fontes/)

| Arquivo | O que faz | Método |
|---|---|---|
| [`base.py`](../gabarito/ofertas/fontes/base.py) | O **contrato**: toda fonte precisa ter `buscar_ofertas()`, `converter(url)`, `e_link(url)` e `pendencia()`. | Classe abstrata: se uma fonte esquecer um método, o Python acusa na hora. |
| [`shopee.py`](../gabarito/ofertas/fontes/shopee.py) | Busca ofertas e gera links. | **API oficial** de afiliados. Cada chamada é assinada com SHA-256 (função `assinar`). |
| [`amazon.py`](../gabarito/ofertas/fontes/amazon.py) | Busca ofertas e gera links com a sua tag. | **API oficial** (Creators API) quando a conta é elegível; senão, lê as páginas de busca no navegador. Troca sozinho. |
| [`mercadolivre.py`](../gabarito/ofertas/fontes/mercadolivre.py) | Lê a página de ofertas e gera links `meli.la`. | Navegador logado + **API interna** do Linkbuilder. Não oficial: veja os [riscos](01-diagnostico.md#4-decisões-registradas). |
| [`navegador.py`](../gabarito/ofertas/fontes/navegador.py) | Abre o Chrome com um perfil salvo (é onde fica o login). | Compartilhado por Mercado Livre e Amazon. |
| [`__init__.py`](../gabarito/ofertas/fontes/__init__.py) | Lista as fontes e descobre de qual loja é um link. | Para adicionar uma loja: crie a classe e inclua-a em `criar_fontes`. |

Em cada fonte, a **leitura dos dados** (`parse_card`, `no_para_oferta`, `item_para_oferta`) é uma função separada do **acesso à internet**. Por isso conseguimos testar a leitura com um HTML de exemplo, sem abrir navegador.

### Processamento e texto

| Arquivo | O que faz | Detalhe importante |
|---|---|---|
| [`processamento.py`](../gabarito/ofertas/processamento.py) | `validar` (tem título, preço, link? desconto plausível?), `filtrar` (desconto mínimo, faixa de preço, palavras bloqueadas, já publicada?) e `escolher` (as N melhores, alternando lojas). | Desconto acima de 95% é tratado como erro de dado e descartado. |
| [`ia.py`](../gabarito/ofertas/ia.py) | Pede à IA a chamada ("PRECIN NO RESERVA ROMA 🤯"), um nome curto e a categoria. | A resposta é **conferida pelo código**: chamada com número, preço, "%" ou promessa não verificada é recusada; o nome só pode usar palavras do título original. Se reprovar, ou se a IA cair, usa uma chamada pronta. |
| [`mensagens.py`](../gabarito/ofertas/mensagens.py) | Monta o texto final no padrão do canal. | Preço, cupom e link são colocados aqui, a partir dos dados. **A IA nunca escreve números.** |

### Persistência e publicação

| Arquivo | O que faz | Detalhe importante |
|---|---|---|
| [`banco.py`](../gabarito/ofertas/banco.py) | Banco SQLite com três tabelas: `ofertas`, `fila` e `cupons`. | A `fila` é a pauta **e** o histórico. Cada linha passa por `rascunho → pendente → enviada` (ou `falhou` após 3 tentativas). |
| [`publicador.py`](../gabarito/ofertas/publicador.py) | Envia foto com legenda; se a foto for recusada, envia só o texto. | "Degradar em vez de quebrar". |
| [`pipeline.py`](../gabarito/ofertas/pipeline.py) | Coordena o fluxo em duas metades: `coletar_e_enfileirar` e `publicar_proximo`. | As metades só se falam pela fila do banco. Se o programa cair, a pauta continua lá. A falha de uma loja ou de um canal não derruba os outros. |
| [`bot.py`](../gabarito/ofertas/bot.py) | Agenda as duas metades e responde aos seus comandos no privado. | Só o dono (`TELEGRAM_OWNER_ID`) comanda. |
| [`__main__.py`](../gabarito/ofertas/__main__.py) | Comandos de terminal (`python -m ofertas ...`). | É aqui que as peças são montadas e entregues umas às outras. |

## De onde veio cada parte

| Nosso arquivo | Arquivo da referência | O que mudou |
|---|---|---|
| `config.py` | `config.py` | Validação obrigatória; vários canais; sem objeto global |
| `modelos.py` | `models.py` | Novos campos: `pagamento`, `categoria`; classe `Cupom` |
| `fontes/shopee.py` | `sources/shopee.py` | Virou classe; termo de busca escapado com `json.dumps`; `httpx` no lugar de `requests` |
| `fontes/amazon.py` | `sources/amazon.py` | Virou classe; estado (token, rodízio) guardado no objeto |
| `fontes/mercadolivre.py` | `sources/mercadolivre.py` | Virou classe; detecta "Pix"; interrompe a coleta ao ver captcha; erro próprio para sessão expirada |
| `processamento.py` | `pipeline.py` (filtrar, escolher) | Nova etapa `validar` |
| `mensagens.py` | `formatter.py` | Reescrito no seu padrão de post; cupom; aviso de esgotado |
| `banco.py` | `db.py` | De 1 tabela para 3; fila persistente; cupons; métricas |
| `publicador.py` | `telegram_poster.py` | Sem botão (o link vai no texto, como nos seus exemplos) |
| `pipeline.py` | `pipeline.py` | Dividido em coleta e publicação, com fila no meio; vários canais |
| `bot.py` | `bot_interativo.py` | Prévias guardadas no banco; comandos de cupom |
| `ia.py`, `logs.py`, `tests/` | — | Novos |

Ficaram de fora: AliExpress, o painel web e os arquivos `.bat` (motivos no [diagnóstico](01-diagnostico.md#24-funcionalidades-uma-a-uma)).

## Testes

Rode com `python -m pytest`. São 63 testes, nenhum acessa a internet.

| Arquivo | O que garante |
|---|---|
| `test_config.py` | Configuração válida carrega; inválida falha com mensagem clara |
| `test_utils.py` | Conversão e formatação de preços; horário ativo |
| `test_mensagens.py` | Os **três exemplos** do seu padrão saem exatamente iguais |
| `test_processamento.py` | Dados incompletos são reprovados; filtros e seleção funcionam |
| `test_banco.py` | Duplicidade bloqueada; fila sobrevive a reinício; desiste após 3 falhas; cupons |
| `test_ia.py` | Chamada com preço é recusada; IA fora do ar não para a operação |
| `test_fontes.py` | Leitura do HTML do ML e da Amazon; assinatura e itens da Shopee |
| `test_pipeline.py` | Fluxo completo; canal com erro não impede os outros; cupom entra no post |

Dois truques usados nos testes: **objetos falsos** (`BotFalso`, `ClienteFalso`, `FonteFalsa`) que imitam o Telegram, a IA e uma loja; e **`tmp_path`**, uma pasta temporária que o pytest cria e apaga, para o banco de teste nunca tocar no banco real.

## O que ainda não foi testado de verdade

Os testes cobrem a lógica, mas as integrações externas só podem ser validadas com as suas credenciais:

| Integração | Como validar |
|---|---|
| Telegram | `python -m ofertas run` e mandar `/start` ao bot |
| Shopee | `python -m ofertas testar shopee` |
| Amazon | `python -m ofertas testar amazon` |
| Mercado Livre | `python -m ofertas ml-login` e depois `python -m ofertas testar ml` |
| IA | `python -m ofertas converter <link>` com `ANTHROPIC_API_KEY` preenchida |

Os seletores de HTML e a API interna do Mercado Livre vieram do projeto de referência; se o site tiver mudado desde então, é nesses dois testes (`testar ml`, `testar amazon`) que vai aparecer.
