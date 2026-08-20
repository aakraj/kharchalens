from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from kharchalens.analytics import (
    balance_trajectory,
    monthly_cash_flow,
    top_merchants,
)
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
_SAVINGS = "#7C3AED"


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

    sorted_months = sorted(monthly_totals)
    years = {month[:4] for month in sorted_months}
    show_year = len(years) > 1
    def _month_label(month: str) -> str:
        year, mon = month.split("-")
        return date(int(year), int(mon), 1).strftime(
            "%b %y" if show_year else "%b"
        )

    month_labels = {
        month: _month_label(month)
        for month in sorted_months
    }

    df = (
        pd.DataFrame(
            {
                "Month": sorted_months,
                "MonthLabel": [month_labels[m] for m in sorted_months],
                "Spent": [float(monthly_totals[m]) for m in sorted_months],
                "Label": [format_inr(monthly_totals[m]) for m in sorted_months],
            }
        )
        .sort_values("Month")
    )

    fig = px.bar(
        df,
        x="Month",
        y="Spent",
        text="Label",
        custom_data=["MonthLabel"],
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
        hovertemplate="%{customdata[0]}<br>%{text}<extra></extra>"
    )
    fig.update_layout(
        xaxis={
            "tickmode": "array",
            "tickvals": df["Month"].tolist(),
            "ticktext": df["MonthLabel"].tolist(),
            "tickangle": 0,
            "automargin": True,
        },
        **_LAYOUT,
    )
    st.plotly_chart(fig, width="stretch")


def render_income_expense(transactions: list[Transaction]) -> None:
    rows = monthly_cash_flow(transactions)

    if not rows:
        return

    months = [row["Month"] for row in rows]
    years = {month[:4] for month in months}
    show_year = len(years) > 1

    def _month_label(month: str) -> str:
        year, mon = month.split("-")
        return date(int(year), int(mon), 1).strftime(
            "%b %y" if show_year else "%b"
        )

    labels = {month: _month_label(month) for month in months}

    tidy = pd.DataFrame(
        [
            {
                "Month": row["Month"],
                "MonthLabel": labels[row["Month"]],
                "Series": "Income",
                "Amount": float(row["Income"]),
                "Label": format_inr(row["Income"]),
            }
            for row in rows
        ]
        + [
            {
                "Month": row["Month"],
                "MonthLabel": labels[row["Month"]],
                "Series": "Expense",
                "Amount": float(row["Expense"]),
                "Label": format_inr(row["Expense"]),
            }
            for row in rows
        ]
    )

    fig = px.bar(
        tidy,
        x="Month",
        y="Amount",
        color="Series",
        barmode="group",
        custom_data=["MonthLabel", "Label"],
        color_discrete_map={"Income": TEAL, "Expense": ACCENT},
    )
    fig.update_traces(
        marker_line_width=0,
        marker_cornerradius=6,
        hovertemplate=(
            "%{customdata[0]}<br>%{fullData.name}: "
            "%{customdata[1]}<extra></extra>"
        ),
    )

    savings_labels = [format_inr(row["Savings"]) for row in rows]
    fig.add_trace(
        go.Scatter(
            x=months,
            y=[float(row["Savings"]) for row in rows],
            mode="lines+markers",
            name="Savings",
            customdata=[
                [labels[month], label]
                for month, label in zip(months, savings_labels)
            ],
            line={"color": _SAVINGS, "width": 3},
            marker={"size": 7, "color": _SAVINGS},
            hovertemplate=(
                "%{customdata[0]}<br>Savings: "
                "%{customdata[1]}<extra></extra>"
            ),
        )
    )
    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="rgba(31, 41, 55, 0.35)",
        line_width=1,
    )

    fig.update_layout(
        xaxis={
            "tickmode": "array",
            "tickvals": months,
            "ticktext": [labels[month] for month in months],
            "tickangle": 0,
            "automargin": True,
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.01},
        height=360,
        **_LAYOUT,
    )

    st.subheader("💵 Income vs Expense")
    st.plotly_chart(fig, width="stretch")


def render_balance_trajectory(transactions: list[Transaction]) -> None:
    points = balance_trajectory(transactions)

    if not points:
        return

    df = pd.DataFrame(
        {
            "Date": [point.date for point in points],
            "Balance": [float(point.balance) for point in points],
            "Label": [format_inr(point.balance) for point in points],
        }
    )

    fig = px.area(
        df,
        x="Date",
        y="Balance",
        custom_data=["Label"],
    )
    fig.update_traces(
        line_color=TEAL,
        fillcolor="rgba(13, 148, 136, 0.18)",
        hovertemplate="%{x|%d %b %Y}<br>%{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        height=320,
        xaxis={"rangeslider": {"visible": False}},
        **_LAYOUT,
    )

    st.subheader("💰 Balance Trajectory")
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