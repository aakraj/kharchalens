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
        {
            "icon": "🏪",
            "label": "Highest Merchant",
            "value": biggest_merchant,
            "accent": "#2563EB",
            "soft": "rgba(37, 99, 235, 0.12)",
        },
        {
            "icon": "🧾",
            "label": "Top Category",
            "value": biggest_category,
            "accent": "#0D9488",
            "soft": "rgba(13, 148, 136, 0.12)",
        },
        {
            "icon": "💰",
            "label": "Savings Rate",
            "value": f"{savings_rate:.1f}%",
            "accent": "#7C3AED",
            "soft": "rgba(124, 58, 237, 0.12)",
        },
        {
            "icon": "📅",
            "label": "Statement Period",
            "value": period,
            "accent": "#D97706",
            "soft": "rgba(217, 119, 6, 0.12)",
        },
    ]

    cols = st.columns(4)

    for col, card in zip(cols, cards):
        bar = ""
        if card["label"] == "Savings Rate":
            bar = (
                f'<div class="hl-bar"><div style="width:'
                f"{min(100.0, float(savings_rate))}%\"></div></div>"
            )
        col.markdown(
            (
                f'<div class="hl-card" style="--hl-accent:{card["accent"]};'
                f'--hl-accent-soft:{card["soft"]}">'
                f'<div class="hl-top">'
                f'<div class="hl-ico">{card["icon"]}</div>'
                f'<div class="hl-label">{card["label"]}</div>'
                f"</div>"
                f'<div class="hl-value">{card["value"]}</div>'
                f"{bar}"
                f"</div>"
            ),
            unsafe_allow_html=True,
        )