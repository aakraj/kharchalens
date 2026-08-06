from datetime import date
from decimal import Decimal

from kharchalens.classifier import TransactionClassifier
from kharchalens.models import (
    Transaction,
    TransactionKind,
    TransactionType,
)


def classify(text: str) -> Transaction:

    transaction = Transaction(
        date=date.today(),
        narration=text,
        amount=Decimal(100),
        transaction_type=TransactionType.DEBIT,
    )

    TransactionClassifier.classify(transaction)

    return transaction


def test_ppf():

    assert classify("NEFT DR MY PPF").kind == TransactionKind.INVESTMENT


def test_ssy():

    assert classify("DAUGHTER SSY").kind == TransactionKind.INVESTMENT


def test_atm():

    assert classify("ATW BANGALORE").kind == TransactionKind.CASH_WITHDRAWAL


def test_zerodha():

    assert classify("UPI ZERODHA").kind == TransactionKind.INVESTMENT


def test_purchase():

    assert classify("AMAZON").kind == TransactionKind.PURCHASE