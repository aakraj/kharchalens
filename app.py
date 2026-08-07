import tempfile
from decimal import Decimal
from pathlib import Path

import pandas as pd
import streamlit as st

from kharchalens.analytics import merchant_coverage, unknown_spending
from kharchalens.dashboard import (
    apply_theme,
    build_summary,
    render_category_spending,
    render_footer,
    render_highlights,
    render_merchant_summary,
    render_monthly_spending,
    render_top_merchants,
)
from kharchalens.dashboard.summary import format_inr
from kharchalens.enrichment import TransactionEnricher
from kharchalens.merchant.preprocessing import NarrationPreprocessor
from kharchalens.merchant.rule_store import MerchantRuleStore
from kharchalens.parser import (
    HdfcParser,
    HdfcPdfParser,
    PdfIncorrectPassword,
    PdfPasswordRequired,
)
from kharchalens.utils.date_utils import format_date

st.set_page_config(page_title="KharchaLens", page_icon="💰", layout="wide")
apply_theme()

_RULES_PATHS = (
    Path(__file__).parent / "kharchalens" / "config" / "merchants.yml",
    Path.cwd() / "local_data" / "merchants.local.yml",
)


def _rules_signature() -> str:
    """Hash of the merchant-rule files, so a rule save busts the parse cache."""
    import hashlib

    digest = hashlib.sha256()
    for path in _RULES_PATHS:
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()


@st.cache_data(show_spinner=False, max_entries=8)
def _parse_statement(
        file_bytes: bytes,
        suffix: str,
        password: str | None,
        rules_signature: str,
) -> list:
    """Parse and enrich a statement once; cached so reruns skip the slow work."""
    enricher = TransactionEnricher()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        temp_file = tmp.name

    if suffix == ".pdf":
        transactions = HdfcPdfParser().parse(temp_file, password=password)
    else:
        transactions = HdfcParser().parse(temp_file)

    return [
        enricher.enrich_transaction(t)
        for t in transactions
    ]


hero, dev_col = st.columns([3, 0.9], vertical_alignment="center")

