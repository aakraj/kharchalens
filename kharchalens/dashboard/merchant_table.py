from __future__ import annotations

import pandas as pd
import streamlit as st

from kharchalens.analytics import merchant_summary
from kharchalens.dashboard.summary import format_inr
from kharchalens.dashboard.theme import YELLOW_SOFT
from kharchalens.models import Transaction

_NEEDS_REVIEW = "🟡 Needs Review"


def render_merchant_summary(
        transactions: list[Transaction],
        limit: int | None = None
) -> None:

    rows = merchant_summary(transactions, limit=limit)

    if not rows:
        return

    df = pd.DataFrame(rows)

    df["Spend"] = df["Spend"].apply(format_inr)

    df["Average"] = df["Average"].apply(format_inr)

    if limit is None:
        heading = "All Merchants"
    else:
        heading = f"Top {limit} Merchants"
    st.subheader(f"📋 {heading}")
    st.caption("Spend, number of transactions and average spend per merchant.")

    needs_review_rows = df["Merchant"] == _NEEDS_REVIEW
    if needs_review_rows.any():
        df = df.style.apply(
            lambda row: [
                f"background-color: {YELLOW_SOFT};"
                if row["Merchant"] == _NEEDS_REVIEW else ""
                for _ in row
            ],
            axis=1,
        )

    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
    )