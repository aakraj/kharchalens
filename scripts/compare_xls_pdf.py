"""Compare parsed HDFC .xls/.xlsx vs .pdf transaction rows.

Usage:
    uv run python scripts/compare_xls_pdf.py <xls-or-xlsx> <pdf> [password] [--mask]

Parses both files and reports every row where the PDF parse disagrees with
the XLS parse on any field. With ``--mask``, narration text is redacted so
layout bugs can be diagnosed without exposing personal data.
"""
from __future__ import annotations

import sys

from kharchalens.enrichment.enricher import TransactionEnricher
from kharchalens.parser import HdfcParser, HdfcPdfParser

_MASK = "--mask" in sys.argv
ARGS = [a for a in sys.argv[1:] if a != "--mask"]
xls_path = ARGS[0]
pdf_path = ARGS[1]
password = ARGS[2] if len(ARGS) > 2 else None

enricher = TransactionEnricher()


def _mask(text: str) -> str:
    if not _MASK:
        return text
    import re

    numeric = re.compile(r"^[\d.,₹-]+$")
    words = text.split()
    return " ".join(
        "DATE" if re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", w)
        else (f"NUM:{len(w)}" if numeric.match(w) else f"TXT:{len(w)}")
        for w in words
    )


xls = HdfcParser().parse(xls_path)
pdf = HdfcPdfParser().parse(pdf_path, password=password)

xls = [enricher.enrich_transaction(t) for t in xls]
pdf = [enricher.enrich_transaction(t) for t in pdf]

print(f"xls count: {len(xls)}, pdf count: {len(pdf)}")

_max = max(len(xls), len(pdf))

fields = ["date", "type", "amount", "balance", "reference", "merchant", "category", "subcategory", "kind", "narration"]


def row_view(t) -> dict[str, str]:
    ref = f'"{t.reference_number}"' if t.reference_number else None
    return {
        "date": t.date.isoformat(),
        "type": "D" if t.transaction_type.name == "DEBIT" else "C",
        "amount": str(t.amount),
        "amount_n": t.amount,
        "balance": str(t.balance) if t.balance is not None else "",
        "balance_n": t.balance,
        "reference": ref or "",
        "merchant": t.merchant or "",
        "category": t.category or "",
        "subcategory": t.subcategory or "",
        "kind": t.kind.name if t.kind is not None else "",
        "narration": _mask(t.narration),
    }


def differs(a_view: dict, b_view: dict, key: str) -> bool:
    if key in ("amount", "balance"):
        return a_view[f"{key}_n"] != b_view[f"{key}_n"]
    return a_view[key] != b_view[key]


mismatches = 0
amount_mismatches = 0
narration_diffs = 0
merchant_diffs = 0
category_diffs = 0
kind_diffs = 0
for i in range(_max):
    a = xls[i] if i < len(xls) else None
    b = pdf[i] if i < len(pdf) else None

    if a is None or b is None:
        mismatches += 1
        print(f"row {i}: count mismatch (xls={a is not None}, pdf={b is not None})")
        continue

    va, vb = row_view(a), row_view(b)
    diffs = [k for k in fields if differs(va, vb, k)]
    if not diffs:
        continue
    mismatches += 1
    if "amount" in diffs or "balance" in diffs:
        amount_mismatches += 1
    if "narration" in diffs:
        narration_diffs += 1
    if "merchant" in diffs:
        merchant_diffs += 1
    if "category" in diffs or "subcategory" in diffs:
        category_diffs += 1
    if "kind" in diffs:
        kind_diffs += 1

    # Always print rows whose money differs; only show a handful of
    # narration-only rows so the important output stays readable.
    if (
        "amount" in diffs
        or "balance" in diffs
        or "merchant" in diffs
        or "category" in diffs
        or "subcategory" in diffs
        or "kind" in diffs
    ) or mismatches <= 20:
        print(f"row {i}:")
        for key in fields:
            marker = "  " if not differs(va, vb, key) else "->"
            print(f"    {key:10s} {marker} xls={va[key]!r} pdf={vb[key]!r}")

print(
    f"\n{mismatches} mismatched rows "
    f"({amount_mismatches} amount/balance, "
    f"{merchant_diffs} merchant, "
    f"{category_diffs} category/subcategory, "
    f"{kind_diffs} kind, "
    f"{narration_diffs} narration)"
)