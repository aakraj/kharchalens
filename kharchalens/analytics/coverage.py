from __future__ import annotations

from dataclasses import dataclass

from kharchalens.models import Transaction


@dataclass(slots=True)
class MerchantCoverage:
    recognized: int
    unknown: int

    @property
    def total(self) -> int:
        return self.recognized + self.unknown

    @property
    def coverage(self) -> float:
        if self.total == 0:
            return 0.0

        return (self.recognized / self.total) * 100


def merchant_coverage(
        transactions: list[Transaction],
) -> MerchantCoverage:

    recognized = 0
    unknown = 0

    for transaction in transactions:

        if transaction.merchant in (None, "", "Unknown"):
            unknown += 1
        else:
            recognized += 1

    return MerchantCoverage(
        recognized=recognized,
        unknown=unknown,
    )