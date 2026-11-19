# 06 — Aula 02: a ficha `Oferta` e o `Cupom`

**Você escreve o código.** Eu explico, você digita, roda e me mostra o resultado. O código pronto está em [`gabarito/ofertas/modelos.py`](../gabarito/ofertas/modelos.py) — use só para conferir depois de tentar.

## O que você vai construir

O arquivo `ofertas/modelos.py`, com duas "fichas":

| Ficha | Para quê |
|---|---|
| `Oferta` | Um produto em promoção: loja, título, preços, link de afiliado, imagem… |
| `Cupom` | Um código de desconto de uma loja, com validade opcional. |

## Por que isso importa

Cada loja entrega os dados de um jeito diferente: a Shopee manda JSON, o Mercado Livre manda HTML, a Amazon manda outra coisa. Se o resto do bot tivesse que entender os três formatos, cada mudança numa loja quebraria tudo.

A solução: **toda loja converte os seus dados para a mesma ficha `Oferta`**. Daí para frente, o filtro, a IA, o banco e o Telegram só conhecem a `Oferta`. É como um formulário padrão: não importa de onde veio a informação, ela chega nos mesmos campos.

```
Shopee ─┐
Amazon ─┼─→  Oferta  ─→  filtro → IA → mensagem → Telegram
ML ─────┘
```

## Passo 0 — Fechar a Aula 01

Falta um teste na Aula 01: sem ele, se alguém tirasse o `02d` de `formatar_preco`, `10.05` sairia `"R$10,5"` e nenhum teste avisaria. Acrescente em `tests/test_utils.py`:

```python
def test_preco_centavos_com_um_digito():
    assert formatar_preco(10.05) == "R$10,05"
```

Rode `python -m pytest tests` → `9 passed`.

## Passo 1 — O teste primeiro

Crie `tests/test_modelos.py`:

```python
from ofertas.modelos import Oferta


def test_oferta_guarda_os_dados():
    o = Oferta(plataforma="mercadolivre", id_produto="MLB123", titulo="Tênis Reserva Roma")
    assert o.titulo == "Tênis Reserva Roma"
    assert o.preco is None


def test_uid_junta_loja_e_produto():
    o = Oferta(plataforma="amazon", id_produto="B0ABC", titulo="Echo Dot")
    assert o.uid == "amazon:B0ABC"
```

Rode. Vai dar `ModuleNotFoundError` — você já sabe o que significa: o arquivo `ofertas/modelos.py` ainda não existe.

## Passo 2 — A classe `Oferta`

Crie `ofertas/modelos.py` e digite:

```python
from dataclasses import dataclass


@dataclass
class Oferta:
    plataforma: str                     # "mercadolivre" | "amazon" | "shopee"
    id_produto: str
    titulo: str
    url_afiliado: str = ""              # vazio até o link de afiliado ser gerado
    url_produto: str = ""
    preco: float | None = None
    preco_original: float | None = None
    desconto_pct: int | None = None     # informado pela loja, quando houver
    imagem: str | None = None
    pagamento: str | None = None        # "Pix" quando o preço é no Pix
    extra: str | None = None            # avaliação, frete grátis etc.
    categoria: str | None = None        # preenchida pela IA

    @property
    def uid(self) -> str:
        return f"{self.plataforma}:{self.id_produto}"
```

| Trecho | O que faz |
|---|---|
| `class Oferta:` | Cria um **molde**. Cada oferta real é uma "cópia preenchida" desse molde (um **objeto**). |
| `@dataclass` | Escreve sozinho o código chato: o construtor que recebe os campos, a comparação entre objetos e o texto que aparece no `print`. Sem ele seriam ~20 linhas a mais. |
| `plataforma: str` | Campo **obrigatório** (sem `=`): toda oferta precisa dizer de qual loja veio. |
| `preco: float \| None = None` | Campo **opcional**: pode ser um número ou `None` (vazio). Se ninguém informar, começa `None`. |
| Ordem dos campos | Obrigatórios **antes** dos opcionais. O Python exige isso. |
| `@property` | Transforma o método num "campo calculado": você escreve `o.uid`, sem parênteses, e ele é calculado na hora. |
| `self` | É "esta oferta aqui". `self.plataforma` é a plataforma desta oferta. |

**Por que `uid`?** O mesmo número de produto pode existir em duas lojas. Juntando loja + produto (`"amazon:B0ABC"`), temos um identificador que nunca se repete. É ele que o banco vai usar, na Aula 06, para não postar o mesmo produto duas vezes.

Rode → `11 passed`.

## Passo 3 — Sua vez: o `desconto`

O post mostra o desconto. Às vezes a loja informa (`desconto_pct`); às vezes só temos os dois preços e precisamos calcular. Acrescente os testes em `tests/test_modelos.py`:

```python
def test_desconto_informado_pela_loja():
    o = Oferta(plataforma="shopee", id_produto="1", titulo="Fone", desconto_pct=40)
    assert o.desconto == 40


def test_desconto_calculado_pelos_precos():
    o = Oferta(plataforma="mercadolivre", id_produto="1", titulo="Tênis",
               preco=177.0, preco_original=399.0)
    assert o.desconto == 56


def test_desconto_sem_dados():
    o = Oferta(plataforma="amazon", id_produto="1", titulo="Livro", preco=50.0)
    assert o.desconto is None


def test_desconto_preco_original_menor_nao_vale():
    o = Oferta(plataforma="amazon", id_produto="1", titulo="Livro",
               preco=50.0, preco_original=40.0)
    assert o.desconto is None
```

Escreva dentro da classe uma `@property` chamada `desconto` que devolve `int | None`. Roteiro:

1. Se `self.desconto_pct` tiver valor, devolva ele (a loja sabe melhor).
2. Se tiver `preco` **e** `preco_original` **e** o original for maior, calcule: `round(100 * (1 - preco / preco_original))`. Conferindo: `1 - 177/399 = 0,556` → `55,6` → `56`.
3. Senão, devolva `None`.

Lembre de usar `self.` antes de cada campo. Rode até ver `15 passed`.

O último teste existe porque dados de loja às vezes vêm trocados. Um "desconto" negativo no post seria vergonhoso.

## Passo 4 — O `Cupom`

Mais simples. No topo de `ofertas/modelos.py`, acrescente:

```python
from datetime import datetime
```

E no final do arquivo:

```python
@dataclass
class Cupom:
    codigo: str
    plataforma: str
    valido_ate: datetime | None = None
```

`datetime` é o tipo do Python para data + hora. `None` aqui quer dizer "sem prazo de validade". O teste:

```python
from datetime import datetime
from ofertas.modelos import Cupom, Oferta   # troque a primeira linha do arquivo por estas duas


def test_cupom_com_validade():
    c = Cupom(codigo="TODOSITE1511", plataforma="mercadolivre",
              valido_ate=datetime(2026, 11, 30, 23, 59))
    assert c.valido_ate.day == 30


def test_cupom_sem_validade():
    c = Cupom(codigo="FRETE10", plataforma="shopee")
    assert c.valido_ate is None
```

Resultado esperado: **`17 passed`**.

## Conferir e avançar

Compare com [`gabarito/ofertas/modelos.py`](../gabarito/ofertas/modelos.py). Quando terminar, me mande a saída do `python -m pytest tests`. A próxima aula é `mensagens.py`: transformar uma `Oferta` no post do seu canal.
