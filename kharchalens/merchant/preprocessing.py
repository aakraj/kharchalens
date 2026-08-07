from __future__ import annotations

import re


class NarrationPreprocessor:
    """
    Removes bank-specific noise from normalized narrations.
    """

    _TRANSACTION_WORDS = frozenset({
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
    })

    _NUMBER_PATTERN = re.compile(r"\b\d+\b")
    _CARD_PATTERN = re.compile(r"\b\d+X+\d+\b", re.IGNORECASE)

    _UPI_PREFIX = re.compile(r"^UPI\s*-\s*", re.IGNORECASE)
    _POS_PREFIX = re.compile(r"^POS\s+", re.IGNORECASE)

    @classmethod
    def extract_keyword(cls, narration: str) -> str:
        """Best-effort default keyword for a raw bank narration.

        - ``UPI-ALL MARKET-...`` → the payee's name right after ``UPI-``.
        - ``POS 512967XXXXXX8643 GK ENTERPRISES V`` → drop the ``POS`` prefix
          and the masked card number, keep the merchant name.
        - Anything else → the full narration.
        """
        def _is_card_number(token: str) -> bool:
            return bool(cls._CARD_PATTERN.match(token)) or (
                token.isdigit() and len(token) >= 12
            )

        text = narration.strip()

        match = cls._UPI_PREFIX.match(text)
        if match:
            segment = text[match.end():].split("-", 1)[0].strip()
            if segment:
                return segment

        match = cls._POS_PREFIX.match(text)
        if match:
            tokens = text[match.end():].split()
            if tokens and _is_card_number(tokens[0]):
                tokens = tokens[1:]
            if tokens:
                return " ".join(tokens).strip()

        return text

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