"""Masked layout dump for an SBI PDF (no personal data printed)."""
from __future__ import annotations

import re
import sys

import pdfplumber

from kharchalens.parser.hdfc_pdf import HdfcPdfParser

path = sys.argv[1]
password = sys.argv[2] if len(sys.argv) > 2 else None

DATE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
NUM = re.compile(r"^[\d.,₹-]+$")


def red(s: str) -> str:
    if DATE.match(s):
        return "DATE"
    if NUM.match(s):
        return "NUM"
    return "TXT"


parser = HdfcPdfParser()
with pdfplumber.open(path, password=password or "") as pdf:
    print(f"=== {len(pdf.pages)} pages ===")
    for page_index, page in enumerate(pdf.pages):
        lines = parser._group_words_by_line(page.extract_words())
        print(f"--- page {page_index+1}: {len(lines)} lines ---")
        for line in lines[:40]:
            ws = " | ".join(
                f"[{red(w[3])}@{round(w[0])},top{round(w[2])}]" for w in line
            )
            print(ws)