with hero:
    st.markdown(
        '<div class="hero">'
        "<h1>💰 KharchaLens</h1>"
        "<p>Privacy-first expense intelligence for Indian bank statements.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

with dev_col:
    developer_mode = st.toggle(
        "🛠 Developer Mode",
        value=False,
        key="developer_mode",
        help=(
            "Turn this on to see how well KharchaLens recognized your "
            "transactions, review the ones it couldn't classify, and teach it "
            "new merchant rules. Leave it off for a clean view. Switching it "
            "on lands you directly on the Developer tab."
        ),
    )

_prev_dev = st.session_state.get("_dev_prev", False)
if developer_mode and not _prev_dev:
    st.session_state["active_view_sel"] = "🛠 Developer"
st.session_state["_dev_prev"] = developer_mode

uploaded = st.file_uploader("Upload HDFC Statement", type=["xls", "xlsx", "pdf"])

if uploaded:
    suffix = Path(uploaded.name).suffix.lower() if Path(uploaded.name).suffix else ".xls"

    pdf_password = None
    if suffix == ".pdf":
        pdf_password = st.text_input(
            "🔒 PDF Password",
            type="password",
            key="pdf_password",
            autocomplete="on",
            width=280,
            help=(
                "Only needed for password-protected statements. This is the "
                "password HDFC asked you to set when downloading the "
                "e-statement (often your first-name initial + the last 4 "
                "digits of your customer ID)."
            ),
        ) or None

    try:
        if suffix == ".pdf":
            with st.spinner("Parsing PDF statement… this can take a few seconds"):
                transactions = _parse_statement(
                    uploaded.getvalue(), suffix, pdf_password, _rules_signature()
                )
        else:
            transactions = _parse_statement(
                uploaded.getvalue(), suffix, None, _rules_signature()
            )

        summary = build_summary(transactions)

#==========================================================================================
# Dashboard Tab
#==========================================================================================
        _label_to_view = {
            "📊 Dashboard": "dashboard",
            "📄 Transactions": "transactions",
            "🛠 Developer": "developer",
        }
        view_options = ["📊 Dashboard", "📄 Transactions"]
        if developer_mode:
            view_options.append("🛠 Developer")
        _current = st.session_state.get("active_view_sel", "📊 Dashboard")
        if _current not in view_options:
            _current = "📊 Dashboard"
        st.session_state["active_view_sel"] = _current
        _choice = st.radio(
            "View",
            options=view_options,
            key="active_view_sel",
            label_visibility="collapsed",
            horizontal=True,
        )
        view = _label_to_view.get(_choice, "dashboard")
        if view == "developer" and not developer_mode:
            view = "dashboard"
            st.session_state["active_view_sel"] = "📊 Dashboard"

        if view == "dashboard":
            start_date = min(t.date for t in transactions)
            end_date = max(t.date for t in transactions)
            st.success(
                "📄 HDFC Statement • "
                f"{len(transactions)} transactions • "
                f"{start_date.strftime('%d %b %Y')} – "
                f"{end_date.strftime('%d %b %Y')}"
            )
            st.caption(
                "⚠️ Parsed automatically — some amounts, dates, or merchants "
                "may occasionally be misread. Verify against your original "
                "statement."
            )

            col1, col2, col3, col4 = st.columns(4)
            total_credit = summary["total_credit"]
            total_debit = summary["total_debit"]
            col1.metric("💰 Total Credit", format_inr(total_credit))
            col2.metric("💸 Total Debit", format_inr(total_debit))
            col3.metric("📈 Saved", format_inr(summary["net_cash_flow"]))

            if total_credit > Decimal(0):
                savings_rate = ((total_credit - total_debit)/ total_credit) * Decimal(100)
            else:
                savings_rate = Decimal(0)
            col4.metric("📊 Savings Rate",f"{savings_rate:.1f}%")

            #==========================================
            render_monthly_spending(transactions)
            st.subheader("🏪 Top Merchants")
            selection = st.radio("Merchant ranking", ["Top 10", "Top 20", "Top 50", "All"], horizontal=True, label_visibility="collapsed")
            limit_map = {"Top 10": 10, "Top 20": 20, "Top 50": 50, "All": None}
            limit = limit_map[selection]
            render_top_merchants(transactions, limit)
            render_merchant_summary(transactions, limit)
            render_category_spending(transactions)
            render_highlights(transactions,summary)
            #==========================================

#==========================================================================================
# Developer tab
#==========================================================================================
        elif view == "developer":
            st.subheader("🛠 Developer Insights")
            st.info(
                "**When to use this tab:** switch on **Developer Mode** "
                "(top-right toggle) to inspect how KharchaLens classified "
                "your transactions. Use it when you want to —\n\n"
                "- **Improve merchant recognition** by teaching it new "
                "merchants for transactions it didn't recognize.\n"
                "- **Check coverage** — see how many transactions were "
                "matched vs. left as *Unknown*.\n"
                "- **Debug a statement** — confirm the parser picked up the "
                "right number of transactions and amounts.\n\n"
                "It doesn't change how your data is processed; it only "
                "surfaces extra detail."
            )
            st.warning(
                "**Disclaimer:** KharchaLens parses bank statements "
                "automatically and may occasionally go wrong. Amounts, "
                "dates, or merchants can be misread, and some transactions "
                "may not be detected correctly — especially with complex "
                "or multi-line narrations, PDFs that aren't well laid out, "
                "or table structure changes. Treat the output as a "
                "starting point and verify against your original "
                "statement, especially for exact balances or tax purposes."
            )
            coverage = merchant_coverage(transactions)
            c1, c2, c3 = st.columns(3)
            c1.metric("Recognized Merchants",coverage.recognized,)
            c2.metric("Unknown Merchants",coverage.unknown,)
            c3.metric("Coverage",f"{coverage.coverage:.1f}%",)
            unknown_spd = unknown_spending(transactions)

            if unknown_spd:
                st.info(
                    """
                💡 **Help KharchaLens get smarter**
                
                Review unknown transactions below and create merchant rules.
                
                - **Local** → Saves the rule only on your computer (recommended for family, friends, local shops, or private transactions).
                - **Public** → Contributes a generic merchant rule that can benefit all KharchaLens users.
                
                Once a rule is saved, matching transactions will be recognised automatically in future imports and will disappear from this list.
                """
                )
                st.markdown("### 💸 Top Unknown Spending")
                known_merchants = MerchantRuleStore.merchant_names()
                local_merchants = MerchantRuleStore.merchant_sources(local=True)
                _local_suffix = " (Local)"

                merchant_options = [
                    f"{m}{_local_suffix}" if m in local_merchants else m
                    for m in known_merchants
                ] + ["✍️ Add new merchant…"]
                header = st.columns([1, 0.8, 4.2, 2.2, 2.5, 1, 0.8])

                header[0].markdown("**Spend**")
                header[1].markdown("**Freq**")
                header[2].markdown("**Narration**")
                header[3].markdown("**Merchant**")
                header[4].markdown("**Keyword**")
                header[5].markdown("**Local**")
                header[6].markdown("**Save**")

                for item in unknown_spd[:20]:
                    cols = st.columns([1, 0.8, 4.2, 2.2, 2.5, 1, 0.8])
                    cols[0].write(format_inr(item.total_spend))
                    cols[1].write(item.transactions)
                    cols[2].write(item.narration)

                    merchant_sel = cols[3].selectbox(
                        "Merchant",
                        merchant_options,
                        key=f"merchant_sel_{item.narration}",
                        index=None,
                        placeholder="Select a merchant…",
                        label_visibility="collapsed",
                    )
                    if merchant_sel == "✍️ Add new merchant…":
                        merchant = cols[3].text_input(
                            "New merchant name",
                            key=f"merchant_new_{item.narration}",
                            placeholder="Type merchant name…",
                            label_visibility="collapsed",
                        )
                        local_default = st.session_state.get(
                            f"local_{item.narration}", True
                        )
                    elif merchant_sel is None:
                        merchant = ""
                        local_default = st.session_state.get(
                            f"local_{item.narration}", True
                        )
                    else:
                        merchant = merchant_sel
                        if merchant.endswith(_local_suffix):
                            merchant = merchant.rstrip()[: -len(_local_suffix)]
                        local_default = merchant in local_merchants
                        st.session_state[f"local_{item.narration}"] = local_default

                    keyword = cols[4].text_input("Keyword", value=NarrationPreprocessor.extract_keyword(item.narration), key=f"keyword_{item.narration}", label_visibility="collapsed")
                    local = cols[5].toggle("Save locally", value=local_default, key=f"local_{item.narration}", label_visibility="collapsed")

                    if cols[6].button("➕ Add", key=f"save_{item.narration}"):
                        if not merchant:
                            st.toast("Pick or enter a merchant first.", icon="⚠️")
                        else:
                            MerchantRuleStore.add_rule(merchant=merchant, keyword=keyword, local=local)
                            st.toast("Rule saved.")
                            st.rerun()
#==========================================================================================
# Transactions Tab
#==========================================================================================
        else:
            df = pd.DataFrame(
                [
                    {
                        "Date": format_date(t.date),
                        "Narration": t.narration,
                        "Merchant": t.merchant,
                        "Amount": t.amount,
                        "Type": t.transaction_type.value,
                        "Balance": t.balance,
                    }
                    for t in transactions
                ]
            )
            search_col, type_col, merchant_col = st.columns([3, 1, 2])
            query = search_col.text_input(
                "🔍 Search", key="txn_search", placeholder="Search narration or merchant…"
            )
            tx_type = type_col.selectbox(
                "Type",
                ["All", "DEBIT", "CREDIT"],
                key="txn_type_filter",
            )
            merchants = sorted(m for m in df["Merchant"].dropna().unique() if m != "Unknown")
            merchants = ["All"] + merchants
            merchant_filter = merchant_col.selectbox(
                "Merchant", merchants, key="txn_merchant_filter"
            )
            filtered = df
            if query:
                mask = (
                    df["Narration"].str.contains(query, case=False, na=False)
                    | df["Merchant"].str.contains(query, case=False, na=False)
                )
                filtered = df[mask]
            if tx_type != "All":
                filtered = filtered[filtered["Type"] == tx_type]
            if merchant_filter != "All":
                filtered = filtered[filtered["Merchant"] == merchant_filter]
            st.caption(f"{len(filtered)} of {len(df)} transactions")
            st.divider()
            st.subheader("📜 Recent Transactions")
            st.dataframe(
                filtered,
                width="stretch",
                height=500,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Narration": st.column_config.TextColumn("Narration", width="large"),
                    "Merchant": st.column_config.TextColumn("Merchant", width="medium"),
                    "Amount": st.column_config.NumberColumn("Amount", format="₹%.2f", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Balance": st.column_config.NumberColumn("Balance", format="₹%.2f", width="small"),
                },
            )

        render_footer()

    except PdfPasswordRequired:
        st.error(
            "🔒 This PDF statement is password-protected. Enter its "
            "password in the PDF Password field above."
        )
    except PdfIncorrectPassword:
        st.error("🔒 The password is incorrect. Please try again.")
    except Exception as ex:  # noqa: BLE001 - surface any error in the UI
        st.exception(ex)