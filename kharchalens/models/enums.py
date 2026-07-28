from enum import Enum


class TransactionType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"