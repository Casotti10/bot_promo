# 02 — Arquitetura proposta e plano de desenvolvimento (Fase 2)

> ```Atualizado em 15/11/2026 com as [decisões registradas no diagnóstico](01-diagnostico.md#4-decisões-registradas): automação total, usando API oficial quando existir e, quando não existir, API interna do p```ainel e scraping.

## 1. A ideia em uma analogia

Pense em uma **redação de jornal de ofertas**:

| Na redação | No sistema | Módulo |
|---|---|---|
| Repórteres trazem notícias de lugares diferentes | Cada plataforma entrega produtos | `fontes/` |
| Toda notícia chega na mesma ficha padrão | Todo produto vira uma `Oferta` | `modelos.py` |
| O editor confere os fatos e descarta o que é fraco | Validação, filtros e seleção | `processamento/` |
| O redator escreve a manchete | A IA cria a chamada comercial | `ia/` |
| O diagramador monta a página no padrão do jornal | O código monta o texto final com os números reais | `mensagens/` |
| A pauta diz o que sai e em que horário | Fila de publicações | `fila/` |
| O entregador leva a cada banca | Envio a cada canal do Telegram | `telegram/` |
| O arquivo guarda tudo o que já saiu | Banco de dados | `banco/` |
| O chefe é avisado quando algo dá errado | Logs e alertas | `monitoramento/` |

Regra de ouro da redação: **o redator (IA) escreve a manchete, mas nunca os números.** Preço, desconto, cupom e link são sempre colocados pelo código, vindos dos dados reais. É assim que garantimos "não inventar preços".

## 2. Fluxo de dados

```
 ┌─────────────┐  ┌──────────────────┐  ┌───────────────────┐  ┌──────────────────────┐
 │ Shopee API  │  │ Amazon: API ou   │  │ Mercado Livre:    │  │ Link colado por você │
 │  (oficial)  │  │ scraping reserva │  │ página de ofertas │  │   (qualquer loja)    │
 └──────┬──────┘  └────────┬─────────┘  └─────────┬─────────┘  └──────────┬───────────┘
        └──────────────────┼──────────────────────┘                       │
                           ▼                                              │
        1. CAPTURA (fontes/)                                              │
                 ▼                              │
        2. VALIDAÇÃO  ── dados incompletos? ──► descarta e registra no log
                 ▼
        3. FILTROS E SELEÇÃO ── já publicada? desconto baixo? ──► descarta
                 ▼
        4. LINK DE AFILIADO  ◄── (ML: API interna do Linkbuilder) ◄───────┘
                 ▼
        5. CUPOM (existe cupom ativo cadastrado para esta oferta?)
                 ▼
        6. IA: chamada comercial + categoria
                 ▼
        7. MONTAGEM da mensagem no seu padrão
                 ▼
        8. FILA (banco)  ── uma entrada por canal de destino
                 ▼
        9. PUBLICADOR ── respeita ritmo e horário ──► Telegram
                 ▼
       10. REGISTRO (publicações, erros) ──► relatórios e alertas
```

A fila no passo 8 é o que dá robustez: se o programa cair entre o passo 8 e o 9, ao voltar ele continua de onde parou, porque a pauta está gravada no banco e não na memória.

## 3. Estrutura de pastas

