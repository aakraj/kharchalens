import yaml

from kharchalens.merchant.rule_store import MerchantRuleStore


def test_add_local_rule(tmp_path, monkeypatch):

    monkeypatch.chdir(tmp_path)

    MerchantRuleStore.add_rule(
        merchant="Test Merchant",
        keyword="TEST",
        local=True,
    )

    file = (
            tmp_path
            / "local_data"
            / "merchants.local.yml"
    )

    assert file.exists()

    with open(file) as f:
        data = yaml.safe_load(f)

    assert data["rules"][0]["merchant"] == "Test Merchant"