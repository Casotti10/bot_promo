import re

def formatar_preco(valor: float) -> str:
    reais, centavos = divmod(round(valor * 100), 100) ##Divide e devolve o resultado e o resto: reais = 189, centavos = 99.
    texto = "R$" + f"{reais:,}".replace(",", ".")
    if centavos:
        texto += f",{centavos:02d}"
    return texto

def parse_preco_br(texto: str) -> float | None:
    if not texto:
        return None
    texto = re.sub(r"[^\d,.]", "", texto).replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None
