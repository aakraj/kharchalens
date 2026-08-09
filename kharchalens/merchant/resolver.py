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
    def _phrase_matches(
            words: list[str],
            keyword_words: list[str],
    ) -> bool:
        """True when the keyword appears in the narration words.

        Two forms are accepted:
          * the keyword's words occur as a contiguous run (e.g.
            ``Amazon Pay Later`` inside ``AMAZON PAY LATER ...``); and
          * the keyword's compacted form is embedded inside a single
            narration word (bank exports often glue tokens, e.g.
            ``ACTFIBERNET``, ``AMZNPRIME``).

        Matching is word-aware, so a short keyword like ``ITR`` can no
        longer match across separate words (with the old all-in-one
        compaction, ``DEBIT RENT`` contained ``ITR``).
        """

        run_length = len(keyword_words)

        for index in range(len(words) - run_length + 1):
            if words[index : index + run_length] == keyword_words:
                return True

        glued = "".join(keyword_words)
        return bool(glued) and any(glued in word for word in words)

    def resolve(
            self,
            narration: str,
            transaction_type: TransactionType | None = None,
    ) -> str:

        normalized = NarrationNormalizer.normalize(narration)
        words = NarrationPreprocessor.preprocess(normalized).split()

        for rule in self.rules:

            for keyword in rule.contains:

                keyword_words = NarrationPreprocessor.preprocess(
                    NarrationNormalizer.normalize(keyword)
                ).split()

                if not keyword_words:
                    continue

                if self._phrase_matches(words, keyword_words):
                    if (
                        transaction_type == TransactionType.DEBIT
                        and rule.merchant in self._CREDIT_ONLY_MERCHANTS
                    ):
                        continue
                    return rule.merchant

        return "Unknown"