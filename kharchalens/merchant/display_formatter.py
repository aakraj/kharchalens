from __future__ import annotations

import re


class MerchantDisplayFormatter:

    @staticmethod
    def format(narration: str) -> str:

        text = narration.upper()

        # Remove common prefixes
        prefixes = [
            "POS ",
            "UPI-",
            "UPI ",
            "NEFT DR-",
            "IMPS-",
            "ACH D-",
            "ATW-",
        ]

        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]

        # Remove masked card numbers
        text = re.sub(r"\b\d+X+\d+\b", "", text)

        # Collapse repeated separators
        text = text.replace("-", " ")
        text = text.replace("/", " ")

        text = re.sub(r"\s+", " ", text).strip()

        return text