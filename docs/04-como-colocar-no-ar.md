# 04 — Como colocar no ar (no seu PC)

Passo a passo para ligar o bot pela primeira vez. Comece só com o Telegram e vá ligando as lojas uma a uma.

> **Este guia vale para o bot completo.** Enquanto você constrói o seu código pelas aulas, `python -m ofertas` ainda não funciona na raiz. Para rodar o gabarito, copie `.env` e `config.yaml` para dentro de `gabarito/` e execute os comandos a partir dessa pasta (`cd gabarito`).

## 1. Preparar o ambiente

No terminal do VS Code, na pasta do projeto:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
```

Resultado esperado: `63 passed`. As bibliotecas já foram instaladas no seu `.venv`; o `pip install` só é necessário em outra máquina.

## 2. Criar o bot e o canal no Telegram

1. No Telegram, fale com **@BotFather** → `/newbot` → escolha nome e @username → copie o **token**.
2. Crie um **canal de testes**. Em Administradores, adicione o seu bot com permissão de **publicar mensagens**.

## 3. Preencher o `.env`

Copie o modelo e abra para editar:

```powershell
Copy-Item .env.example .env -Force
code .env
```

Preencha por enquanto:

```text
TELEGRAM_BOT_TOKEN=<o token do BotFather>
TELEGRAM_CHAT_IDS=@seu_canal_de_testes
TELEGRAM_OWNER_ID=1
```

O `1` é provisório. Para descobrir os IDs reais:

```powershell
python -m ofertas run
```

No Telegram, mande `/id` ao seu bot no privado: ele responde o **seu user id**. Coloque esse número em `TELEGRAM_OWNER_ID`. Se o canal for privado, encaminhe um post dele ao bot (depois de corrigir o owner id) para ver o id do canal. Pare o bot com `Ctrl+C` e ligue de novo.

## 4. Conferir

```powershell
python -m ofertas check
```

Mostra o que está pronto e o que falta em cada loja.

## 5. Ligar as lojas

Preencha as credenciais no `.env` e teste cada uma **sem publicar nada**:

| Loja | O que preencher | Onde conseguir | Teste |
|---|---|---|---|
| Shopee | `SHOPEE_APP_ID`, `SHOPEE_APP_SECRET` | [affiliate.shopee.com.br](https://affiliate.shopee.com.br) → Open API (aprovação pode levar dias) | `python -m ofertas testar shopee` |
| Amazon | `AMAZON_TAG` (e, se tiver, as credenciais da Creators API) | [associados.amazon.com.br](https://associados.amazon.com.br) | `python -m ofertas testar amazon` |
| Mercado Livre | `ML_ETIQUETA` | [Linkbuilder](https://www.mercadolivre.com.br/afiliados/linkbuilder) → "Etiqueta em uso" | `python -m ofertas ml-login` e depois `python -m ofertas testar ml` |

O `ml-login` abre um Chrome separado: faça login, confira que o Linkbuilder aparece logado e **feche o navegador**. A sessão fica salva em `dados/ml_perfil`. Mercado Livre e Amazon precisam do **Google Chrome** instalado.

Para desligar uma loja, ponha `ativa: false` no bloco dela em `config.yaml`.

## 6. Ligar a IA (opcional)

Crie uma chave em [console.anthropic.com](https://console.anthropic.com) e preencha `ANTHROPIC_API_KEY`. Sem a chave, o bot funciona com chamadas prontas.

O modelo é escolhido em `config.yaml` (`ia.modelo`). Cada chamada usa poucas centenas de tokens; os preços de cada modelo estão comentados no próprio arquivo. Para gastar o mínimo, use `claude-haiku-5-5`.

Teste a prévia de um post, sem publicar:

```powershell
python -m ofertas converter "https://www.amazon.com.br/dp/XXXXXXXXXX"
```

## 7. Usar

```powershell
python -m ofertas run
```

O bot busca ofertas a cada 45 minutos, coloca as melhores na fila e publica uma a cada 2 minutos, entre 8h e 23h. Tudo isso se ajusta em `config.yaml`.

Comandos no privado do bot:

| Comando | O que faz |
|---|---|
| *colar um link* | Mostra a prévia do post com botões **Publicar** / **Descartar** |
| `/status` | Fila, canais e situação de cada loja |
| `/ciclo` | Busca ofertas agora |
| `/cupom CODIGO loja [dias]` | Cadastra um cupom; ele entra nos próximos posts da loja. Ex: `/cupom TODOSITE1511 mercadolivre 2` |
| `/esgotado CODIGO` | Desativa o cupom e publica o aviso de esgotado nos canais |
| `/cupons` | Lista os cupons ativos |
| `/id` | Mostra o id do chat |

O bot só anexa cupons que você cadastrou — é assim que ele garante não anunciar cupom sem validade conferida.

## Problemas comuns

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| `Configuração incompleta: ...` | Falta um dos três campos do Telegram no `.env` | Preencher o campo citado |
| Bot não publica no canal | Bot não é administrador, ou id do canal errado | Conferir administradores; ver `/status` e o log |
| Bot ignora seus comandos | `TELEGRAM_OWNER_ID` errado | Mandar `/id` e corrigir |
| `testar ml` acha 0 ofertas | Sessão expirou, ou o ML mudou o layout | Refazer `ml-login`; se persistir, os seletores estão em `fontes/mercadolivre.py` |
| Aviso "Mercado Livre parou de gerar links" | Sessão expirada | `python -m ofertas ml-login` |
| Amazon sem resultados | Bloqueio temporário do site | Aguardar; reduzir `requisicoes_por_ciclo` |
| Nada é publicado de madrugada | `horario_ativo` | Ajustar em `config.yaml` (`""` = 24h) |

O histórico completo fica em `dados/logs/ofertas.log`.

## Próximas etapas

- **Validar as integrações** com as suas credenciais (seção 5) — é o que falta testar de verdade.
- **Deploy 24/7 em servidor** (Fase 9): comparação de hospedagens, `systemd` e tela virtual para o Chrome.
- **Relatórios e otimização** (Fase 10).
