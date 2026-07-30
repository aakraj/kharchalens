from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from kharchalens.models import Transaction, TransactionType


def render_monthly_spending(transactions: list[Transaction]) -> None:
    """
    Display monthly debit spending.
    """

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
                "Spent": [float(value) for value in monthly_totals.values()],
            }
        )
        .sort_values("Month")
    )

    fig = px.bar(
        df,
        x="Month",
        y="Spent",
        text="Spent",
    )

    fig.update_traces(texttemplate="₹%{y:,.0f}")

    fig.update_layout(
        title="Monthly Spending",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        height=420,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )