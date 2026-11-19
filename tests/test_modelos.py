from datetime import datetime
from ofertas.modelos import Cupom, Oferta


def test_oferta_guarda_os_dados():
    o = Oferta(plataforma="mercadolivre", id_produto="MLB123", titulo="Tênis Reserva Roma")
    assert o.titulo == "Tênis Reserva Roma"
    assert o.preco is None


def test_uid_junta_loja_e_produto():
    o = Oferta(plataforma="amazon", id_produto="B0ABC", titulo="Echo Dot")
    assert o.uid == "amazon:B0ABC"

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

    
def test_cupom_com_validade():
    c = Cupom(codigo="TODOSITE1511", plataforma="mercadolivre",
              valido_ate=datetime(2026, 11, 30, 23, 59))
    assert c.valido_ate.day == 30


def test_cupom_sem_validade():
    c = Cupom(codigo="FRETE10", plataforma="shopee")
    assert c.valido_ate is None


def test_desconto_absurdo_da_loja_e_ignorado():
    o = Oferta(plataforma="shopee", id_produto="1", titulo="Fone", desconto_pct=150)
    assert o.desconto is None


def test_desconto_absurdo_usa_os_precos():
    o = Oferta(plataforma="shopee", id_produto="1", titulo="Fone", desconto_pct=150,
               preco=50.0, preco_original=100.0)
    assert o.desconto == 50