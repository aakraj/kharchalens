from enum import Enum


class TransactionKind(str, Enum):

    PURCHASE = "Lifestyle Spending"

    INVESTMENT = "Investment"

    TRANSFER = "Family/Self Transfer"

    CASH_WITHDRAWAL = "Cash Withdrawal"

    INSURANCE = "Insurance"

    UNKNOWN = "Unknown"