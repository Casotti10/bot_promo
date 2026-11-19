from dataclasses import dataclass
from datetime import datetime


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
        """Identificador único: usado para não repetir o produto."""
        return f"{self.plataforma}:{self.id_produto}"

    @property
    def desconto(self) -> int | None:
        """Desconto em %: o da loja ou, na falta, calculado pelos preços."""
        # Só confia no desconto da loja se for um valor possível (1 a 99%).
        if self.desconto_pct is not None and 1 <= self.desconto_pct <= 99:
            return self.desconto_pct
        if self.preco and self.preco_original and self.preco_original > self.preco:
            return round(100 * (1 - self.preco / self.preco_original))
        return None


@dataclass
class Cupom:
    codigo: str
    plataforma: str
    valido_ate: datetime | None = None