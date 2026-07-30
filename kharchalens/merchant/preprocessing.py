from __future__ import annotations

import re


class NarrationPreprocessor:
    """
    Removes bank-specific noise from normalized narrations.
    """

    _TRANSACTION_WORDS = {
        "POS",
        "UPI",
        "IMPS",
        "NEFT",
        "RTGS",
        "ACH",
        "ATM",
        "DR",
        "CR",
        "NETBANK",
    }

    _NUMBER_PATTERN = re.compile(r"\b\d+\b")
    _CARD_PATTERN = re.compile(r"\b\d+X+\d+\b", re.IGNORECASE)

    @classmethod
    def preprocess(cls, narration: str) -> str:

        narration = cls._remove_transaction_words(narration)
        narration = cls._remove_card_numbers(narration)
        narration = cls._remove_numbers(narration)
        narration = cls._collapse_spaces(narration)

        return narration

    @classmethod
    def _remove_transaction_words(cls, text: str) -> str:

        words = [
            word
            for word in text.split()
            if word not in cls._TRANSACTION_WORDS
        ]

        return " ".join(words)

    @classmethod
    def _remove_card_numbers(cls, text: str) -> str:

        return cls._CARD_PATTERN.sub(" ", text)

    @classmethod
    def _remove_numbers(cls, text: str) -> str:

        return cls._NUMBER_PATTERN.sub(" ", text)

    @staticmethod
    def _collapse_spaces(text: str) -> str:

        return " ".join(text.split())