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


def test_add_public_rule_writes_committed_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    MerchantRuleStore.add_rule(
        merchant="Test Merchant",
        keyword="TEST",
        local=False,
    )

    file = (
            tmp_path
            / "kharchalens"
            / "config"
            / "merchants.yml"
    )

    assert file.exists()

    with open(file) as f:
        data = yaml.safe_load(f)

    assert data["rules"][0]["merchant"] == "Test Merchant"


def test_add_rule_merges_keywords_for_existing_merchant(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    MerchantRuleStore.add_rule("Shop", "PINEAPPLE", local=True)
    MerchantRuleStore.add_rule("Shop", "MANGO", local=True)

    file = tmp_path / "local_data" / "merchants.local.yml"

    with open(file) as f:
        data = yaml.safe_load(f)

    assert data["rules"] == [
        {
            "merchant": "Shop",
            "contains": ["MANGO", "PINEAPPLE"],
        }
    ]


def test_add_rule_rejects_empty_name_or_keyword():
    try:
        MerchantRuleStore.add_rule("  ", "KW", local=True)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Merchant name cannot be empty." in str(exc)

    try:
        MerchantRuleStore.add_rule("Shop", "  ", local=True)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "Keyword cannot be empty." in str(exc)


def test_merchant_sources_reads_local_and_public(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "local_data").mkdir()
    (tmp_path / "local_data" / "merchants.local.yml").write_text(
        "rules:\n  - merchant: Local Shop\n    contains: [LBL]\n",
        encoding="utf-8",
    )

    assert MerchantRuleStore.merchant_sources(local=True) == {"Local Shop"}

    public_names = MerchantRuleStore.merchant_sources(local=False)
    assert "Local Shop" not in public_names
    assert public_names


def test_merchant_sources_missing_file_returns_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert MerchantRuleStore.merchant_sources(local=True) == set()


def test_merchant_names_merges_all_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "local_data").mkdir()
    (tmp_path / "local_data" / "merchants.local.yml").write_text(
        "rules:\n  - merchant: Zebra Shop\n    contains: [ZBR]\n",
        encoding="utf-8",
    )

    names = MerchantRuleStore.merchant_names()

    assert "Zebra Shop" in names
    assert any("amazon" in name.lower() for name in names)
    assert names == sorted(names, key=str.upper)