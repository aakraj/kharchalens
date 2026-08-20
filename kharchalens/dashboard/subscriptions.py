from __future__ import annotations

import pandas as pd
import streamlit as st

from kharchalens.analytics import recurring_subscriptions
from kharchalens.dashboard.summary import format_inr
from kharchalens.models import Transaction


def _cadence_label(interval_days: int) -> str:
    if 25 <= interval_days <= 40:
        return "Monthly"
    return f"Every {interval_days}d"


def render_recurring_subscriptions(
        transactions: list[Transaction],
) -> None:
    st.subheader("🔄 Recurring Subscriptions")

    rows = recurring_subscriptions(transactions)

    if not rows:
        st.caption(
            "No recurring payments detected — import more statement months "
            "for better detection."
        )
        return

    df = pd.DataFrame(
        {
            "Merchant": [row.merchant for row in rows],
            "Amount": [format_inr(row.amount) for row in rows],
            "Cadence": [_cadence_label(row.interval_days) for row in rows],
            "Occurrences": [row.occurrences for row in rows],
            "Monthly Cost": [format_inr(row.monthly_cost) for row in rows],
            "Annual Cost": [format_inr(row.annual_cost) for row in rows],
        }
    )

    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "Debits that repeat to the same merchant at a roughly monthly "
        "cadence with a stable amount."
    )