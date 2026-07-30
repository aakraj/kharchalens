import tempfile
import re

import pandas as pd
import streamlit as st
import plotly.express as px

from kharchalens.parser import HdfcParser
from kharchalens.dashboard import build_summary
from kharchalens.dashboard.summary import format_inr

st.set_page_config(page_title="KharchaLens", page_icon="💰", layout="wide")

# --- HELPER: MERCHANT EXTRACTOR ---
def extract_merchant(narration):
    """
    Attempts to clean messy Indian bank narrations to find the actual merchant.
    """
    n = str(narration).upper().strip()

    # Handle standard UPI formats (e.g., UPI-ZOMATO@HDFC or UPI/SWIGGY/1234)
    if 'UPI' in n:
        # Split by hyphens or slashes
        parts = re.split(r'[-/]', n)
        if len(parts) > 1:
            # Usually, the second chunk is the merchant name
            merchant = parts[1]
            # Strip out UPI handles like @okhdfcbank
            merchant = merchant.split('@')[0]
            # Remove trailing numbers if any (basic cleanup)
            merchant = re.sub(r'[0-9]+', '', merchant)
            if merchant.strip():
                return merchant.strip()

    # Handle POS/Card purchases (e.g., POS 123456 AMAZON PAY)
    if 'POS' in n or 'PUR' in n:
        # Remove the word POS and the numeric reference that usually follows
        cleaned = re.sub(r'^(POS|PUR)\s*[0-9]*\s*', '', n)
        if cleaned.strip():
            return cleaned.strip()

    # Handle IMPS/NEFT (e.g., NEFT-12345-PERSON NAME)
    if 'NEFT' in n or 'IMPS' in n:
        parts = re.split(r'[-/]', n)
        if len(parts) > 2:
            return parts[2].strip()

    # Fallback: Just return the first 15 characters of the raw narration
    return n[:15].strip()

st.title("💰 KharchaLens")
st.caption("Privacy-first expense intelligence for Indian bank statements")

uploaded = st.file_uploader(
    "Upload HDFC Statement",
    type=["xls", "xlsx", "csv"],
)

if uploaded:
    try:
        if uploaded.name.lower().endswith(".csv"):
            suffix = ".csv"
        elif uploaded.name.lower().endswith(".xlsx"):
            suffix = ".xlsx"
        else:
            suffix = ".xls"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.getvalue())
            temp_file = tmp.name

        parser = HdfcParser()
        transactions = parser.parse(temp_file)
        summary = build_summary(transactions)

        st.success(f"Parsed {len(transactions)} transactions")

        # --- 1. SUMMARY CARDS ---
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("💸 Total Debit", format_inr(summary["total_debit"]))
        col2.metric("💰 Total Credit", format_inr(summary["total_credit"]))
        col3.metric("📈 Net Cash Flow", format_inr(summary["net_cash_flow"]))
        col4.metric("🧾 Transactions", summary["transaction_count"])

        st.divider()

        df = pd.DataFrame(
            [
                {
                    "Date": t.date,
                    "Narration": t.narration,
                    "Amount": t.amount,
                    "Type": t.transaction_type.value if hasattr(t.transaction_type, 'value') else t.transaction_type,
                    "Balance": t.balance,
                }
                for t in transactions
            ]
        )

        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
        # Apply the cleaner function to create a new 'Merchant' column
        df['Merchant'] = df['Narration'].apply(extract_merchant)

        # --- 2. MONTHLY SPENDING CHART ---
        st.subheader("📈 Monthly Spending Trend")

        debits = df[df['Type'].astype(str).str.upper() == 'DEBIT'].copy()

        if not debits.empty:
            debits['Month'] = debits['Date'].dt.to_period('M').astype(str)

            monthly_spend = debits.groupby('Month')['Amount'].sum().reset_index()
            monthly_spend = monthly_spend.sort_values('Month')
            monthly_spend['Formatted_Amount'] = monthly_spend['Amount'].apply(format_inr)

            fig_monthly = px.bar(
                monthly_spend,
                x='Month',
                y='Amount',
                text='Formatted_Amount',
                labels={'Amount': 'Amount (₹)', 'Month': 'Month'},
                color_discrete_sequence=['#ff4b4b']
            )

            fig_monthly.update_traces(
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Amount: %{text}<extra></extra>'
            )

            fig_monthly.update_layout(
                xaxis_title="",
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=(dict(showgrid=True, gridcolor='lightgray')),
                margin=dict(l=0, r=0, t=30, b=0)
            )

            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No debit transactions found to display monthly trends.")

        st.divider()

        # --- 3. TOP MERCHANTS ---
        st.subheader("🏆 Top 10 Merchants")

        if not debits.empty:
            # Group by our new cleaned Merchant column
            top_merchants = debits.groupby('Merchant')['Amount'].sum().reset_index()
            # Sort descending and get top 10
            top_merchants = top_merchants.sort_values('Amount', ascending=False).head(10)
            # Sort ascending just for Plotly so the biggest bar is at the top
            top_merchants = top_merchants.sort_values('Amount', ascending=True)

            top_merchants['Formatted_Amount'] = top_merchants['Amount'].apply(format_inr)

            # Horizontal Bar Chart
            fig_merchants = px.bar(
                top_merchants,
                x='Amount',
                y='Merchant',
                orientation='h',
                text='Formatted_Amount',
                labels={'Amount': 'Amount (₹)', 'Merchant': 'Merchant'},
                color_discrete_sequence=['#4b8bff'] # A nice blue for merchants
            )

            fig_merchants.update_traces(
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Amount: %{text}<extra></extra>'
            )

            fig_merchants.update_layout(
                xaxis_title="",
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=(dict(showgrid=True, gridcolor='lightgray')),
                margin=dict(l=0, r=0, t=30, b=0),
                height=400
            )

            st.plotly_chart(fig_merchants, use_container_width=True)

        st.divider()

        # --- 4. RECENT TRANSACTIONS TABLE ---
        st.subheader("Recent Transactions")

        df_display = df.copy()
        df_display['Date'] = df_display['Date'].dt.strftime('%d-%b-%Y')

        # Rearrange columns so 'Merchant' is right after 'Narration'
        cols = ['Date', 'Narration', 'Merchant', 'Amount', 'Type', 'Balance']
        df_display = df_display[cols]

        st.dataframe(df_display, use_container_width=True)

    except Exception as ex:
        st.exception(ex)