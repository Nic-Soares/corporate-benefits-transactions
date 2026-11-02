import re

from src.entities.brazil import BrazilProvider


def _check_digit(digits: list[int], weights: list[int]) -> int:
    remainder = sum(d * w for d, w in zip(digits, weights, strict=True)) % 11
    return 0 if remainder < 2 else 11 - remainder


def test_cpf_is_valid():
    provider = BrazilProvider(seed=1)
    for _ in range(1000):
        cpf = provider.cpf()
        assert re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf)
        d = [int(c) for c in re.sub(r"\D", "", cpf)]
        assert d[9] == _check_digit(d[:9], list(range(10, 1, -1)))
        assert d[10] == _check_digit(d[:10], list(range(11, 1, -1)))


def test_cnpj_is_valid():
    provider = BrazilProvider(seed=1)
    for _ in range(1000):
        cnpj = provider.cnpj()
        assert re.fullmatch(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", cnpj)
        d = [int(c) for c in re.sub(r"\D", "", cnpj)]
        assert d[12] == _check_digit(d[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
        assert d[13] == _check_digit(d[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])


def test_unmasked_and_seeded():
    assert BrazilProvider(seed=7).cpf(with_mask=False).isdigit()
    assert BrazilProvider(seed=7).cnpj(with_mask=False) == BrazilProvider(seed=7).cnpj(
        with_mask=False
    )
