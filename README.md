# KharchaLens 💰

> **Understand your spending. Protect your privacy.**

KharchaLens is a **privacy-first, offline personal finance analyzer** that reads your **HDFC bank statements** (.xls / .xlsx / .pdf) and tells you where your money goes.

It answers one simple question:

> **Where did my money go?**

Every statement is parsed and analyzed **entirely on your computer** — no account, no cloud upload, no tracking. Your data never leaves your device.

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Supported Statements](#supported-statements)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Run the app](#run-the-app)
  - [Import a statement](#import-a-statement)
- [Configuration](#configuration)
  - [Adding merchant rules](#adding-merchant-rules)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Development](#development)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Features

- **📊 Spending Dashboard** — total credit, total debit, savings and savings rate at a glance.
- **📅 Monthly Spending Trend** — track how your spending shifts month to month.
- **🏪 Merchant Detection** — automatic recognition of common merchants (Zomato, Swiggy, Amazon, …) with ranked Top Merchants and a full spend/average/transaction summary.
- **🧾 Category Breakdown** — classified into Lifestyle Spending, Investment, Insurance, Cash Withdrawal, Transfers and more.
- **💡 Highlights** — top merchant, top category, savings rate and statement period.
- **📄 Transactions** — browse every dated transaction (narration, merchant, amount, balance).
- **🛠 Developer Mode** — merchant coverage metrics + a review UI to resolve unknown spending.

**Missing a merchant?** Unrecognized entries appear as **🟡 Needs Review**. In Developer Mode, add a merchant rule — **Local** (saved to `local_data/merchants.local.yml`, only for you) or **Public** (saved to `kharchalens/config/merchants.yml`, benefits everyone). Matching transactions are recognized on the next import.

---

## Screenshots

> *Coming soon — add a screenshot or two of the dashboard here.*

---

## Supported Statements

- **HDFC** e-statements in `.xls`, `.xlsx` or `.pdf`.
- **Password-protected PDFs** are supported — enter the password HDFC prompted you to set when downloading your e-statement in the **PDF Password** field.

> ⚠️ **Not affiliated with or endorsed by HDFC Bank.** Always review sensitive statements before sharing them.

---

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python 3.14 for you)
- Any modern browser (macOS / Linux / Windows)

### Run the app

```bash
git clone https://github.com/aakraj/kharchalens.git
cd kharchalens
uv run streamlit run app.py
```

> ⚠️ Run from the **repository root** — merchant rules are resolved relative to the current working directory.

Open the URL Streamlit prints (usually `http://localhost:5000`).

### Import a statement

1. Click **Upload HDFC Statement** and select a `.xls`, `.xlsx` or `.pdf` file.
2. For a password‑protected PDF, enter its password in the **PDF Password** field.
3. Explore the Dashboard, Top Merchants, Categories and Transactions.

---

## Your merchant rules

Rules are plain YAML. **Recognized** merchants ship with the app in `kharchalens/config/merchants.yml`; **your personal** rules live in (gitignored) `local_data/merchants.local.yml`. Developer Mode is the easiest way to add them — [see above](#features).

---

## Tech Stack

- **Streamlit** — interactive UI
- **Python 3.14** — managed with `uv` (hatchling build backend)
- **pdfplumber** — PDF text extraction
- **pandas / plotly** — data and visualizations

---

## Project Structure

```
.
├── app.py                          # Streamlit entrypoint
├── kharchalens/
│   ├── parser/                     # HDFC .xls/.xlsx/.pdf parsing
│   ├── merchant/                   # Merchant resolution + rule store
│   ├── classifier/                 # Transaction categorization
│   ├── analytics/                  # Aggregations, coverage, unknown spending
│   ├── dashboard/                  # Charts, highlights, theme
│   └── config/merchants.yml        # Built-in public merchant rules
├── local_data/merchants.local.yml  # Your personal rules (gitignored)
└── tests/
```

---

## Development

```bash
uv run pytest           # test suite
uv run ruff check .     # linting
uv run mypy kharchalens # strict type-checking
```

---

## Contributing

KharchaLens is open source and welcomes contributions. To get started:

1. Fork the repository and create a feature branch.
2. Make your changes, add or update tests.
3. Run `uv run pytest` to ensure checks pass.
4. Open a pull request describing the change.

Note: because privacy is a priority, contributions that upload or transmit user data will not be accepted.

---

## Security

- **Offline by design** — statements are parsed locally and never uploaded.
- Merchant rules are simple YAML; personal rules never leave your machine.
- If you find a way this app might leak data or misbehave, open an issue on the repository and describe the concern.

---

## License

KharchaLens is released under the [MIT License](LICENSE).

---

Made with **Streamlit**. Not affiliated with HDFC Bank.