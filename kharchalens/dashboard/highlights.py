from __future__ import annotations

from decimal import Decimal

import streamlit as st

from kharchalens.analytics import (
    spending_by_transaction_kind,
    top_merchants,
)
from kharchalens.dashboard.summary import format_inr
from kharchalens.models import Transaction


def render_highlights(
        transactions: list[Transaction],
        summary: dict,
) -> None:
    st.subheader("💡 Highlights")

    savings_rate = Decimal("0")

    if summary["total_credit"] > 0:
        savings_rate = (
            summary["net_cash_flow"] / summary["total_credit"]
        ) * Decimal("100")

    merchants = top_merchants(
        transactions,
        limit=1,
    )

    biggest_merchant = (
        f"{merchants[0][0]} ({format_inr(merchants[0][1])})"
        if merchants
        else "-"
    )

    categories = spending_by_transaction_kind(
        transactions,
    )

    biggest_category = "-"

    if categories:
        biggest_category = max(
            categories.items(),
            key=lambda item: item[1],
        )[0].value

    period = (
        f'{transactions[0].date.strftime("%b %Y")}'
        f" – {transactions[-1].date.strftime("%b %Y")}"
        if transactions
        else "-"
    )

    cards = [
        ("🏪 Highest Merchant", biggest_merchant),
        ("🧾 Top Category", biggest_category),
        ("💰 Savings Rate", f"{savings_rate:.1f}%"),
        ("📅 Statement Period", period),
    ]

    cols = st.columns(4)

    for col, (label, value) in zip(cols, cards):
        col.markdown(
            f'<div class="stat-card">'
            f'<div class="stat-label">{label}</div>'
            f'<div class="stat-value">{value}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )