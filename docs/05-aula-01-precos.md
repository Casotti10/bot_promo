# 05 — Aula 01: preços e o seu primeiro teste

**Você escreve o código.** Eu explico, você digita, roda e me mostra o resultado. O código pronto está em [`gabarito/`](../gabarito/) — use só para conferir depois de tentar.

## O que você vai construir

Duas funções pequenas que o bot inteiro usa:

| Função | Entrada | Saída |
|---|---|---|
| `formatar_preco` | `399.0` | `"R$399"` |
| `parse_preco_br` | `"R$ 1.234,56"` | `1234.56` |

A primeira escreve o preço no post. A segunda lê o preço que vem do site da loja, que chega como texto.

## Por que começar por aqui

São **funções puras**: mesma entrada, mesma saída, sem internet, sem banco, sem Telegram. É o tipo de código mais fácil de testar, e é onde você aprende o ciclo que vai repetir no projeto todo:

```
escrever o teste  →  ver falhar  →  escrever o código  →  ver passar
```

## Passo 1 — Criar os arquivos

As pastas `ofertas/` e `tests/` já existem, vazias. Crie dentro delas quatro arquivos vazios:

```
ofertas/__init__.py
ofertas/utils.py
tests/__init__.py
tests/test_utils.py
```

O `__init__.py` vazio é o que diz ao Python "esta pasta é um pacote". Sem ele, `from ofertas.utils import ...` não funciona.

## Passo 2 — Escrever o teste primeiro

Em `tests/test_utils.py`, digite:

```python
from ofertas.utils import formatar_preco


def test_preco_sem_centavos():
    assert formatar_preco(399.0) == "R$399"


def test_preco_com_centavos():
    assert formatar_preco(189.99) == "R$189,99"


def test_preco_com_milhar():
    assert formatar_preco(1299.0) == "R$1.299"
```

- Todo teste é uma função cujo nome começa com `test_`.
- `assert` significa "isto tem que ser verdade". Se não for, o teste falha.

Rode no terminal:

```powershell
.venv\Scripts\Activate.ps1
python -m pytest
```

**Vai falhar** com `ImportError: cannot import name 'formatar_preco'`. É o esperado: a função ainda não existe. Ver o teste falhar primeiro prova que ele realmente testa alguma coisa.

## Passo 3 — Escrever `formatar_preco`

Em `ofertas/utils.py`, digite:

```python
def formatar_preco(valor: float) -> str:
    reais, centavos = divmod(round(valor * 100), 100)
    texto = "R$" + f"{reais:,}".replace(",", ".")
    if centavos:
        texto += f",{centavos:02d}"
    return texto
```

Linha a linha:

| Trecho | O que faz |
|---|---|
| `valor: float` e `-> str` | Anotações: avisam que entra um número e sai um texto. Não mudam o comportamento, ajudam quem lê. |
| `round(valor * 100)` | Transforma reais em centavos inteiros: `189.99` → `18999`. Fazemos isso porque contas com números quebrados dão erros minúsculos (`0.1 + 0.2` não dá exatamente `0.3`). |
| `divmod(18999, 100)` | Divide e devolve o resultado **e** o resto: `(189, 99)`. |
| `f"{reais:,}"` | Formata com separador de milhar no padrão americano: `1299` → `"1,299"`. |
| `.replace(",", ".")` | Troca para o padrão brasileiro: `"1.299"`. |
| `if centavos:` | Zero conta como falso. Só escreve os centavos se existirem. |
| `f"{centavos:02d}"` | Sempre dois dígitos: `5` → `"05"`. |

Rode `python -m pytest` de novo. Resultado esperado: `3 passed`.

## Passo 4 — Sua vez: `parse_preco_br`

Agora o caminho inverso, e desta vez **você escreve a função**. Primeiro acrescente os testes em `tests/test_utils.py` (e inclua `parse_preco_br` no `import` da primeira linha):

```python
def test_parse_formato_completo():
    assert parse_preco_br("R$ 1.234,56") == 1234.56


def test_parse_so_centavos():
    assert parse_preco_br("56,43") == 56.43


def test_parse_numero_simples():
    assert parse_preco_br("189") == 189.0


def test_parse_texto_vazio():
    assert parse_preco_br("") is None
```

Depois escreva a função em `ofertas/utils.py`. Um roteiro possível:

1. Se o texto estiver vazio, devolva `None`.
2. Remova tudo que não for dígito, vírgula ou ponto. Dica: `import re` e `re.sub(r"[^\d,.]", "", texto)`.
3. Se sobrou uma vírgula, ela é o separador de centavos: apague os pontos e troque a vírgula por ponto.
4. Converta com `float(...)`.

Rode os testes até ver `7 passed`.

## Passo 5 — Quebrar de propósito

Em `formatar_preco`, troque `02d` por `d` e rode os testes. Todos passam? Então falta um teste. Descubra qual preço revelaria o erro, escreva o teste, veja falhar e desfaça a troca.

Esse é o hábito mais valioso da aula: **um bug que os testes não pegam é um teste que falta**.

## Conferir e avançar

Compare com [`gabarito/ofertas/utils.py`](../gabarito/ofertas/utils.py). A sua versão não precisa ser igual — precisa passar nos testes. O gabarito trata um caso a mais (`"1.234"` sem vírgula, que é mil duzentos e trinta e quatro); se quiser, escreva o teste e resolva.

Quando terminar, me mande a saída do `python -m pytest` e, se travar em algum ponto, o erro que apareceu. A próxima aula é `modelos.py`: a ficha `Oferta`.
