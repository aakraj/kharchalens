from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

import pandas as pd
import plotly.express as px
import streamlit as st

from kharchalens.analytics import top_merchants
from kharchalens.dashboard.summary import format_inr
from kharchalens.dashboard.theme import ACCENT, MONEY_FONT, TEAL, YELLOW
from kharchalens.models import Transaction, TransactionType

_LAYOUT = {
    "font": {"family": MONEY_FONT, "color": "#1F2937"},
    "hoverlabel": {"bgcolor": "white", "font_color": "#1F2937"},
    "margin": {"l": 20, "r": 20, "t": 30, "b": 20},
    "plot_bgcolor": "rgba(0,0,0,0)",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "bargap": 0.35,
}

_NEEDS_REVIEW = "🟡 Needs Review"

_LIGHT_BLUE = "#93C5FD"
_DEEP_BLUE = "#2563EB"


def _lerp_hex(left: str, right: str, t: float) -> str:
    """Linear blend between two hex colours, t in [0, 1]."""
    a = [int(left[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(right[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(
        f"{round(a[i] + (b[i] - a[i]) * t):02X}" for i in range(3)
    )


def bar_colors(values: list[float]) -> list[str]:
    """Blue gradient by size (light→deep), with the top bars in teal."""
    if not values:
        return []
    distinct = sorted(set(values))
    threshold = distinct[-2] if len(distinct) >= 2 else distinct[0]
    pool = [v for v in values if v < threshold] or values
    vmin, vmax = min(pool), max(pool)
    span = (vmax - vmin) or 1.0
    return [
        TEAL
        if value >= threshold
        else _lerp_hex(_LIGHT_BLUE, _DEEP_BLUE, (value - vmin) / span)
        for value in values
    ]


def render_monthly_spending(transactions: list[Transaction]) -> None:
    st.subheader("📅 Monthly Spending Trend")
    monthly_totals: dict[str, Decimal] = defaultdict(lambda: Decimal(0))

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
                "Label": [
                    format_inr(v)
                    for v in monthly_totals.values()
                ],
            }
        )
        .sort_values("Month")
    )

    fig = px.bar(
        df,
        x="Month",
        y="Spent",
        text="Label",
        color_discrete_sequence=[ACCENT],
    )

    values = [float(v) for v in df["Spent"]]
    fig.update_traces(
        texttemplate="%{text}",
        marker_line_width=0,
        marker_cornerradius=6,
        marker_color=bar_colors(values),
    )
    fig.update_traces(
        hovertemplate="%{y}<br>%{text}<extra></extra>"
    )
    fig.update_layout(**_LAYOUT)
    st.plotly_chart(fig, width="stretch")


def render_top_merchants(transactions: list[Transaction], limit: int | None = None) -> None:
    merchants = top_merchants(transactions,limit=limit)

    if not merchants:
        return

    df = pd.DataFrame(
        {
            "Merchant": [m for m, _ in merchants],
            "Amount": [float(a) for _, a in merchants],
            "Label": [
                format_inr(a)
                for _, a in merchants
            ],
        }
    )

    fig = px.bar(
        df,
        x="Amount",
        y="Merchant",
        orientation="h",
        text="Label",
        color_discrete_sequence=[ACCENT],
    )

    colors = bar_colors([float(a) for _, a in merchants])
    for i, merchant in enumerate(df["Merchant"]):
        if merchant == _NEEDS_REVIEW:
            colors[i] = YELLOW

    fig.update_traces(
        texttemplate="%{text}",
        textposition="auto",
        cliponaxis=False,
        marker_line_width=0,
        marker_cornerradius=6,
        marker_color=colors,
    )
    fig.update_traces(hovertemplate="%{y}<br>%{text}<extra></extra>")
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        height=max(450, len(df) * 35),
    )
    fig.update_layout(**_LAYOUT)

    st.plotly_chart(fig, width="stretch")