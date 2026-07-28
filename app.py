import tempfile

import pandas as pd
import streamlit as st

from kharchalens.parser import HdfcParser

st.set_page_config(page_title="KharchaLens", page_icon="💰")

st.title("💰 KharchaLens")

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

        st.success(f"Parsed {len(transactions)} transactions")

        df = pd.DataFrame(
            [
                {
                    "Date": t.date,
                    "Narration": t.narration,
                    "Amount": t.amount,
                    "Type": t.transaction_type.value,
                    "Balance": t.balance,
                }
                for t in transactions
            ]
        )

        st.dataframe(df, use_container_width=True)

    except Exception as ex:
        st.exception(ex)