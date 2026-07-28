from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

from kharchalens.models import Transaction, TransactionType

from .base import StatementParser


class HdfcParser(StatementParser):
    REQUIRED_COLUMNS = [
        "Date",
        "Narration",
        "Chq./Ref.No.",
        "Withdrawal Amt.",
        "Deposit Amt.",
        "Closing Balance",
    ]

    def parse(self, file_path: str) -> list[Transaction]:

        suffix = Path(file_path).suffix.lower()

        if suffix == ".xls":
            df = pd.read_excel(file_path, engine="xlrd")
        elif suffix == ".xlsx":
            df = pd.read_excel(file_path, engine="openpyxl")
        else:
            raise ValueError("Only .xls and .xlsx are currently supported.")

        missing = [
            c for c in self.REQUIRED_COLUMNS
            if c not in df.columns
        ]

        if missing:
            raise ValueError(
                f"Not a valid HDFC statement. Missing columns: {missing}"
            )

        transactions: list[Transaction] = []

        for _, row in df.iterrows():

            debit = row["Withdrawal Amt."]
            credit = row["Deposit Amt."]

            if pd.notna(debit):
                amount = Decimal(str(debit))
                tx_type = TransactionType.DEBIT
            else:
                amount = Decimal(str(credit))
                tx_type = TransactionType.CREDIT

            balance = None
            if pd.notna(row["Closing Balance"]):
                balance = Decimal(str(row["Closing Balance"]))

            reference = None
            if pd.notna(row["Chq./Ref.No."]):
                reference = str(row["Chq./Ref.No."])

            transactions.append(
                Transaction(
                    date=datetime.strptime(
                        str(row["Date"]),
                        "%d/%m/%Y",
                    ).date(),
                    narration=str(row["Narration"]),
                    amount=amount,
                    transaction_type=tx_type,
                    balance=balance,
                    reference_number=reference,
                )
            )

        return transactions