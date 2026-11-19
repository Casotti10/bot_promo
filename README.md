# Plataforma de Afiliados para Telegram

Bot em Python que encontra ofertas no Mercado Livre, Amazon e Shopee, gera os seus links de afiliado, cria a chamada comercial com IA e publica automaticamente nos seus canais do Telegram.

```
PRECIN NO RESERVA ROMA 🤯

Tênis Reserva Roma

De: R$399 | Por: R$177 no Pix 👑

⚠️ Cupom: TODOSITE1511

Link: https://meli.la/16RkQdx
```

## Como este projeto funciona

Você escreve o código, aula por aula, nas pastas `ofertas/` e `tests/`. A pasta `gabarito/` tem uma versão completa e testada, para conferir depois de tentar.

**Aula atual: Aula 03 (ainda não escrita).**

### Onde paramos (18/11/2026)

Pausa: o Lucas encerrou o dia e continua em outra data.

- Aulas 01 e 02 concluídas e revisadas; `python -m pytest tests` → **20 passed**.
- Depois da revisão entraram três testes a mais, além dos 17 da aula: `desconto_pct` só vale entre 1 e 99 (fora disso, calcula pelos preços) e `parse_preco_br` devolve `None` para texto com dois preços. A pedido dele, esse código foi escrito pelo Claude, não por ele.
- **Ao retomar:** escrever a [Aula 03](#roteiro-das-aulas) (`mensagens.py`) em `docs/07-aula-03-...`. Ele digita o código; o Claude ensina e confere.

## Roteiro das aulas

| Aula | Você constrói | Situação |
|---|---|---|
| 01 | `utils.py` — preços e o primeiro teste | ✅ Concluída |
| 02 | `modelos.py` — a ficha `Oferta` e o `Cupom` | ✅ [Concluída](docs/06-aula-02-modelos.md) |
| 03 | `mensagens.py` — o post no seu padrão | |
| 04 | `config.py` — `.env` e `config.yaml` | |
| 05 | `publicador.py` — primeiro post no Telegram | |
| 06 | `banco.py` — duplicidade, fila e cupons | |
| 07 | `processamento.py` — validar, filtrar, escolher | |
| 08 | `fontes/` — contrato e Shopee | |
| 09 | `fontes/amazon.py` | |
| 10 | `fontes/mercadolivre.py` | |
| 11 | `ia.py` — chamada comercial com IA | |
| 12 | `pipeline.py` — juntar tudo | |
| 13 | `bot.py` e `__main__.py` — agendamento e comandos | |
| 14 | Deploy 24/7 | |

Cada aula é escrita depois que você termina a anterior.

## Documentação

| # | Documento | Para quê |
|---|---|---|
| 01 | [Diagnóstico](docs/01-diagnostico.md) | Análise do bot antigo (Discord) e do projeto de referência; decisões tomadas e riscos |
| 02 | [Arquitetura e plano](docs/02-arquitetura-e-plano.md) | Como o sistema foi pensado, tecnologias escolhidas e fases do projeto |
| 03 | [Guia do código](docs/03-guia-do-codigo.md) | O que cada arquivo faz, de onde veio e o que os testes garantem |
| 04 | [Como colocar no ar](docs/04-como-colocar-no-ar.md) | Configuração, comandos do bot e solução de problemas |
| 05 | [Aula 01 — preços](docs/05-aula-01-precos.md) | Primeira aula prática |
| 06 | [Aula 02 — modelos](docs/06-aula-02-modelos.md) | A ficha `Oferta` e o `Cupom` |

Os documentos 03 e 04 descrevem o código do gabarito.

## Estrutura

```
automação/
├── README.md              Este arquivo
├── docs/                  Documentação
├── .env.example           Modelo dos segredos (copie para .env)
├── config.yaml            Ajustes: intervalos, filtros, lojas ativas, modelo de IA
├── requirements.txt       Bibliotecas do projeto
├── ofertas/               O SEU código (você escreve nas aulas)
├── tests/                 Os SEUS testes
├── gabarito/              Versão completa para consulta (ofertas/ + tests/)
│   ├── __main__.py        Comandos de terminal
│   ├── config.py          Lê e valida .env + config.yaml
│   ├── modelos.py         Oferta e Cupom
│   ├── utils.py           Funções pequenas (preços, horário)
│   ├── fontes/            Uma fonte por loja
│   │   ├── base.py        O contrato das fontes
│   │   ├── shopee.py      API oficial
│   │   ├── amazon.py      API oficial + scraping de reserva
│   │   ├── mercadolivre.py Página de ofertas + API interna do Linkbuilder
│   │   └── navegador.py   Chrome com sessão salva
│   ├── processamento.py   Valida, filtra e escolhe as ofertas
│   ├── ia.py              Chamada comercial, nome curto e categoria
│   ├── mensagens.py       Monta o texto do post
│   ├── banco.py           SQLite: ofertas, fila e cupons
│   ├── publicador.py      Envia ao Telegram
│   ├── pipeline.py        Coordena coleta e publicação
│   ├── bot.py             Agendamento e comandos no privado
│   └── logs.py            Registro de eventos
│   └── tests/             63 testes automatizados
├── dados/                 Banco, logs e sessão do navegador (criada ao rodar; fora do Git)
└── legado/                Bot antigo do Discord, guardado para consulta
```

## Situação do gabarito

O seu código está na Aula 02. A tabela abaixo é sobre a versão pronta em `gabarito/`.

| Fase | Situação |
|---|---|
| 1. Análise | ✅ Concluída |
| 2. Arquitetura | ✅ Concluída |
| 3. Telegram | ✅ Código pronto — falta validar com o seu bot |
| 4. Lojas (Shopee, Amazon, Mercado Livre) | ✅ Código pronto — falta validar com as suas credenciais |
| 5. Processamento e seleção | ✅ Pronto e testado |
| 6. Inteligência Artificial | ✅ Código pronto — falta validar com a sua chave |
| 7. Fila, cupons e automação | ✅ Pronto e testado |
| 8. Testes | ✅ 63 testes de lógica; integrações reais ainda não validadas |
| 9. Deploy 24/7 | Pendente |
| 10. Relatórios e otimização | Pendente |

**O que foi testado:** toda a lógica interna, com 63 testes automatizados.
**O que não foi testado:** as conexões reais com Telegram, Shopee, Amazon, Mercado Livre e a IA, porque dependem das suas credenciais. A lista de como validar cada uma está no [guia do código](docs/03-guia-do-codigo.md#o-que-ainda-não-foi-testado-de-verdade).

## Decisões tomadas

| Data | Decisão |
|---|---|
| 15/11/2026 | **Automação total.** API oficial quando existir; senão, API interna do painel de afiliados e scraping (Mercado Livre e Amazon). Projeto de estudo pessoal, com conta própria; riscos registrados no [diagnóstico](docs/01-diagnostico.md#4-decisões-registradas). |
| 15/11/2026 | **Limpeza da pasta.** Sobras de Node.js apagadas; bot do Discord movido para `legado/`. |
| 15/11/2026 | **Você escreve o código, com aulas curtas.** O código que eu havia escrito inteiro foi movido para `gabarito/` e serve só de consulta. |
| 18/11/2026 | **Projeto de referência fora do Git.** `bot-ofertas-telegram.zip` está no `.gitignore`; no futuro será apagado da pasta. Antes de apagar, conferir se o [diagnóstico](docs/01-diagnostico.md) ainda precisa dele. |

## Princípios

- **Dados reais, sempre.** A IA escreve a chamada; preço, cupom e link vêm dos dados e são inseridos pelo código.
- **API oficial primeiro.** Onde não houver, API interna e scraping com ritmo baixo, falhas isoladas e alertas.
- **Segredos fora do código.** Tokens e chaves só no `.env`, que nunca vai para o Git.
- **Nada para por causa de uma peça.** Loja fora do ar, IA indisponível ou canal com erro não derrubam o resto.
