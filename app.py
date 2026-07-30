import tempfile

import pandas as pd
import streamlit as st

from kharchalens.parser import HdfcParser
from kharchalens.dashboard import (
    build_summary,
    render_monthly_spending,
    render_top_merchants,
)

from kharchalens.analytics import (
    merchant_coverage,
    top_unknown_merchants,
)
from kharchalens.dashboard.summary import format_inr

st.set_page_config(page_title="KharchaLens", page_icon="💰", layout="wide")
developer_mode = st.sidebar.checkbox(
    "🛠 Developer Mode",
    value=False,
)

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

        st.divider()
        render_top_merchants(transactions)

        if developer_mode:

            st.divider()
            st.subheader("🛠 Developer Insights")

            coverage = merchant_coverage(transactions)
            c1, c2, c3 = st.columns(3)
            c1.metric("Recognized",coverage.recognized,)
            c2.metric("Unknown",coverage.unknown,)
            c3.metric("Coverage",f"{coverage.coverage:.1f}%",)

            unknown = top_unknown_merchants(transactions)

            if unknown:
                st.markdown("### Top Unknown Merchant Patterns")
                import pandas as pd
                unknown_df = pd.DataFrame(
                    unknown,
                    columns=[
                        "Narration",
                        "Count",
                    ],
                )
                st.dataframe(
                    unknown_df,
                    use_container_width=True,
                    hide_index=True,
                )

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