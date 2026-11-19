from ofertas.utils import formatar_preco, parse_preco_br


def test_preco_sem_centavos():
    assert formatar_preco(399.0) == "R$399"


def test_preco_com_centavos():
    assert formatar_preco(189.99) == "R$189,99"


def test_preco_com_milhar():
    assert formatar_preco(1299.0) == "R$1.299"

def test_parse_formato_completo():
    assert parse_preco_br("R$ 1.234,56") == 1234.56

def test_parse_so_centavos():
    assert parse_preco_br("56,43") == 56.43

def test_parse_numero_simples():
    assert parse_preco_br("189") == 189.0

def test_parse_texto_vazio():
    assert parse_preco_br("") is None

def test_parse_com_texto_em_volta():
    assert parse_preco_br("R$ 189 no Pix") == 189.0

def test_preco_centavos_com_um_digito():
    assert formatar_preco(10.05) == "R$10,05"


def test_parse_dois_precos_devolve_none():
    # Melhor ficar sem preço do que publicar um preço errado.
    assert parse_preco_br("R$ 1.234,56 por R$ 999,00") is None

