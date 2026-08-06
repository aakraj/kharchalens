from __future__ import annotations

from kharchalens.classifier import TransactionClassifier
from kharchalens.merchant import MerchantResolver
from kharchalens.models import Transaction


class TransactionEnricher:

    def __init__(self) -> None:
        self._merchant_resolver = MerchantResolver()
        self._classifier = TransactionClassifier()

    def enrich_transaction(
            self,
            transaction: Transaction,
    ) -> Transaction:

        transaction.merchant = self._merchant_resolver.resolve(
            transaction.narration
        )

        self._classifier.classify(transaction)

        return transaction