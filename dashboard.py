# =============================================================
# dashboard.py
# Streamlit Interactive Dashboard
#
# HOW TO RUN:
#   streamlit run dashboard.py
# Then open: http://localhost:8501
# =============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ── Page settings ──────────────────────────────────────────────
st.set_page_config(
    page_title="TEYZIX CORE - Marketing Attribution",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load all data (cached so it only runs once) ────────────────
@st.cache_data
def load_all_data():
    """Run the full pipeline and return all datasets."""
    # Use absolute path based on this file location
    # This works both locally and on Streamlit Cloud
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "data", "category_tree.csv")

    from data_pipeline import run_pipeline
    from attribution_models import run_all_models

    cat_df, tp = run_pipeline(csv_path=csv_path)
    results    = run_all_models(tp)
    return cat_df, tp, results

# Show a spinner while data loads
with st.spinner("Loading data and running attribution models..."):
    cat_df, tp, results = load_all_data()

# Useful constants
CHANNELS = sorted(tp["channel"].unique().tolist())
MODELS   = results["model"].unique().tolist()
COLORS   = ["#3366CC", "#DC3912", "#FF9900", "#109618", "#990099"]

BUDGETS = {
    "Organic Search":    45000,
    "Paid Social":       30000,
    "Email Marketing":   20000,
    "Display Ads":       25000,
    "Direct / Referral": 15000,
}

