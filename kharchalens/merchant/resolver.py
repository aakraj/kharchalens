from __future__ import annotations

from pathlib import Path

import yaml

from .normalizer import NarrationNormalizer
from .preprocessing import NarrationPreprocessor
from .rules import MerchantRule


class MerchantResolver:

    def __init__(self) -> None:

        config_file = (
                Path(__file__).parent.parent
                / "config"
                / "merchants.yml"
        )

        with open(config_file, encoding="utf-8") as file:
            config = yaml.safe_load(file)

        self.rules: list[MerchantRule] = [
            MerchantRule(**rule)
            for rule in config["rules"]
        ]

    def resolve(self, narration: str) -> str:

        normalized = NarrationNormalizer.normalize(narration)
        preprocessed = NarrationPreprocessor.preprocess(normalized)

        for rule in self.rules:

            for keyword in rule.contains:

                if keyword in preprocessed:
                    return rule.merchant

        return "Unknown"