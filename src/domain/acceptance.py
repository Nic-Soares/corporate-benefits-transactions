"""Where a wallet is accepted: the one rule the attempt generator and the
issuer's validators both follow.

Proprietary network: the establishment's CNAE decides, by the longest
matching prefix among the rules (`cnae_wallets`), only the active ones. Brand
cards: the wallets the issuer can charge at the establishment's MCC
(`mcc_wallets`), plus the open wallet, which takes any MCC.
"""

from collections.abc import Iterable
from typing import Any

from src.data_generators.reference_data.card_program_loader import (
    load_cnae_wallets,
    load_mcc_wallets,
)
from src.utils.read_yamls import load_pre_populated_data

OPEN_WALLET = "GIFT"  # on a brand card, takes any MCC (and cash)


class Acceptance:
    """Built from rule rows: `cnae_wallets` (`cnae_code`, `wallet_id`, `active`)
    and `mcc_wallets` (`mcc_code`, `wallet_id`)."""

    def __init__(
        self, cnae_wallets: Iterable[dict[str, Any]], mcc_wallets: Iterable[dict[str, Any]]
    ) -> None:
        self.cnae_rules: dict[str, dict[str, bool]] = {}
        for row in cnae_wallets:
            self.cnae_rules.setdefault(row["cnae_code"], {})[row["wallet_id"]] = row["active"]
        self.mcc_rules: dict[str, set[str]] = {}
        for row in mcc_wallets:
            self.mcc_rules.setdefault(row["mcc_code"], set()).add(row["wallet_id"])
        self._by_cnae: dict[str, set[str]] = {}

    @classmethod
    def from_config(cls) -> Acceptance:
        """The rules of `pre_populated_data.yaml`, as the setup loads them."""
        data = load_pre_populated_data()
        return cls(load_cnae_wallets(data).to_dicts(), load_mcc_wallets(data).to_dicts())

    def by_cnae(self, cnae: str) -> set[str]:
        """Proprietary network: the active wallets of the longest matching prefix."""
        if cnae not in self._by_cnae:
            prefixes = [code for code in self.cnae_rules if cnae.startswith(code)]
            rules = self.cnae_rules[max(prefixes, key=len)] if prefixes else {}
            self._by_cnae[cnae] = {wallet for wallet, active in rules.items() if active}
        return self._by_cnae[cnae]

    def by_mcc(self, mcc: str) -> set[str]:
        """Brand: the wallets the issuer charges at the MCC, plus the open wallet."""
        return self.mcc_rules.get(mcc, set()) | {OPEN_WALLET}

    def wallets(self, cnae: str, mcc: str) -> set[tuple[str, str]]:
        """(network, wallet) pairs an establishment takes: `own` or `brand`."""
        return {("own", w) for w in self.by_cnae(cnae)} | {("brand", w) for w in self.by_mcc(mcc)}
