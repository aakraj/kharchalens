import tempfile

import pandas as pd
import streamlit as st

from kharchalens.parser import HdfcParser
from kharchalens.dashboard import (
    build_summary,
    render_monthly_spending,
)
from kharchalens.dashboard.summary import format_inr

st.set_page_config(page_title="KharchaLens", page_icon="💰", layout="wide")

st.title("💰 KharchaLens")
st.caption("Privacy-first expense intelligence for Indian bank statements")

uploaded = st.file_uploader(
    "Upload HDFC Statement",
    type=["xls", "xlsx"],
)

if uploaded:
    try:
        suffix = ".xlsx" if uploaded.name.lower().endswith(".xlsx") else ".xls"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            temp_file = tmp.name

        parser = HdfcParser()
        transactions = parser.parse(temp_file)
        summary = build_summary(transactions)

        st.success(f"Parsed {len(transactions)} transactions")
        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "💸 Total Debit",
            format_inr(summary["total_debit"]),
        )

        col2.metric(
            "💰 Total Credit",
            format_inr(summary["total_credit"]),
        )

        col3.metric(
            "📈 Net Cash Flow",
            format_inr(summary["net_cash_flow"]),
        )

        col4.metric(
            "🧾 Transactions",
            summary["transaction_count"],
        )

        st.divider()
        render_monthly_spending(transactions)

        df = pd.DataFrame(
            [
                {
                    "Date": t.date,
                    "Narration": t.narration,
                    "Merchant": t.merchant,
                    "Amount": t.amount,
                    "Type": t.transaction_type.value,
                    "Balance": t.balance,
                }
                for t in transactions
            ]
        )

        st.divider()
        st.subheader("Recent Transactions")
        st.dataframe(
            df,
            use_container_width=True,
            height=500,
        )

    except Exception as ex:
        st.exception(ex)