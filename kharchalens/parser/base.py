from __future__ import annotations

from abc import ABC, abstractmethod

from kharchalens.models import Transaction


class StatementParser(ABC):
    """Base class for all bank statement parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> list[Transaction]:
        """Parse a statement into transactions."""
        raise NotImplementedError