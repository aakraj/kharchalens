from __future__ import annotations

from pathlib import Path

import yaml

from .rules import MerchantRule
from .normalizer import NarrationNormalizer


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

        narration = NarrationNormalizer.normalize(narration)

        for rule in self.rules:

            for keyword in rule.contains:

                if keyword in narration:
                    return rule.merchant

        return "Unknown"