A estrutura implementada está no [README](../README.md#estrutura), e a explicação de cada arquivo, no [guia do código](03-guia-do-codigo.md).

Em relação ao desenho inicial, três simplificações: `processamento`, `ia` e `mensagens` são arquivos únicos em vez de pastas (cada um tem menos de 200 linhas); a fila fica dentro de `banco.py`; e os canais vêm do `.env` em vez de uma tabela própria. As tabelas do banco são três: `ofertas`, `fila` (que também serve de histórico de publicações) e `cupons`.

## 4. Como os módulos conversam

Duas regras simples mantêm o projeto organizado:

1. **As dependências apontam para dentro.** `fontes`, `telegram` e `ia` (que falam com o mundo externo) conhecem `modelos`. `modelos` não conhece ninguém. Assim, trocar a API da Shopee não afeta o formatador.
2. **Quem precisa de algo recebe pronto.** Em vez de cada módulo ler o `.env` por conta própria (como na referência, com o `config` global), a configuração é lida uma vez no início e entregue a quem precisa. Isso se chama *injeção de dependência* e é o que torna o código testável: no teste, entregamos uma configuração falsa.

## 5. Banco de dados

**Escolha: SQLite.** É um banco que vive em um único arquivo e já vem com o Python. Para o nosso volume (centenas de ofertas por dia) sobra capacidade, não custa nada e o backup é copiar um arquivo. PostgreSQL só faria sentido com vários programas escrevendo ao mesmo tempo, o que não é o nosso caso.

| Tabela | Guarda | Para quê |
|---|---|---|
| `ofertas` | Produto, loja, preços, link de afiliado, categoria, data da coleta | Histórico do que foi encontrado |
| `fila` | Oferta, canal, texto pronto, chamada, situação, tentativas, id da mensagem, datas | A pauta de publicação, o histórico (anti-duplicidade) e a base das métricas |
| `cupons` | Código, loja, validade, situação (ativo / esgotado) | Anexar cupom aos posts e avisar quando esgotar |

## 6. Tecnologias e justificativas

| Necessidade | Escolha | Por quê | Alternativa descartada |
|---|---|---|---|
| Linguagem | Python 3.12 | Já instalado no seu ambiente; versão estável e bem suportada | 3.14 (a referência fixa essa versão sem necessidade) |
| Telegram | `python-telegram-bot` v21+ | Biblioteca madura para a API oficial de bots; já inclui agendador | `aiogram` (igualmente boa, mas a referência já mostra o caminho com a outra) |
| Agendamento | `JobQueue` da própria biblioteca do Telegram | Zero dependência extra | Celery, cron externo (complexidade sem ganho) |
| Fila | Tabela no SQLite | Persistente e simples; nosso volume é baixo | Redis, RabbitMQ (seria mais um serviço para manter) |
| Banco | SQLite (`sqlite3` nativo) | Ver seção 5 | PostgreSQL, ORM |
| Chamadas HTTP | `httpx` | Já vem instalada junto com a biblioteca do Telegram; funciona em modo assíncrono | `requests` (só síncrona) |
| Navegador automatizado | `playwright` com o Google Chrome instalado | Necessário para o Mercado Livre e para a reserva da Amazon; guarda a sessão de login em um perfil | Selenium (seu projeto atual; mais frágil e sem perfil persistente simples) |
| Leitura de HTML | `beautifulsoup4` + `lxml` | Extrair os dados dos cartões de produto de forma legível e testável com HTML salvo | Ler tudo pelo navegador, elemento a elemento (lento, como no seu `main.py`) |
| Segredos | `python-dotenv` + `.env` | Padrão de mercado, já instalado | Segredos no código |
| Ajustes | `PyYAML` + `config.yaml` | Legível e aceita comentários | JSON (não aceita comentários) |
| Testes | `pytest` | Padrão da comunidade Python; testes curtos e legíveis | `unittest` (mais verboso) |
| IA | API da Anthropic (Claude); modelo configurável em `config.yaml` | Uma chamada curta por oferta; dá para trocar qualidade por custo mudando uma linha | Rodar modelo local (exigiria servidor caro) |
| Dependências | `pip` + `requirements.txt` | O mais simples de aprender primeiro | `uv` (ótimo; podemos migrar depois) |
| Produção | VPS Linux + `systemd` + tela virtual (Xvfb) | Controle total, custo baixo, reinício automático. A tela virtual existe porque o ML bloqueia navegador invisível | Hospedagens "serverless" e plataformas sem navegador (não rodam o Chrome) |

Ainda serão **pesquisados com fontes atuais**: a comparação de hospedagens e preços (Fase 9) e vídeos de apoio para cada integração. Sobre o Mercado Livre, a pesquisa de 15/11/2026 não encontrou API oficial pública para afiliados gerarem links; as ferramentas existentes usam a sessão do navegador, como a referência.

### O que ficou de fora de propósito

- **Selenium:** substituído pelo Playwright.
- **Docker:** útil, mas não essencial para um único processo. Reavaliamos na Fase 9.
- **Painel web:** o próprio Telegram será o seu painel (comandos no privado do bot).

## 7. Onde a IA entra — e onde não entra

| Tarefa | Usa IA? | Motivo |
|---|---|---|
| Criar a chamada ("JÁ TOMOU A TUA HOJE?") | ✅ | Criatividade e variação são o ponto forte da IA |
| Encurtar e limpar o nome do produto | ✅ | Títulos de marketplace são longos e poluídos |
| Classificar a categoria | ✅ | Simples e barato; direciona a oferta ao canal certo |
| Resumo de desempenho em linguagem natural | ✅ (Fase 10) | Transforma números em leitura rápida |
| Preço, desconto, cupom, link | ❌ Nunca | Vêm dos dados; o código insere |
| Decidir se um cupom é válido | ❌ | É um fato a verificar, não a "achar" |
| Evitar duplicidade | ❌ | O banco resolve com exatidão |

Proteção extra: depois que a IA responde, o código confere a chamada (tamanho, ausência de números e de "R$", ausência de promessas como "menor preço do Brasil"). Se reprovar, usa uma chamada padrão. Se a IA estiver fora do ar, o post sai com a chamada padrão — a operação não para.

## 8. Cupons: o que é possível de verdade

Seu Exemplo 2 ("❌ Cupom esgotado!") exige honestidade técnica: **não conheço uma API pública que informe se um cupom de site inteiro ainda tem saldo.** Portanto:

- **Cadastro:** você informa o cupom ao bot (`/cupom TODOSITE1511 mercadolivre validade`). O bot passa a anexá-lo às ofertas daquela loja.
- **Esgotou:** você avisa (`/esgotado TODOSITE1511`) e o bot publica o aviso do Exemplo 2 em todos os canais e para de usar o cupom. Cupons com validade vencem sozinhos.
- **Automático onde houver dado oficial:** se a API de uma plataforma informar cupons ou ofertas com prazo, usamos.

Assim cumprimos a regra "não anunciar cupons sem verificar sua validade": só entra cupom que você confirmou.

## 9. Plano de desenvolvimento

Cada etapa tem um **critério de validação**. Situação em 15/11/2026: o código das fases 3 a 7 está escrito e a lógica está coberta por testes; os critérios que dependem de credenciais reais (mensagem chegar ao canal, `testar shopee`, `testar ml` etc.) ainda precisam ser validados por você — veja [como colocar no ar](04-como-colocar-no-ar.md).

| Fase | Entrega | Critério de validação | Base na referência |
|---|---|---|---|
| **1. Análise** ✅ | [Diagnóstico](01-diagnostico.md) | Você leu e respondeu às 3 decisões | — |
| **2. Arquitetura** ✅ | Este documento | Você aprovou a estrutura | — |
| **3. Telegram** | | | |
| 3.1 Fundação | Ambiente, `.env`, `config.py`, testes | Testes passando | `config.py`, `.env.example` |
| 3.2 Primeiro envio | Bot criado no BotFather; mensagem de texto no canal | Mensagem aparece no canal | `telegram_poster.py` |
| 3.3 Post completo | Modelo `Oferta` + formatador no seu padrão + foto | Os 3 exemplos do seu padrão reproduzidos | `models.py`, `formatter.py` |
| 3.4 Vários canais | Envio a N canais com tratamento de erro | Um canal com erro não impede os outros | — (novo) |
| **4. Afiliados** | | | |
| 4.1 Shopee | Busca e link pela API oficial | `testar shopee` lista ofertas com link | `sources/shopee.py` |
| 4.2 Amazon | API oficial quando elegível; scraping da busca como reserva; link com tag | `testar amazon` lista ofertas; link sai com a sua tag | `sources/amazon.py` |
| 4.3 Mercado Livre | Pesquisa de API oficial; login único; leitura da página de ofertas; links pela API interna do Linkbuilder | `testar ml` lista ofertas; link `meli.la` com a sua etiqueta; sessão expirada gera alerta | `sources/mercadolivre.py` |
| **5. Processamento** | Validação, filtros, seleção, banco, anti-duplicidade | Oferta repetida é bloqueada; oferta sem preço é descartada | `pipeline.py`, `db.py` |
| **6. IA** | Gerador de chamadas, validador, classificador | Chamada reprovada cai no padrão; nenhum número vem da IA | — (novo) |
| **7. Automação** | Fila, ritmo, horário ativo, cupons, bot de administração | Derrubar o programa no meio e ele retoma a fila | `bot_interativo.py`, `config.dentro_do_horario` |
| **8. Testes** | Testes de integração e de recuperação de falhas | Suíte completa passando | — (novo) |
| **9. Deploy** | Servidor, `systemd`, logs, backup, atualização | Bot sobrevive a reinício do servidor | `run.bat` (a ideia de reiniciar sozinho) |
| **10. Crescimento** | Relatórios, novos canais, AliExpress | Relatório semanal no seu privado | `sources/aliexpress.py`, `nichos.py` |

Os testes não ficam só na Fase 8: **toda aula já traz seus testes**. A Fase 8 acrescenta os testes que envolvem o sistema inteiro.

## 10. Regras de operação que já adotamos

- **Aviso de afiliado:** a descrição de cada canal informará que os links geram comissão (exigência dos programas, em especial o da Amazon).
- **Ritmo de envio:** o Telegram limita mensagens por segundo; a fila respeitará esses limites em vez de testá-los.
- **Só canais seus:** o bot publica apenas onde foi adicionado como administrador por você.
- **API oficial sempre em primeiro lugar:** cada integração da Fase 4 começa pesquisando a API oficial; scraping e API interna entram só onde ela não existe ou não está liberada para a sua conta.
- **Scraping educado:** poucas páginas por ciclo, pausas entre acessos, um acesso por vez e parada imediata ao detectar captcha ou bloqueio (com alerta para você).
- **Sem promessa de imunidade:** essas práticas reduzem o risco, mas o uso automatizado do Mercado Livre e da Amazon pode levar ao bloqueio da conta de afiliado. É um risco que você aceitou conscientemente.

---

Próximo documento: [03 — Guia do código](03-guia-do-codigo.md).
