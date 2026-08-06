from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from kharchalens.analytics import spending_by_transaction_kind
from kharchalens.dashboard.charts import bar_colors
from kharchalens.dashboard.summary import format_inr
from kharchalens.dashboard.theme import ACCENT, MONEY_FONT
from kharchalens.models import Transaction


def render_category_spending(
        transactions: list[Transaction],
) -> None:

    summary = spending_by_transaction_kind(
        transactions,
    )

    if not summary:
        return

    df = pd.DataFrame(
        [
            {
                "Category": kind.value,
                "Amount": float(amount),
            }
            for kind, amount in sorted(
            summary.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        ]
    )

    fig = px.bar(
        df,
        x="Amount",
        y="Category",
        orientation="h",
        text="Amount",
        color_discrete_sequence=[ACCENT],
        title="📊 Spending Breakdown",
    )

    df["Label"] = [
        format_inr(amount)
        for amount in df["Amount"]
    ]

    fig.update_traces(
        text=df["Label"],
        textposition="auto",
        cliponaxis=False,
        marker_line_width=0,
        marker_cornerradius=6,
        marker_color=bar_colors([float(a) for a in df["Amount"]]),
    )

    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=350,
        font={"family": MONEY_FONT, "color": "#1F2937"},
        hoverlabel={"bgcolor": "white", "font_color": "#1F2937"},
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.35,
    )

    st.subheader(
        "Where did you spend money?"
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )