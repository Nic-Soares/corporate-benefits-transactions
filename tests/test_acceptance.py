"""One acceptance rule for the generator and the issuer."""

from src.domain.acceptance import OPEN_WALLET, Acceptance
from src.reference import build_reference_tables


def test_generator_and_issuer_read_the_same_rule(sources):
    """The rule from the config (generator) and from the reference tables the
    setup loads (issuer) answer alike for every CNAE and MCC."""
    tables = build_reference_tables(sources.cnae, sources.mcc)
    issuer = Acceptance(tables["cnae_wallets"].to_dicts(), tables["mcc_wallets"].to_dicts())
    generator = Acceptance.from_config()
    for cnae in sources.cnae["subclasse_id"]:
        assert generator.by_cnae(cnae) == issuer.by_cnae(cnae)
    for mcc in sources.mcc["mcc_code"]:
        assert generator.by_mcc(mcc) == issuer.by_mcc(mcc)


def test_inactive_rule_and_longest_prefix():
    acceptance = Acceptance(
        [
            {"cnae_code": "5611", "wallet_id": "MEAL", "active": True},
            {"cnae_code": "5611201", "wallet_id": "MEAL", "active": False},
            {"cnae_code": "5611201", "wallet_id": "GIFT", "active": True},
        ],
        [{"mcc_code": "5812", "wallet_id": "MEAL"}],
    )
    assert acceptance.by_cnae("5611201") == {"GIFT"}  # the longer prefix wins, inactive out
    assert acceptance.by_cnae("5611203") == {"MEAL"}
    assert acceptance.by_mcc("5812") == {"MEAL", OPEN_WALLET}
    assert acceptance.by_mcc("0000") == {OPEN_WALLET}
