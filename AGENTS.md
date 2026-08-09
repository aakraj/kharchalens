# AGENTS.md

KharchaLens: a privacy-first, offline Streamlit app that parses HDFC bank statements (`.xls`/`.xlsx`/`.pdf`) and shows spending insights. Python 3.14, managed with `uv` (hatchling build backend, `uv.lock`).

## Commands

- Run the app: `uv run streamlit run app.py` — **must be run from the repo root** (see merchant-rules gotcha below).
- Tests: `uv run pytest` (testpaths = `tests`)
- Lint: `uv run ruff check .` — **not clean today** (92 errors: mostly `FURB157` use-pathlib and `DTZ011` naive-datetime, plus `I001` import sorting and `F821` undefined-name — the `continuex` bug below and two unimported `Optional`s). Do not assume a green lint.
- Typecheck: `uv run mypy kharchalens` — strict mode, **not clean today** (missing stubs for plotly/pandas). Treat errors pragmatically.
- `uv` is the only package manager; `.venv/` already exists. `requires-python = ">=3.14,<3.15"`.
- `pdfplumber` is pinned to `cryptography==42.0.8` in `pyproject.toml` because newer `cryptography` has no macOS x86_64 wheels (pdfminer.six requires it) and its source build fails. Do not bump `cryptography` without checking wheel availability for this platform.

## Architecture

- `app.py` (repo root) is the Streamlit entrypoint; all real code lives in the `kharchalens/` package. `temp.py` is a stale prototype — ignore it.
- Upload pipeline: uploader → `HdfcParser.parse(file)` (`.xls`/`.xlsx`) or `HdfcPdfParser.parse(file)` (`.pdf`) → `TransactionEnricher.enrich_transaction(txn)` (runs merchant resolution + classification) → dashboard renderers in `kharchalens/dashboard/`. `app.py` dispatches on the file suffix.
- `HdfcParser` (`.xls`/`.xlsx` only) heuristically finds the header row, parses dates day-first, and requires columns `Date`, `Narration`, `Chq./Ref.No.`, `Withdrawal Amt.`, `Deposit Amt.`.
- `HdfcPdfParser` reads HDFC PDFs via pdfplumber **word positions** (blank withdrawal/deposit cells vanish from raw text, so values are column-assigned by x-coordinate). Extraction: `page.extract_words()` → `_group_words_by_line` (groups by `top` rounded to 0.1, sorts by x0) → column assigned by comparing a word's **left edge** (`x0`) against the header column's left edges (`_column_for_x`). Multi-line narrations are appended to the previous row — in real HDFC PDFs only the transaction's first line carries the date, and continuation lines carry the ref/amounts. Password-protected PDFs are supported: `parse(file, password=...)` passes the password to `pdfplumber.open`; on failure it unwraps the inner exception and raises `PdfPasswordRequired` (no password given) or `PdfIncorrectPassword` (wrong password) — both subclass `ValueError`. (Note: the `PdfminerException` you may see comes from **pdfplumber's own** `utils.exceptions`, wrapping pdfminer's `PDFPasswordIncorrect` — the wrapper's `str()` is empty.) Damaged/scanned PDFs raise a generic `ValueError` that includes the underlying traceback. `_extract_word_rows` is what integration tests must exercise (a past bug: `extract_text_lines()` dicts have no `words` key — always use `extract_words()`).
- Merchant matching: `narration → NarrationNormalizer.normalize → NarrationPreprocessor.preprocess → substring match of rule keywords`. Unmatched resolves to the magic string `"Unknown"`, which other code checks against.
- Amounts are `Decimal`, dates are `datetime.date`. Use `kharchalens/dashboard/summary.py:format_inr` for money display.

## Merchant rules (the main gotcha)

Rules are YAML `rules:` lists of `{merchant, contains[]}`. `MerchantResolver` loads BOTH files:

- `kharchalens/config/merchants.yml` — committed, generic rules for all users.
- `local_data/merchants.local.yml` — gitignored, personal rules.

`MerchantRuleStore.add_rule(merchant, keyword, local)` resolves both files via `Path.cwd()`, and `MerchantResolver` loads the local file via `Path.cwd()` (only the committed one is package-relative). Running from any other directory silently drops local rules, and `add_rule(local=False)` would write a bogus `kharchalens/config/merchants.yml` under the wrong cwd. The app's Developer Mode toggle (top-right) adds rules via the "Top Unknown Spending" table; new rules appear only after a `st.rerun()`.

## Testing quirks

- `tests/test_hdfc_parser.py` exercises `HdfcParser` end-to-end with throwaway `.xlsx` workbooks written to `tmp_path` (no real fixture needed — `openpyxl` reads both `.xls`/`.xlsx` via content sniffing). The PDF parser is unit-tested with synthetic word-coordinate rows (monkeypatched `_extract_word_rows`) plus end-to-end tests against the committed reportlab-generated `tests/fixtures/hdfc_sample.pdf` (2 pages, multi-line narration, repeated header). `tests/fixtures/hdfc_sample_encrypted.pdf` is that same statement encrypted with the password `secret123` (via throwaway pypdf — not a project dep) and drives the password tests: no password → `PdfPasswordRequired`, wrong → `PdfIncorrectPassword`, correct → 7 transactions. Both fixtures are synthetic — a real sanitized HDFC `.pdf` should eventually replace them.
- `tests/test_merchant_resolver.py` asserts against the real committed `merchants.yml` (Zomato/Swiggy/Amazon/Unknown) — edit that YAML and these tests change.
- `tests/test_rule_store.py` isolates writes with `monkeypatch.chdir(tmp_path)`.

## Style

- ruff line-length 100, target `py314`; mypy `strict = true`.
- Existing code favors `from __future__ import annotations`, dataclasses with `slots=True`, and `staticmethod`s. It uses a nonstandard 8-space hang-indent for class-method parameters.
