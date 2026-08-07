from __future__ import annotations

from pathlib import Path

import yaml


class MerchantRuleStore:

    @staticmethod
    def merchant_names() -> list[str]:
        """Return the sorted, de-duplicated merchant names from all rule files."""
        names: set[str] = set()
        project_root = Path.cwd()
        paths = [
            Path(__file__).resolve().parent.parent / "config" / "merchants.yml",
            project_root / "local_data" / "merchants.local.yml",
        ]
        for path in paths:
            if not path.exists():
                continue
            with open(path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            for rule in config.get("rules", []):
                name = rule.get("merchant", "")
                if name:
                    names.add(name)
        return sorted(names, key=str.upper)

    @staticmethod
    def merchant_sources(local: bool) -> set[str]:
        """Return the set of merchant names defined in a single rule file.

        ``local=True`` reads the gitignored ``local_data/merchants.local.yml``,
        ``local=False`` reads the committed ``merchants.yml``.
        """
        project_root = Path.cwd()
        path = (
            project_root / "local_data" / "merchants.local.yml"
            if local
            else Path(__file__).resolve().parent.parent / "config" / "merchants.yml"
        )
        names: set[str] = set()
        if path.exists():
            with open(path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            for rule in config.get("rules", []):
                name = rule.get("merchant", "")
                if name:
                    names.add(name)
        return names

    @staticmethod
    def add_rule(
            merchant: str,
            keyword: str,
            local: bool,
    ) -> None:
        merchant = merchant.strip()
        keyword = keyword.strip().upper()

        if not merchant:
            raise ValueError("Merchant name cannot be empty.")

        if not keyword:
            raise ValueError("Keyword cannot be empty.")

        project_root = Path.cwd()

        if local:
            file = (
                    project_root
                    / "local_data"
                    / "merchants.local.yml"
            )
        else:
            file = (
                    project_root
                    / "kharchalens"
                    / "config"
                    / "merchants.yml"
            )

        # Create parent folder if needed
        file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing YAML
        if file.exists():
            with open(file, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        rules = config.get("rules", [])

        # Add new or update the rule
        existing_rule = None
        for rule in rules:
            if rule["merchant"].upper() == merchant.upper():
                existing_rule = rule
                break

        if existing_rule is None:
            rules.append(
                {
                    "merchant": merchant,
                    "contains": [keyword],
                }
            )
        else:
            keywords = existing_rule.setdefault(
                "contains",
                [],
            )
            if keyword not in keywords:
                keywords.append(keyword)
            keywords.sort()

        # Sort alphabetically by merchant
        rules = sorted(
            rules,
            key=lambda r: r["merchant"].upper(),
        )

        config["rules"] = rules

        # Save back
        with open(
                file,
                "w",
                encoding="utf-8",
        ) as f:
            yaml.safe_dump(
                config,
                f,
                sort_keys=False,
                allow_unicode=True,
            )