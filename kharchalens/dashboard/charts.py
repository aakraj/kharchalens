from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from kharchalens.analytics import top_merchants
from kharchalens.models import Transaction, TransactionType


def render_monthly_spending(transactions: list[Transaction]) -> None:
    monthly_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    for transaction in transactions:
        if transaction.transaction_type != TransactionType.DEBIT:
            continue

        month = transaction.date.strftime("%Y-%m")
        monthly_totals[month] += transaction.amount

    if not monthly_totals:
        return

    df = (
        pd.DataFrame(
            {
                "Month": list(monthly_totals.keys()),
                "Spent": [float(v) for v in monthly_totals.values()],
            }
        )
        .sort_values("Month")
    )

    fig = px.bar(
        df,
        x="Month",
        y="Spent",
        text="Spent",
        title="Monthly Spending",
    )

    fig.update_traces(texttemplate="₹%{y:,.0f}")

    st.plotly_chart(fig, use_container_width=True)


def render_top_merchants(transactions: list[Transaction]) -> None:

    merchants = top_merchants(transactions)

    if not merchants:
        return

    df = pd.DataFrame(
        {
            "Merchant": [m for m, _ in merchants],
            "Amount": [float(a) for _, a in merchants],
        }
    )

    fig = px.bar(
        df,
        x="Amount",
        y="Merchant",
        orientation="h",
        text="Amount",
        title="Top Merchants",
    )

    fig.update_traces(texttemplate="₹%{x:,.0f}")

    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)