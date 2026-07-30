from __future__ import annotations

import re


class NarrationNormalizer:
    """
    Converts raw bank narrations into a normalized form
    suitable for merchant matching.
    """

    _SEPARATORS = re.compile(r"[-_/\\.,:;()]+")
    _MULTIPLE_SPACES = re.compile(r"\s+")

    @classmethod
    def normalize(cls, narration: str) -> str:
        text = narration.upper()

        # Replace separators with spaces
        text = cls._SEPARATORS.sub(" ", text)

        # Collapse multiple spaces
        text = cls._MULTIPLE_SPACES.sub(" ", text)

        return text.strip()