# ── Sidebar ────────────────────────────────────────────────────
st.sidebar.image("https://via.placeholder.com/200x60?text=TEYZIX+CORE", width=200)
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to section:",
    ["🏠 Overview", "📊 Attribution Models", "💰 Budget Analysis",
     "🔗 Markov Chain", "📈 Journey Analysis", "📋 Data"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Task:** DA-2 | Multi-Touch Attribution")
st.sidebar.markdown("**Domain:** Data Analytics")
st.sidebar.markdown("**Dataset:** category_tree.csv")


# ================================================================
# PAGE: OVERVIEW
# ================================================================
if page == "🏠 Overview":

    st.title("📊 TEYZIX CORE – Marketing Attribution Dashboard")
    st.markdown("**Task DA-2** | Multi-Touch Marketing Attribution Analysis")
    st.markdown("---")

    # ── KPI metrics ──────────────────────────────────────────
    total_journeys  = tp["journey_id"].nunique()
    conv_journeys   = tp[tp["converted"] == True]["journey_id"].nunique()
    conv_rate       = conv_journeys / total_journeys
    total_touches   = len(tp)
    total_revenue   = tp[(tp["converted"] == True) & (tp["is_last"] == True)]["revenue"].sum()
    avg_touches     = tp.groupby("journey_id")["touch_order"].max().mean()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Journeys",     f"{total_journeys:,}")
    col2.metric("Conversions",        f"{conv_journeys:,}")
    col3.metric("Conversion Rate",    f"{conv_rate:.1%}")
    col4.metric("Total Touchpoints",  f"{total_touches:,}")
    col5.metric("Total Revenue",      f"${total_revenue:,.0f}")

    st.markdown("---")

    # ── Dataset information ───────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📁 Dataset Information")
        st.info("""
        **Provided Dataset:** `category_tree.csv`
        - 1,669 product categories
        - Hierarchical parent-child structure
        - 25 root categories (depth 0)
        - Max depth: 5 levels

        **How it's used:**
        Category depth is mapped to marketing channels:
        - Depth 0 → Organic Search
        - Depth 1 → Paid Social
        - Depth 2 → Email Marketing
        - Depth 3 → Display Ads
        - Depth 4+ → Direct / Referral

        **Synthetic Data:** 1,500 customer journeys generated
        using category tree topology as seed.
        *(Labeled: data_source = SYNTHETIC)*
        """)

    with col_right:
        st.subheader("🔍 Attribution Models")
        st.success("""
        **5 Models Implemented:**

        1. **First-Touch** – 100% credit to first channel
        2. **Last-Touch** – 100% credit to last channel
        3. **Linear** – Equal credit across all channels
        4. **Time-Decay** – More credit to recent channels
        5. **Markov Chain** – Statistical removal effect *(Bonus)*

        Each model tells a different story about which
        channels are most important in the customer journey.
        """)

    st.markdown("---")

    # ── Category tree depth chart ─────────────────────────────
    st.subheader("📂 Category Tree Structure")
    depth_counts = cat_df["depth"].value_counts().sort_index().reset_index()
    depth_counts.columns = ["Depth", "Count"]
    depth_counts["Channel"] = depth_counts["Depth"].map({
        0: "Organic Search",
        1: "Paid Social",
        2: "Email Marketing",
        3: "Display Ads",
        4: "Direct / Referral",
        5: "Direct / Referral",
    })

    fig = px.bar(
        depth_counts,
        x="Depth", y="Count", color="Channel",
        title="Number of Categories per Depth Level → Marketing Channel Mapping",
        color_discrete_sequence=COLORS,
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title="Tree Depth", yaxis_title="Number of Categories")
    st.plotly_chart(fig, use_container_width=True)


# ================================================================
# PAGE: ATTRIBUTION MODELS
# ================================================================
elif page == "📊 Attribution Models":

    st.title("📊 Attribution Models")
    st.markdown("Compare how each model assigns credit to marketing channels.")
    st.markdown("---")

    # ── Model selector ────────────────────────────────────────
    selected_model = st.selectbox("Select a model to explore:", MODELS)
    model_df = results[results["model"] == selected_model].copy()
    model_df = model_df.sort_values("credit", ascending=False)

    st.subheader(f"Results: {selected_model}")

    col1, col2 = st.columns(2)

    with col1:
        # Attribution credit bar chart
        fig1 = px.bar(
            model_df,
            x="channel", y="credit",
            color="channel",
            color_discrete_sequence=COLORS,
            title=f"{selected_model} – Attribution Credit per Channel",
            labels={"credit": "Attribution Credit", "channel": "Channel"},
            text=model_df["credit"].apply(lambda x: f"{x:.1%}"),
        )
        fig1.update_yaxes(tickformat=".0%")
        fig1.update_traces(textposition="outside")
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Revenue bar chart
        fig2 = px.bar(
            model_df,
            x="channel", y="revenue",
            color="channel",
            color_discrete_sequence=COLORS,
            title=f"{selected_model} – Attributed Revenue per Channel",
            labels={"revenue": "Revenue ($)", "channel": "Channel"},
            text=model_df["revenue"].apply(lambda x: f"${x:,.0f}"),
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ── All models side-by-side comparison ───────────────────
    st.subheader("All Models Comparison")

    # Exclude Markov from this chart (different scale)
    compare_df = results[results["model"] != "Markov Chain"]

    fig3 = px.bar(
        compare_df,
        x="channel", y="credit",
        color="model",
        barmode="group",
        title="Attribution Credit – All 4 Standard Models Side by Side",
        labels={"credit": "Attribution Credit", "channel": "Channel", "model": "Model"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig3.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ── Heatmap ───────────────────────────────────────────────
    st.subheader("Attribution Heatmap (All Models vs All Channels)")

    pivot = results.pivot_table(
        index="model",
        columns="channel",
        values="credit",
        aggfunc="mean"
    ).fillna(0)

    fig4 = px.imshow(
        pivot,
        text_auto=".1%",
        color_continuous_scale="Blues",
        title="Heatmap: How much credit does each model give each channel?",
        aspect="auto",
    )
    fig4.update_layout(xaxis_title="Channel", yaxis_title="Model")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # ── Model explanation table ───────────────────────────────
    st.subheader("Model Descriptions")
    explanation = pd.DataFrame({
        "Model":       ["First-Touch", "Last-Touch", "Linear", "Time-Decay", "Markov Chain"],
        "How it works":["100% to first channel", "100% to last channel",
                        "Equal split across all", "More to recent channels",
                        "Removal effect probability"],
        "Best for":    ["Awareness measurement", "Conversion measurement",
                        "Balanced view", "Short sales cycles",
                        "Strategic budget decisions"],
        "Limitation":  ["Ignores rest of journey", "Ignores upper funnel",
                        "Ignores recency", "May undervalue awareness",
                        "Needs enough data"],
    })
    st.table(explanation)


# ================================================================
# PAGE: BUDGET ANALYSIS
# ================================================================
elif page == "💰 Budget Analysis":

    st.title("💰 Budget Analysis & Recommendations")
    st.markdown("Compare current budget allocation vs what attribution models suggest.")
    st.markdown("---")

    budget_model = st.selectbox("Select model for budget analysis:", MODELS)

    # Get credit values for selected model
    bdf = results[results["model"] == budget_model].copy()
    bdf["current_budget"]     = bdf["channel"].map(BUDGETS)
    total_budget              = sum(BUDGETS.values())
    bdf["budget_share"]       = bdf["current_budget"] / total_budget
    bdf["roi_score"]          = bdf["credit"] / bdf["budget_share"]
    bdf["recommended_budget"] = (bdf["credit"] * total_budget).round(0)
    bdf["budget_change"]      = bdf["recommended_budget"] - bdf["current_budget"]

    # ── ROI Score chart ───────────────────────────────────────
    st.subheader("ROI Score per Channel")
    st.caption("ROI Score > 1.0 = channel outperforms its budget (underinvested) | < 1.0 = overinvested")

    fig5 = px.bar(
        bdf.sort_values("roi_score"),
        x="roi_score", y="channel",
        orientation="h",
        color="roi_score",
        color_continuous_scale="RdYlGn",
        title="ROI Score: Attribution Credit vs Budget Share",
        labels={"roi_score": "ROI Score", "channel": "Channel"},
        text=bdf.sort_values("roi_score")["roi_score"].apply(lambda x: f"{x:.2f}"),
    )
    fig5.add_vline(x=1.0, line_dash="dash", line_color="black", annotation_text="Balanced (1.0)")
    fig5.update_traces(textposition="outside")
    st.plotly_chart(fig5, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Current vs recommended budget
        budget_compare = pd.melt(
            bdf[["channel", "current_budget", "recommended_budget"]],
            id_vars="channel",
            var_name="type",
            value_name="amount"
        )
        budget_compare["type"] = budget_compare["type"].map({
            "current_budget": "Current",
            "recommended_budget": "Recommended"
        })

        fig6 = px.bar(
            budget_compare,
            x="channel", y="amount",
            color="type",
            barmode="group",
            title="Current vs Recommended Budget",
            labels={"amount": "Budget ($)", "channel": "Channel", "type": ""},
            color_discrete_sequence=["#3366CC", "#FF9900"],
            text=budget_compare["amount"].apply(lambda x: f"${x:,.0f}"),
        )
        fig6.update_traces(textposition="outside")
        st.plotly_chart(fig6, use_container_width=True)

    with col2:
        # Budget change waterfall-style bar
        colors_change = ["#109618" if x > 0 else "#DC3912" for x in bdf["budget_change"]]
        fig7 = px.bar(
            bdf,
            x="channel", y="budget_change",
            title="Recommended Budget Change ($)",
            labels={"budget_change": "Change ($)", "channel": "Channel"},
            text=bdf["budget_change"].apply(lambda x: f"+${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}"),
        )
        fig7.update_traces(
            marker_color=colors_change,
            textposition="outside"
        )
        fig7.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")

    # ── Recommendations table ─────────────────────────────────
    st.subheader("Budget Recommendations Table")

    rec_table = bdf[["channel", "current_budget", "recommended_budget", "budget_change", "roi_score"]].copy()
    rec_table.columns = ["Channel", "Current ($)", "Recommended ($)", "Change ($)", "ROI Score"]
    rec_table["Action"] = rec_table["Change ($)"].apply(
        lambda x: "⬆ Increase" if x > 200 else ("⬇ Reduce" if x < -200 else "✓ Keep")
    )
    rec_table["ROI Score"] = rec_table["ROI Score"].round(2)

    # Format numbers
    for col in ["Current ($)", "Recommended ($)"]:
        rec_table[col] = rec_table[col].apply(lambda x: f"${x:,.0f}")
    rec_table["Change ($)"] = rec_table["Change ($)"].apply(
        lambda x: f"+${x:,.0f}" if x >= 0 else f"-${abs(x):,.0f}"
    )

    st.dataframe(rec_table, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Budget scatter ────────────────────────────────────────
    st.subheader("Budget vs Attribution Credit")

    fig8 = px.scatter(
        bdf,
        x="current_budget",
        y="credit",
        size="revenue",
        color="channel",
        text="channel",
        title="Current Budget vs Attribution Credit (bubble size = attributed revenue)",
        labels={"current_budget": "Current Budget ($)", "credit": "Attribution Credit"},
        color_discrete_sequence=COLORS,
    )
    fig8.update_traces(textposition="top center")
    fig8.update_yaxes(tickformat=".0%")
    fig8.update_layout(showlegend=False)
    st.plotly_chart(fig8, use_container_width=True)


# ================================================================
# PAGE: MARKOV CHAIN
# ================================================================
elif page == "🔗 Markov Chain":

    st.title("🔗 Markov Chain Attribution (Bonus)")
    st.markdown("---")

    st.info("""
    ### How Markov Chain Attribution Works

    1. We build a **probability map** of how customers move between channels
    2. For each channel, we **remove** it from all journeys and re-simulate
    3. We measure how much the **conversion rate drops** without that channel
    4. Bigger drop = that channel is more important = gets more credit
    5. This is called the **Removal Effect**
    """)

    markov_df = results[results["model"] == "Markov Chain"].copy()

    col1, col2 = st.columns(2)

    with col1:
        # Credit bar chart
        fig9 = px.bar(
            markov_df.sort_values("credit", ascending=True),
            x="credit", y="channel",
            orientation="h",
            color="credit",
            color_continuous_scale="Blues",
            title="Markov Chain – Attribution Credit per Channel",
            labels={"credit": "Attribution Credit", "channel": "Channel"},
            text=markov_df.sort_values("credit", ascending=True)["credit"].apply(lambda x: f"{x:.1%}"),
        )
        fig9.update_xaxes(tickformat=".0%")
        fig9.update_traces(textposition="outside")
        st.plotly_chart(fig9, use_container_width=True)

    with col2:
        # Removal effect bar chart
        fig10 = px.bar(
            markov_df.sort_values("removal_effect", ascending=True),
            x="removal_effect", y="channel",
            orientation="h",
            color="removal_effect",
            color_continuous_scale="Reds",
            title="Removal Effect – How much does CR drop without this channel?",
            labels={"removal_effect": "Conversion Rate Drop", "channel": "Channel"},
            text=markov_df.sort_values("removal_effect", ascending=True)["removal_effect"].apply(lambda x: f"{x:.4f}"),
        )
        fig10.update_traces(textposition="outside")
        st.plotly_chart(fig10, use_container_width=True)

    st.markdown("---")

    # ── Markov vs Linear comparison ───────────────────────────
    st.subheader("Markov Chain vs Linear – Which channels differ most?")

    linear_df = results[results["model"] == "Linear"][["channel", "credit"]].rename(columns={"credit": "Linear"})
    markov_c  = markov_df[["channel", "credit"]].rename(columns={"credit": "Markov Chain"})
    comp      = linear_df.merge(markov_c, on="channel")
    comp_melt = comp.melt(id_vars="channel", var_name="Model", value_name="Credit")

    fig11 = px.bar(
        comp_melt,
        x="channel", y="Credit",
        color="Model",
        barmode="group",
        title="Linear vs Markov Chain Attribution Credit",
        labels={"Credit": "Attribution Credit", "channel": "Channel"},
        color_discrete_sequence=["#3366CC", "#DC3912"],
        text=comp_melt["Credit"].apply(lambda x: f"{x:.1%}"),
    )
    fig11.update_yaxes(tickformat=".0%")
    fig11.update_traces(textposition="outside")
    st.plotly_chart(fig11, use_container_width=True)

    st.markdown("---")

    # ── Key insight ───────────────────────────────────────────
    st.subheader("Key Insight from Markov Chain")
    top_channel = markov_df.sort_values("removal_effect", ascending=False).iloc[0]["channel"]
    top_effect  = markov_df.sort_values("removal_effect", ascending=False).iloc[0]["removal_effect"]
    st.success(f"""
    **Most critical channel: {top_channel}**

    Removing **{top_channel}** from all customer journeys causes the biggest
    drop in conversion rate (removal effect = {top_effect:.4f}).

    This means {top_channel} is structurally the most important channel —
    even if traditional models like Last-Touch give it less credit.

    **Recommendation:** Do NOT cut budget for {top_channel} based only on
    last-touch metrics. The Markov Chain analysis shows it plays a critical
    role in enabling conversions.
    """)


# ================================================================
# PAGE: JOURNEY ANALYSIS
# ================================================================
elif page == "📈 Journey Analysis":

    st.title("📈 Customer Journey Analysis")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        # Conversion funnel
        total_j  = tp["journey_id"].nunique()
        conv_j   = tp[tp["converted"] == True]["journey_id"].nunique()
        total_t  = len(tp)

        funnel = pd.DataFrame({
            "Stage": ["Total Touchpoints", "Total Journeys", "Converted Journeys"],
            "Count": [total_t, total_j, conv_j]
        })
        fig12 = px.funnel(
            funnel, x="Count", y="Stage",
            title="Conversion Funnel",
            color_discrete_sequence=["#3366CC"]
        )
        st.plotly_chart(fig12, use_container_width=True)

    with col2:
        # Touchpoint share donut chart
        ch_counts = tp.groupby("channel").size().reset_index(name="count")
        fig13 = px.pie(
            ch_counts,
            names="channel",
            values="count",
            title="Touchpoint Share by Channel",
            color_discrete_sequence=COLORS,
            hole=0.45,
        )
        st.plotly_chart(fig13, use_container_width=True)

    st.markdown("---")

    col3, col4 = st.columns(2)

    with col3:
        # Journey length histogram
        journey_len = tp.groupby("journey_id")["touch_order"].max().reset_index(name="length")
        fig14 = px.histogram(
            journey_len,
            x="length",
            nbins=6,
            title="How long are customer journeys? (number of touchpoints)",
            labels={"length": "Number of Touchpoints", "count": "Number of Journeys"},
            color_discrete_sequence=["#3366CC"],
        )
        fig14.update_layout(bargap=0.1)
        st.plotly_chart(fig14, use_container_width=True)

    with col4:
        # Conversion rate by journey length
        journey_len["converted"] = journey_len["journey_id"].map(
            tp.groupby("journey_id")["converted"].first()
        )
        conv_by_len = journey_len.groupby("length").agg(
            total=("journey_id", "count"),
            converted=("converted", "sum")
        ).reset_index()
        conv_by_len["conv_rate"] = conv_by_len["converted"] / conv_by_len["total"]

        fig15 = px.bar(
            conv_by_len,
            x="length", y="conv_rate",
            title="Conversion Rate by Journey Length",
            labels={"length": "Number of Touchpoints", "conv_rate": "Conversion Rate"},
            color="conv_rate",
            color_continuous_scale="Greens",
            text=conv_by_len["conv_rate"].apply(lambda x: f"{x:.1%}"),
        )
        fig15.update_yaxes(tickformat=".0%")
        fig15.update_traces(textposition="outside")
        st.plotly_chart(fig15, use_container_width=True)

    st.markdown("---")

    # Monthly trend
    st.subheader("Monthly Conversions Trend")
    monthly = (
        tp[(tp["converted"] == True) & (tp["is_last"] == True)]
        .groupby("month")["journey_id"]
        .count()
        .reset_index(name="conversions")
    )
    fig16 = px.line(
        monthly, x="month", y="conversions",
        markers=True,
        title="Number of Conversions per Month (2025)",
        labels={"month": "Month", "conversions": "Conversions"},
        color_discrete_sequence=["#3366CC"],
    )
    fig16.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig16, use_container_width=True)

    st.markdown("---")

    # Channel performance comparison: converted vs non-converted
    st.subheader("Channel Appearance: Converted vs Non-Converted Journeys")

    ch_conv     = tp[tp["converted"] == True].groupby("channel").size().reset_index(name="converted")
    ch_nonconv  = tp[tp["converted"] == False].groupby("channel").size().reset_index(name="not_converted")
    ch_compare  = ch_conv.merge(ch_nonconv, on="channel")
    ch_melt     = ch_compare.melt(id_vars="channel", var_name="journey_type", value_name="count")

    fig17 = px.bar(
        ch_melt,
        x="channel", y="count",
        color="journey_type",
        barmode="group",
        title="How often does each channel appear in converted vs non-converted journeys?",
        labels={"count": "Number of Touches", "channel": "Channel", "journey_type": "Journey Type"},
        color_discrete_sequence=["#109618", "#DC3912"],
    )
    st.plotly_chart(fig17, use_container_width=True)


# ================================================================
# PAGE: DATA
# ================================================================
elif page == "📋 Data":

    st.title("📋 Data Tables")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Attribution Results", "Touchpoints", "Category Tree"])

    with tab1:
        st.subheader("Attribution Results (all models)")

        # Filter by model
        model_filter = st.multiselect("Filter by model:", MODELS, default=MODELS)
        filtered = results[results["model"].isin(model_filter)].copy()

        # Format for display
        display = filtered.copy()
        display["credit"]  = display["credit"].apply(lambda x: f"{x:.1%}")
        display["revenue"] = display["revenue"].apply(lambda x: f"${x:,.0f}")
        if "removal_effect" in display.columns:
            display["removal_effect"] = display["removal_effect"].apply(
                lambda x: f"{x:.5f}" if pd.notna(x) else "-"
            )

        st.dataframe(display, use_container_width=True, hide_index=True)

        # Download button
        csv = filtered.to_csv(index=False)
        st.download_button(
            "📥 Download Results as CSV",
            data=csv,
            file_name="attribution_results.csv",
            mime="text/csv"
        )

    with tab2:
        st.subheader("Customer Journey Touchpoints (Synthetic Data)")
        st.caption("data_source = SYNTHETIC — generated from category tree topology")

        # Filters
        ch_filter = st.multiselect("Filter by channel:", CHANNELS, default=CHANNELS)
        conv_filter = st.checkbox("Show only converted journeys", value=False)

        filtered_tp = tp[tp["channel"].isin(ch_filter)]
        if conv_filter:
            filtered_tp = filtered_tp[filtered_tp["converted"] == True]

        st.dataframe(filtered_tp.head(200), use_container_width=True, hide_index=True)
        st.caption(f"Showing first 200 rows of {len(filtered_tp):,} total")

    with tab3:
        st.subheader("Category Tree Dataset (Provided by TEYZIX CORE)")
        st.caption("Source: category_tree.csv — 1,669 category hierarchy records")
        st.dataframe(cat_df, use_container_width=True, hide_index=True)

        csv_cat = cat_df.to_csv(index=False)
        st.download_button(
            "📥 Download Enriched Category Tree",
            data=csv_cat,
            file_name="category_tree_enriched.csv",
            mime="text/csv"
        )
