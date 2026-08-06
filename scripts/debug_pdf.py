"""Dump how HdfcPdfParser sees a real HDFC PDF statement.

Usage:
    uv run python scripts/debug_pdf.py <path-to-pdf> [password] [--mask]

With ``--mask``, transaction content is redacted: words are shown only as
DATE / NUM / TXT with their x0/x1/top positions and length, so a layout
bug can be diagnosed without exposing personal data. Without it, the full
word text is printed (for local use only).

Prints per-page stats, the detected header columns, the first pages' raw
word rows, and the raw parsed rows.
"""
from __future__ import annotations

import re
import sys

import pdfplumber

from kharchalens.parser.hdfc_pdf import HdfcPdfParser

_MASK = "--mask" in sys.argv
ARGS = [a for a in sys.argv[1:] if a != "--mask"]
path = ARGS[0]
password = ARGS[1] if len(ARGS) > 1 else None

_DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
_NUM_RE = re.compile(r"^[\d.,₹-]+$")


def redact(text: str) -> str:
    if _DATE_RE.match(text):
        return "DATE"
    if _NUM_RE.match(text):
        return f"NUM:{len(text)}"
    return f"TXT:{len(text)}"


def show(text: str) -> str:
    return redact(text) if _MASK else text


parser = HdfcPdfParser()

with pdfplumber.open(path, password=password or "") as pdf:
    print(f"=== {len(pdf.pages)} pages ===")
    page_lines = []
    for index, page in enumerate(pdf.pages):
        words = page.extract_words()
        lines = parser._group_words_by_line(words)
        page_lines.append(lines)
        print(
            f"page {index + 1:3d}: words={len(words):5d} lines={len(lines):4d}"
        )

lines = [line for page in page_lines for line in page]

columns = parser._header_columns(lines)
print("\n=== detected header columns (word x0) ===")
if columns is None:
    print("  NONE")
else:
    for name, x in columns.items():
        print(f"  {name}: x0={x}")

date_count = 0
for line in lines:
    if parser._extract_date(line, columns or {}) is not None:
        date_count += 1
print(f"\n=== {len(lines)} total lines, {date_count} lines with a detected date ===")

print("\n=== first 3 pages raw lines ===")
for index, line in enumerate(lines[:80]):
    words = " | ".join(f"[{w[1]:6.1f},{w[0]:6.1f}] {show(w[3])}" for w in line)
    print(f"{index:3d} top={line[0][2]:6.1f} {words}")

rows = parser._lines_to_transactions(lines)
print(f"\n=== {len(rows)} raw rows ===")
for row in rows[:50]:
    print("  ", {key: show(str(value)) for key, value in row.items()})

print("\n=== drop analysis (uses real _parse_row) ===")
reasons = {
    "no date": 0,
    "bad date": 0,
    "empty narration": 0,
    "unparsable amount": 0,
    "zero/absent amount": 0,
}
kept = 0
for row in rows:
    if parser._parse_row(row) is not None:
        kept += 1
        continue
    date_value = str(row.get("Date") or "").strip()
    narration = str(row.get("Narration") or "").strip()
    withdrawal = str(row.get("Withdrawal Amt.") or "").strip()
    deposit = str(row.get("Deposit Amt.") or "").strip()

    if not date_value:
        reasons["no date"] += 1
    elif parser._parse_date(date_value) is None:
        reasons["bad date"] += 1
    elif not narration:
        reasons["empty narration"] += 1
    elif (withdrawal or deposit) and (
        parser._parse_amount(withdrawal) is None
        and parser._parse_amount(deposit) is None
    ):
        reasons["unparsable amount"] += 1
    else:
        reasons["zero/absent amount"] += 1

for reason, count in reasons.items():
    print(f"  {reason}: {count}")
print(f"  kept (valid transactions): {kept}")
print(
    "  (parser.parse drops exactly the rows above; this count must equal "
    "the final transaction count)"
)

print("\n=== last page raw lines (masked) ===")
for index, line in enumerate(lines[-50:], start=len(lines) - 50):
    words = " | ".join(f"[{w[1]:6.1f},{w[0]:6.1f}] {show(w[3])}" for w in line)
    print(f"{index:3d} top={line[0][2]:6.1f} {words}")

print("\n=== dropped rows (masked, from fixed _lines_to_transactions) ===")
shown = 0
for row in rows:
    if parser._parse_row(row) is not None:
        continue
    print("  ", {key: show(str(value)) for key, value in row.items()})
    shown += 1
    if shown >= 40:
        break
if shown == 0:
    print("  none")

print("\n=== final transaction count (parser.parse) ===")
print(f"  {len(parser.parse(path, password=password))}")

