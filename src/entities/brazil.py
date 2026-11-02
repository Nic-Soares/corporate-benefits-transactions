"""CPF and CNPJ provider for Brazil.

Ported from `mimesis.builtins.BrazilSpecProvider` (mimesis 18, MIT license),
which mimesis 19 removed.
"""

from mimesis.providers.base import BaseProvider


class BrazilProvider(BaseProvider):
    """Valid (check-digit) CPF and CNPJ numbers."""

    class Meta:
        name = "brazil_provider"

    @staticmethod
    def _cpf_check_digit(digits: list[int], weight: int) -> int:
        total = sum(digit * (weight - index) for index, digit in enumerate(digits))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    def cpf(self, with_mask: bool = True) -> str:
        """Random CPF, e.g. `001.137.297-40`."""
        digits = [self.random.randint(0, 9) for _ in range(9)]
        digits.append(self._cpf_check_digit(digits, 10))
        digits.append(self._cpf_check_digit(digits, 11))
        cpf = "".join(map(str, digits))

        if with_mask:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf

    @staticmethod
    def _cnpj_check_digit(digits: list[int]) -> int:
        weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2][-len(digits) :]
        total = sum(weight * digit for weight, digit in zip(weights, digits, strict=True))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    def cnpj(self, with_mask: bool = True) -> str:
        """Random CNPJ, e.g. `77.732.230/0001-70`."""
        digits = [self.random.randint(0, 9) for _ in range(12)]
        digits.append(self._cnpj_check_digit(digits))
        digits.append(self._cnpj_check_digit(digits))
        cnpj = "".join(map(str, digits))

        if with_mask:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
