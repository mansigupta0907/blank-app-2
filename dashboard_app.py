"""
Candy Sales Dashboard - Streamlit App
--------------------------------------
Recreates two report pages:
  1. Product Performance (Top products by sales, Profit by product,
     Units sold by type, Cost vs Gross Profit scatter)
  2. Regional Analysis (Sales by state, Profit by region,
     Avg lead time by region, Sales vs Profit by region)

HOW TO RUN:
  1. Install requirements:  pip install streamlit pandas plotly
  2. Run:  streamlit run dashboard_app.py
  3. Upload your CSV in the sidebar. The app lets you map your own
     column names to the fields each chart needs, so it works even
     if your file uses different header names.

Beginner note: every section below is commented so you can see what
each block of code is doing and tweak it later.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------------------------------------------------------------
# 1. PAGE CONFIG - sets the browser tab title, layout, etc.
#    This must be the first Streamlit command in the script.
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Candy Sales Dashboard",
    page_icon="🍫",
    layout="wide",
)

st.title("🍫 Candy Sales Dashboard")

# ----------------------------------------------------------------------
# 2. DATA UPLOAD
#    st.file_uploader lets the user drop a CSV in from the browser.
#    We cache the loaded dataframe so re-running the app doesn't
#    re-read the file every time a widget changes.
# ----------------------------------------------------------------------
st.sidebar.header("1. Upload your data")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])


@st.cache_data
def load_data(file):
    return pd.read_csv(file)


if uploaded_file is None:
    st.info("⬅️ Upload a CSV file in the sidebar to get started.")
    st.caption(
        "Expected kinds of columns: Product, Sales, Profit, Cost, Units, "
        "Product Type/Category, State, Region, Lead Time."
    )
    st.stop()  # halts the script here until a file is uploaded

df = load_data(uploaded_file)

with st.expander("Preview raw data"):
    st.dataframe(df.head(20))

# ----------------------------------------------------------------------
# 3. COLUMN MAPPING
#    Real-world CSVs rarely use the exact column names a chart needs.
#    Instead of hardcoding names, we let the user pick which of their
#    columns maps to each concept via dropdowns in the sidebar.
#    "— none —" lets a chart be skipped if that data isn't available.
# ----------------------------------------------------------------------
st.sidebar.header("2. Map your columns")

columns = ["— none —"] + list(df.columns)


def pick(label, guesses):
    """Show a selectbox, pre-selecting the first column name that
    roughly matches one of the guessed keywords (case-insensitive)."""
    default_index = 0
    for i, col in enumerate(columns):
        if col == "— none —":
            continue
        if any(g.lower() in col.lower() for g in guesses):
            default_index = i
            break
    return st.sidebar.selectbox(label, columns, index=default_index)

col_product = pick("Product name", ["product", "item"])
col_sales = pick("Sales / Revenue", ["sales", "revenue", "amount"])
col_profit = pick("Profit", ["profit"])
col_cost = pick("Cost", ["cost"])
col_units = pick("Units sold", ["units", "boxes", "qty", "quantity"])
col_type = pick("Product type/category", ["type", "category"])
col_state = pick("State", ["state"])
col_region = pick("Region", ["region"])
col_leadtime = pick("Lead time (days)", ["lead", "days"])

def has(col):
    return col != "— none —"

# ----------------------------------------------------------------------
# 4. PAGE NAVIGATION
#    A simple radio button in the sidebar switches between the two
#    report pages, mirroring the "Page 3" / "Page 4" layout.
# ----------------------------------------------------------------------
st.sidebar.header("3. Choose a page")
page = st.sidebar.radio("Go to", ["Product Performance", "Regional Analysis"])

# ------------------------------------------------------------------
# Helper to lay out four charts in a 2x2 grid, like the source pages
# ------------------------------------------------------------------
def four_chart_grid(fig1, title1, fig2, title2, fig3, title3, fig4, title4):
    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader(title1)
        st.plotly_chart(fig1, use_container_width=True)
    with row1_col2:
        st.subheader(title2)
        st.plotly_chart(fig2, use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.subheader(title3)
        st.plotly_chart(fig3, use_container_width=True)
    with row2_col2:
        st.subheader(title4)
        st.plotly_chart(fig4, use_container_width=True)


# ========================================================================
# PAGE 3 EQUIVALENT: PRODUCT PERFORMANCE
# ========================================================================
if page == "Product Performance":
    st.header("Product Performance")

    charts = []

    # --- Chart 1: Top 8 products by sales (horizontal bar) ---
    if has(col_product) and has(col_sales):
        top_products = (
            df.groupby(col_product)[col_sales]
            .sum()
            .sort_values(ascending=False)
            .head(8)
            .reset_index()
        )
        fig1 = px.bar(
            top_products.sort_values(col_sales),
            x=col_sales, y=col_product, orientation="h",
            color_discrete_sequence=["#E07B1B"],
        )
        fig1.update_layout(yaxis_title="", xaxis_title="Sales $")
    else:
        fig1 = px.bar(title="Need Product + Sales columns")

    # --- Chart 2: Profit by product ---
    if has(col_product) and has(col_profit):
        profit_products = (
            df.groupby(col_product)[col_profit]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )
        fig2 = px.bar(
            profit_products, x=col_product, y=col_profit,
            color_discrete_sequence=["#6AA84F"],
        )
        fig2.update_layout(xaxis_title="", yaxis_title="Profit $")
        fig2.update_xaxes(tickangle=-30)
    else:
        fig2 = px.bar(title="Need Product + Profit columns")

    # --- Chart 3: Units sold by product type ---
    if has(col_type) and has(col_units):
        units_by_type = (
            df.groupby(col_type)[col_units].sum().reset_index()
        )
        fig3 = px.bar(
            units_by_type, x=col_type, y=col_units,
            color=col_type,
        )
        fig3.update_layout(xaxis_title="", yaxis_title="Units", showlegend=False)
        total_units = int(df[col_units].sum())
        st.caption(f"**Total units sold: {total_units:,}**")
    else:
        fig3 = px.bar(title="Need Type + Units columns")

    # --- Chart 4: Cost vs Gross Profit scatter ---
    if has(col_cost) and has(col_profit):
        fig4 = px.scatter(
            df, x=col_cost, y=col_profit,
            opacity=0.6,
            color_discrete_sequence=["#4C78A8"],
        )
        fig4.update_layout(xaxis_title="Cost $", yaxis_title="Gross Profit $")
    else:
        fig4 = px.scatter(title="Need Cost + Profit columns")

    four_chart_grid(
        fig1, "Top 8 Products by Sales",
        fig2, "Profit by Product",
        fig3, "Units Sold by Type",
        fig4, "Cost vs Gross Profit",
    )

# ========================================================================
# PAGE 4 EQUIVALENT: REGIONAL ANALYSIS
# ========================================================================
else:
    st.header("Regional Analysis")

    # --- Chart 1: Sales by state, top 10 ---
    if has(col_state) and has(col_sales):
        top_states = (
            df.groupby(col_state)[col_sales]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig1 = px.bar(
            top_states, x=col_state, y=col_sales,
            color_discrete_sequence=["#1F4E79"],
        )
        fig1.update_layout(xaxis_title="", yaxis_title="Sales $")
    else:
        fig1 = px.bar(title="Need State + Sales columns")

    # --- Chart 2: Profit by region ---
    if has(col_region) and has(col_profit):
        profit_region = (
            df.groupby(col_region)[col_profit].sum().sort_values(ascending=False).reset_index()
        )
        fig2 = px.bar(
            profit_region, x=col_region, y=col_profit,
            color=col_region,
        )
        fig2.update_layout(xaxis_title="", yaxis_title="Profit $", showlegend=False)
    else:
        fig2 = px.bar(title="Need Region + Profit columns")

    # --- Chart 3: Avg lead time by region ---
    if has(col_region) and has(col_leadtime):
        lead_region = (
            df.groupby(col_region)[col_leadtime].mean().reset_index()
        )
        fig3 = px.bar(
            lead_region, x=col_region, y=col_leadtime,
            color_discrete_sequence=["#D2691E"],
        )
        fig3.update_layout(xaxis_title="", yaxis_title="Days")
        overall_avg = df[col_leadtime].mean()
        st.caption(f"**Overall average lead time: {overall_avg:.1f} days**")
    else:
        fig3 = px.bar(title="Need Region + Lead Time columns")

    # --- Chart 4: Sales vs Profit bubble chart by region ---
    if has(col_region) and has(col_sales) and has(col_profit):
        region_summary = (
            df.groupby(col_region)
            .agg({col_sales: "sum", col_profit: "sum"})
            .reset_index()
        )
        fig4 = px.scatter(
            region_summary, x=col_sales, y=col_profit,
            text=col_region, size=col_sales,
            color=col_region,
        )
        fig4.update_traces(textposition="top center")
        fig4.update_layout(
            xaxis_title="Sales $", yaxis_title="Profit $", showlegend=False
        )
    else:
        fig4 = px.scatter(title="Need Region + Sales + Profit columns")

    four_chart_grid(
        fig1, "Sales by State (Top 10)",
        fig2, "Profit by Region",
        fig3, "Avg Lead Time by Region",
        fig4, "Sales vs Profit by Region",
    )
