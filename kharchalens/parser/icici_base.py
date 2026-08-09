from __future__ import annotations

from typing import ClassVar

from .sbi_base import SbiStatementParser


class IciciStatementParser(SbiStatementParser):
    """Shared row-parsing logic for ICICI statements (Excel and PDF).

    Reuses the SBI parser because ICICI statements share its shape: two date
    columns (``Value Date`` / ``Transaction Date``), a ``Cheque Number``
    column, and ``Withdrawal(Dr)`` / ``Deposit(Cr)`` amount columns, either of
    which is ``0.00`` when empty. Column names, not positions, are what
    matter, and amounts may trail a ``Dr``/``Cr`` suffix.
    """

    #: Headers found on an ICICI statement normalise against these canonical
    #: names via :meth:`_column_for_header`. Normalisation keeps only letters,
    #: digits and spaces, so ``Withdrawal Amount(INR)`` becomes
    #: ``withdrawal amountinr`` and both spellings are listed below.
    _CANONICAL_ALIASES: ClassVar[dict[str, str]] = {
        # Value date.
        "value": "value_date",
        "valuedate": "value_date",
        "value date": "value_date",
        # Transaction / posting date (the date actually reported).
        "transaction": "post_date",
        "transactiondate": "post_date",
        "transaction date": "post_date",
        "businessdate": "post_date",
        "business date": "post_date",
        "txndate": "post_date",
        "txn date": "post_date",
        "postdate": "post_date",
        "post date": "post_date",
        "date": "post_date",
        # Narration.
        "transaction remarks": "details",
        "transactionremarks": "details",
        "particulars": "details",
        "description": "details",
        "description of transaction": "details",
        "narration": "details",
        "remarks": "details",
        "details": "details",
        "txndetails": "details",
        # Reference / cheque number.
        "cheque number": "ref",
        "chequenumber": "ref",
        "cheque": "ref",
        "chequeno": "ref",
        "chq": "ref",
        "chqnoref": "ref",
        "chqrefno": "ref",
        "ref": "ref",
        "refno": "ref",
        "ref no": "ref",
        "refnumber": "ref",
        # Debit.
        "withdrawal": "debit",
        "withdrawalamount": "debit",
        "withdrawal amount": "debit",
        "withdrawalamountinr": "debit",
        "withdrawal amountinr": "debit",
        "withdrawalamtinr": "debit",
        "debit": "debit",
        "debitamount": "debit",
        "debit amount": "debit",
        "dr": "debit",
        # Credit.
        "deposit": "credit",
        "depositamount": "credit",
        "deposit amount": "credit",
        "depositamountinr": "credit",
        "deposit amountinr": "credit",
        "depositamtinr": "credit",
        "credit": "credit",
        "creditamount": "credit",
        "credit amount": "credit",
        "cr": "credit",
        # Balance.
        "balance": "balance",
        "balanceinr": "balance",
        "closingbalance": "balance",
        "closing balance": "balance",
        "runningbalance": "balance",
    }