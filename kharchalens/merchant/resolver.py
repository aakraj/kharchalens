from __future__ import annotations

from pathlib import Path

import yaml

from kharchalens.models import TransactionType

from .normalizer import NarrationNormalizer
from .preprocessing import NarrationPreprocessor
from .rules import MerchantRule


class MerchantResolver:

    _CREDIT_ONLY_MERCHANTS = frozenset(
        {
            "Dividend Credit",
            "Interest Credit",
        }
    )

    def __init__(self) -> None:

        self.rules: list[MerchantRule] = []

        self._load_rules(
            Path(__file__).parent.parent
            / "config"
            / "merchants.yml"
        )

        self._load_rules(
            Path.cwd()
            / "local_data"
            / "merchants.local.yml"
        )

    def _load_rules(self, path: Path) -> None:

        if not path.exists():
            return

        with open(path, encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}

        self.rules.extend(
            MerchantRule(**rule)
            for rule in config.get("rules", [])
        )

    @staticmethod
    def _compact(text: str) -> str:

        return "".join(text.split())

    def resolve(
            self,
            narration: str,
            transaction_type: TransactionType | None = None,
    ) -> str:

        normalized = NarrationNormalizer.normalize(narration)
        preprocessed = self._compact(
            NarrationPreprocessor.preprocess(normalized)
        )

        for rule in self.rules:

            for keyword in rule.contains:

                compact_keyword = self._compact(
                    NarrationPreprocessor.preprocess(
                        NarrationNormalizer.normalize(keyword)
                    )
                )

                if compact_keyword and compact_keyword in preprocessed:
                    if (
                        transaction_type == TransactionType.DEBIT
                        and rule.merchant in self._CREDIT_ONLY_MERCHANTS
                    ):
                        continue
                    return rule.merchant

        return "Unknown"