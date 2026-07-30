from dataclasses import dataclass


@dataclass(slots=True)
class MerchantRule:
    merchant: str
    contains: list[str]