"""
Streamlit dashboard for Metro Romania Personalized Offers Recommender.

Interactive showcase with 6 tabs:
  1. Customer Insights (B2B business types)
  2. Offer Analytics (tiered pricing, offer types)
  3. Model Performance
  4. Feature Drift
  5. Recommendation Explorer
  6. Diversity Metrics

Usage:
    streamlit run src/dashboard.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    DB_PATH, MODELS_DIR, CATEGORY_NAMES, BUSINESS_PROFILES,
    PSI_WARN_THRESHOLD, PSI_ALERT_THRESHOLD, TOP_N_RECOMMENDATIONS,
)
from src.db import get_connection

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Metro Romania Offers Recommender",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_resource
def get_db():
    return get_connection()


@st.cache_data(ttl=60)
def load_table(table_name, query=None):
    conn = get_db()
    if query:
        return pd.read_sql(query, conn)
    return pd.read_sql(f"SELECT * FROM {table_name}", conn)


def color_palette():
    return {
        "horeca": "#FF6B6B",
        "trader": "#4ECDC4",
        "sco": "#45B7D1",
        "freelancer": "#FFA07A",
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("Metro Romania")
st.sidebar.markdown("**B2B Cash & Carry Recommender**")
st.sidebar.markdown("---")

if os.path.exists(str(DB_PATH)):
    db_mb = os.path.getsize(str(DB_PATH)) / (1024 * 1024)
    st.sidebar.metric("Database Size", f"{db_mb:.1f} MB")
    try:
        conn = get_db()
        n_cust = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        n_recs = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
        last_run = conn.execute("SELECT MAX(run_date) FROM recommendations").fetchone()[0]
        st.sidebar.metric("Customers", f"{n_cust:,}")
        st.sidebar.metric("Recommendations", f"{n_recs:,}")
        if last_run:
            st.sidebar.info(f"Last run: {last_run}")
    except Exception as e:
        st.sidebar.error(f"DB error: {e}")
else:
    st.sidebar.warning("Database not found. Run the pipeline first.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Architecture:** Two-stage recommender  \n"
    "Stage 1: Candidate retrieval (~200/customer)  \n"
    "Stage 2: Supervised ranking (LR/LightGBM)  \n"
    "**All prices in RON**"
)

# ---------------------------------------------------------------------------
# Main content - Tabs
# ---------------------------------------------------------------------------

st.title("Metro Romania Personalized Offers Recommender")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Customer Insights",
    "Offer Analytics",
    "Model Performance",
    "Feature Drift",
    "Recommendation Explorer",
    "Diversity Metrics",
])


# =========================================================================
# Tab 1: Customer Insights
# =========================================================================

with tab1:
    st.header("Customer Insights")

    customers = load_table("customers")
    cust_feats = load_table("customer_features")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Customers", f"{len(customers):,}")
    col2.metric("Avg Frequency (90d)", f"{cust_feats['frequency'].mean():.1f}")
    col3.metric("Avg Basket Size", f"{cust_feats['avg_basket_size'].mean():.1f}")
    col4.metric("Avg Promo Affinity", f"{cust_feats['promo_affinity'].mean():.1%}")

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        # Business type distribution
        bt_counts = customers["business_type"].value_counts().reset_index()
        bt_counts.columns = ["business_type", "count"]
        fig = px.pie(
            bt_counts, values="count", names="business_type",
            title="Business Type Distribution",
            color="business_type", color_discrete_map=color_palette(),
            hole=0.4,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Loyalty tier by business type
        loyalty = customers.groupby(["business_type", "loyalty_tier"]).size().reset_index(name="count")
        fig = px.bar(
            loyalty, x="business_type", y="count", color="loyalty_tier",
            title="Loyalty Tiers by Business Type",
            barmode="stack",
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        # Business subtype breakdown
        sub_counts = customers["business_subtype"].value_counts().head(15).reset_index()
        sub_counts.columns = ["business_subtype", "count"]
        fig = px.bar(
            sub_counts, x="count", y="business_subtype",
            orientation="h",
            title="Top 15 Business Subtypes",
            color="count",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        # Tier purchase ratios by business type
        merged = cust_feats.merge(
            customers[["customer_id", "business_type"]], on="customer_id"
        )
        bt_col = "business_type_y" if "business_type_y" in merged.columns else "business_type"
        tier_data = merged.groupby(bt_col).agg({
            "tier2_purchase_ratio": "mean",
            "tier3_purchase_ratio": "mean",
        }).reset_index()
        tier_data.columns = ["business_type", "Tier 2 Ratio", "Tier 3 Ratio"]
        tier_melted = tier_data.melt(id_vars="business_type", var_name="Tier", value_name="Ratio")
        fig = px.bar(
            tier_melted, x="business_type", y="Ratio", color="Tier",
            title="Avg Tier Purchase Ratios by Business Type",
            barmode="group",
            color_discrete_sequence=["#4ECDC4", "#FF6B6B"],
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Category-business_type heatmap
    st.subheader("Category Preferences by Business Type")
    try:
        cat_bt = load_table(
            "cat_bt",
            """
            SELECT c.business_type, p.category, COUNT(*) AS purchase_count
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN customers c ON o.customer_id = c.customer_id
            GROUP BY c.business_type, p.category
            """
        )
        pivot = cat_bt.pivot_table(
            index="category", columns="business_type", values="purchase_count", fill_value=0
        )
        pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100

        fig = px.imshow(
            pivot_pct,
            title="Category Purchase Share by Business Type (%)",
            color_continuous_scale="YlOrRd",
            aspect="auto",
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not generate heatmap: {e}")

    # Purchase mode breakdown
    st.subheader("Purchase Mode: Business vs Individual")
    try:
        pm_data = load_table(
            "pm_data",
            """
            SELECT o.purchase_mode, c.business_type,
                   COUNT(*) AS order_count,
                   AVG(o.total_amount) AS avg_amount,
                   AVG(o.num_items) AS avg_items
            FROM orders o
            JOIN customers c ON o.customer_id = c.customer_id
            GROUP BY o.purchase_mode, c.business_type
            """
        )
        pm1, pm2 = st.columns(2)
        with pm1:
            pm_total = pm_data.groupby("purchase_mode")["order_count"].sum().reset_index()
            fig = px.pie(
                pm_total, values="order_count", names="purchase_mode",
                title="Order Distribution: Business vs Individual",
                color="purchase_mode",
                color_discrete_map={"business": "#4ECDC4", "individual": "#FF6B6B"},
                hole=0.4,
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        with pm2:
            fig = px.bar(
                pm_data, x="business_type", y="avg_amount", color="purchase_mode",
                title="Avg Order Amount by Mode & Business Type (RON)",
                barmode="group",
                color_discrete_map={"business": "#4ECDC4", "individual": "#FF6B6B"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not generate purchase mode charts: {e}")


# =========================================================================
# Tab 2: Offer Analytics
# =========================================================================

with tab2:
    st.header("Offer Analytics")

    offers = load_table("offers")
    offer_feats = load_table("offer_features")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Offers", f"{len(offers):,}")
    col2.metric("Avg Discount Depth", f"{offer_feats['discount_depth'].mean():.1%}")
    col3.metric(
        "Avg Redemption Rate",
        f"{offer_feats['historical_redemption_rate'].mean():.1%}",
    )

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        # Redemption rate by category
        if not offer_feats.empty and "category" in offer_feats.columns:
            cat_rates = (
                offer_feats.groupby("category")["historical_redemption_rate"]
                .mean()
                .sort_values(ascending=True)
                .reset_index()
            )
            fig = px.bar(
                cat_rates, x="historical_redemption_rate", y="category",
                orientation="h",
                title="Avg Redemption Rate by Category",
                color="historical_redemption_rate",
                color_continuous_scale="Greens",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Discount depth vs redemption rate
        if not offer_feats.empty:
            fig = px.scatter(
                offer_feats, x="discount_depth", y="historical_redemption_rate",
                size="total_impressions",
                color="category",
                title="Discount Depth vs Redemption Rate",
                hover_data=["offer_id", "brand"],
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

    # Impressions/redemptions over time
    st.subheader("Impressions & Redemptions Over Time")
    try:
        daily_imp = load_table(
            "daily_imp",
            """
            SELECT DATE(shown_timestamp) AS day, COUNT(*) AS impressions
            FROM impressions GROUP BY DATE(shown_timestamp)
            ORDER BY day
            """
        )
        daily_red = load_table(
            "daily_red",
            """
            SELECT DATE(redeemed_timestamp) AS day, COUNT(*) AS redemptions
            FROM redemptions GROUP BY DATE(redeemed_timestamp)
            ORDER BY day
            """
        )
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=daily_imp["day"], y=daily_imp["impressions"],
                       name="Impressions", line=dict(color="#45B7D1")),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=daily_red["day"], y=daily_red["redemptions"],
                       name="Redemptions", line=dict(color="#FF6B6B")),
            secondary_y=True,
        )
        fig.update_layout(title="Daily Impressions & Redemptions", height=400)
        fig.update_yaxes(title_text="Impressions", secondary_y=False)
        fig.update_yaxes(title_text="Redemptions", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load time series: {e}")

    # Offer type distribution
    c1, c2 = st.columns(2)
    with c1:
        dtype_counts = offers["offer_type"].value_counts().reset_index()
        dtype_counts.columns = ["offer_type", "count"]
        fig = px.pie(
            dtype_counts, values="count", names="offer_type",
            title="Offer Type Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Top performing offers
        top_offers = offer_feats.nlargest(10, "historical_redemption_rate")[
            ["offer_id", "category", "brand", "offer_type", "discount_depth",
             "historical_redemption_rate", "total_impressions"]
        ]
        st.subheader("Top 10 Offers by Redemption Rate")
        st.dataframe(top_offers, use_container_width=True)


# =========================================================================
# Tab 3: Model Performance
# =========================================================================

with tab3:
    st.header("Model Performance")

    artifact_path = MODELS_DIR / "ranker_latest.pkl"
    if artifact_path.exists():
        import joblib
        artifact = joblib.load(artifact_path)
        metrics = artifact.get("metrics", {})

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("LR AUC", f"{metrics.get('lr_auc', 0):.4f}")
        col2.metric("LightGBM AUC", f"{metrics.get('lgbm_auc', 0):.4f}")
        col3.metric("Best Model", metrics.get("best_model", "N/A"))
        col4.metric("Best AUC", f"{metrics.get('best_auc', 0):.4f}")

        st.markdown("---")

        c1, c2 = st.columns(2)

        with c1:
            importance = metrics.get("feature_importance", {})
            if importance:
                imp_df = pd.DataFrame(
                    [{"feature": k, "importance": abs(v)} for k, v in importance.items()]
                ).sort_values("importance", ascending=True)

                fig = px.bar(
                    imp_df, x="importance", y="feature",
                    orientation="h",
                    title="Feature Importance (absolute)",
                    color="importance",
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            comparison = pd.DataFrame([
                {"Model": "Logistic Regression", "AUC": metrics.get("lr_auc", 0),
                 "Train Time (s)": metrics.get("lr_train_time_s", 0)},
                {"Model": "LightGBM", "AUC": metrics.get("lgbm_auc", 0),
                 "Train Time (s)": metrics.get("lgbm_train_time_s", 0)},
            ])
            fig = px.bar(
                comparison, x="Model", y="AUC",
                title="Model Comparison: AUC",
                color="Model",
                color_discrete_sequence=["#FF6B6B", "#4ECDC4"],
                text="AUC",
            )
            fig.update_traces(texttemplate="%{text:.4f}", textposition="outside")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(comparison, use_container_width=True)

        # Offline evaluation metrics
        st.subheader("Offline Evaluation Metrics")
        try:
            eval_row = get_db().execute("""
                SELECT metadata FROM pipeline_runs
                WHERE step = 'evaluate' AND status = 'completed'
                ORDER BY run_date DESC LIMIT 1
            """).fetchone()
            if eval_row and eval_row[0]:
                eval_metrics = json.loads(eval_row[0]) if isinstance(eval_row[0], str) else eval_row[0]
                if isinstance(eval_metrics, dict):
                    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
                    mc1.metric("NDCG@10", f"{eval_metrics.get('ndcg_at_k', 0):.4f}")
                    mc2.metric("Precision@10", f"{eval_metrics.get('precision_at_k', 0):.4f}")
                    mc3.metric("Recall@10", f"{eval_metrics.get('recall_at_k', 0):.4f}")
                    mc4.metric("MRR", f"{eval_metrics.get('mrr', 0):.4f}")
                    mc5.metric("Redemption Rate", f"{eval_metrics.get('redemption_rate_at_k', 0):.4f}")
        except Exception:
            st.info("Run the pipeline to generate evaluation metrics.")
    else:
        st.warning("No model artifact found. Run the training pipeline first.")


# =========================================================================
# Tab 4: Feature Drift
# =========================================================================

with tab4:
    st.header("Feature Drift Monitoring (PSI)")

    try:
        drift_log = load_table("drift_log")

        if drift_log.empty:
            st.info("No drift data available. Run the pipeline to compute drift.")
        else:
            latest_date = drift_log["run_date"].max()
            latest_drift = drift_log[drift_log["run_date"] == latest_date]

            st.subheader(f"Latest Drift Report ({latest_date})")
            for _, row in latest_drift.iterrows():
                icon = "OK" if row["severity"] == "ok" else ("WARN" if row["severity"] == "warn" else "ALERT")
                st.markdown(
                    f"**[{icon}] {row['feature_name']}**: PSI = {row['psi_value']:.4f} ({row['severity']})"
                )

            st.markdown("---")

            c1, c2 = st.columns(2)

            with c1:
                pivot = drift_log.pivot_table(
                    index="feature_name", columns="run_date",
                    values="psi_value", fill_value=0,
                )
                fig = px.imshow(
                    pivot,
                    title="PSI Heatmap Over Time",
                    color_continuous_scale="RdYlGn_r",
                    aspect="auto",
                    zmin=0, zmax=0.5,
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                fig = px.line(
                    drift_log, x="run_date", y="psi_value",
                    color="feature_name",
                    title="PSI Trends by Feature",
                )
                fig.add_hline(
                    y=PSI_WARN_THRESHOLD, line_dash="dash",
                    line_color="orange", annotation_text="Warn (0.10)",
                )
                fig.add_hline(
                    y=PSI_ALERT_THRESHOLD, line_dash="dash",
                    line_color="red", annotation_text="Alert (0.25)",
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            alerts = drift_log[drift_log["severity"] != "ok"]
            if not alerts.empty:
                st.warning(f"{len(alerts)} drift alerts detected across all runs")
                st.dataframe(alerts, use_container_width=True)

    except Exception as e:
        st.warning(f"Could not load drift data: {e}")


# =========================================================================
# Tab 5: Recommendation Explorer
# =========================================================================

with tab5:
    st.header("Recommendation Explorer")

    try:
        conn = get_db()

        sample_customers = pd.read_sql("""
            SELECT DISTINCT r.customer_id, c.business_type, c.business_subtype, c.loyalty_tier
            FROM recommendations r
            JOIN customers c ON r.customer_id = c.customer_id
            LIMIT 200
        """, conn)

        if sample_customers.empty:
            st.info("No recommendations available. Run the pipeline first.")
        else:
            options = [
                f"{row['customer_id']} ({row['business_type']}/{row['business_subtype']}, {row['loyalty_tier']})"
                for _, row in sample_customers.iterrows()
            ]
            selected = st.selectbox("Select a customer:", options)
            customer_id = int(selected.split(" ")[0])

            cust = conn.execute(
                "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
            ).fetchone()
            feats = conn.execute(
                "SELECT * FROM customer_features WHERE customer_id = ?", (customer_id,)
            ).fetchone()

            c1, c2 = st.columns(2)

            with c1:
                st.subheader("Customer Profile")
                if cust:
                    st.markdown(f"**Business:** {cust['business_name']}")
                    st.markdown(f"**Type:** {cust['business_type']} / {cust['business_subtype']}")
                    st.markdown(f"**Loyalty Tier:** {cust['loyalty_tier']}")
                    st.markdown(f"**Home Store:** {cust['home_store_id']}")
                    st.markdown(f"**Metro Card:** {cust['metro_card_number']}")
                    st.markdown(f"**Joined:** {cust['join_date']}")

                if feats:
                    st.markdown("---")
                    st.markdown("**Features (90-day)**")
                    fc1, fc2, fc3 = st.columns(3)
                    fc1.metric("Recency", f"{feats['recency_days']:.0f} days")
                    fc2.metric("Frequency", f"{feats['frequency']}")
                    fc3.metric("Monetary", f"{feats['monetary']:.0f} RON")

                    fc4, fc5, fc6 = st.columns(3)
                    fc4.metric("Promo Affinity", f"{feats['promo_affinity']:.1%}")
                    fc5.metric("Basket Size", f"{feats['avg_basket_size']:.1f}")
                    fc6.metric("Cat Entropy", f"{feats['category_entropy']:.2f}")

                    fc7, fc8, fc9 = st.columns(3)
                    fc7.metric("Tier2 Ratio", f"{feats['tier2_purchase_ratio']:.1%}")
                    fc8.metric("Tier3 Ratio", f"{feats['tier3_purchase_ratio']:.1%}")
                    fc9.metric("Fresh Ratio", f"{feats['fresh_category_ratio']:.1%}")

            with c2:
                if feats and feats["top_3_categories"]:
                    try:
                        top_cats = json.loads(feats["top_3_categories"])
                    except (json.JSONDecodeError, TypeError):
                        top_cats = []

                    if top_cats:
                        cat_data = pd.read_sql("""
                            SELECT p.category, COUNT(*) AS cnt
                            FROM orders o
                            JOIN order_items oi ON o.order_id = oi.order_id
                            JOIN products p ON oi.product_id = p.product_id
                            WHERE o.customer_id = ?
                            GROUP BY p.category
                            ORDER BY cnt DESC
                            LIMIT 10
                        """, conn, params=(customer_id,))

                        if not cat_data.empty:
                            fig = go.Figure(data=go.Scatterpolar(
                                r=cat_data["cnt"].tolist(),
                                theta=cat_data["category"].tolist(),
                                fill="toself",
                                fillcolor="rgba(69, 183, 209, 0.3)",
                                line=dict(color="#45B7D1"),
                            ))
                            fig.update_layout(
                                polar=dict(radialaxis=dict(visible=True)),
                                title="Category Purchase Profile",
                                height=350,
                            )
                            st.plotly_chart(fig, use_container_width=True)

            # Recommendations table
            st.subheader("Top Recommendations")
            recs = pd.read_sql("""
                SELECT
                    r.rank, r.score,
                    p.category, p.brand, p.name AS product,
                    o.offer_type, o.discount_value,
                    p.tier1_price,
                    o.end_date AS expires,
                    cp.strategy
                FROM recommendations r
                JOIN offers o ON r.offer_id = o.offer_id
                JOIN products p ON o.product_id = p.product_id
                LEFT JOIN candidate_pool cp
                    ON r.customer_id = cp.customer_id
                    AND r.offer_id = cp.offer_id
                    AND cp.run_date = r.run_date
                WHERE r.customer_id = ?
                  AND r.run_date = (SELECT MAX(run_date) FROM recommendations)
                ORDER BY r.rank
            """, conn, params=(customer_id,))

            if not recs.empty:
                fig = px.bar(
                    recs, x="rank", y="score",
                    color="category",
                    title="Recommendation Scores by Rank",
                    text="score",
                )
                fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(recs, use_container_width=True)
            else:
                st.info("No recommendations found for this customer.")

    except Exception as e:
        st.error(f"Error loading explorer: {e}")


# =========================================================================
# Tab 6: Diversity Metrics
# =========================================================================

with tab6:
    st.header("Recommendation Diversity")

    try:
        conn = get_db()
        last_run = conn.execute("SELECT MAX(run_date) FROM recommendations").fetchone()[0]

        if last_run is None:
            st.info("No recommendations available.")
        else:
            diversity = pd.read_sql("""
                SELECT r.customer_id, COUNT(DISTINCT p.category) AS n_categories
                FROM recommendations r
                JOIN offers o ON r.offer_id = o.offer_id
                JOIN products p ON o.product_id = p.product_id
                WHERE r.run_date = ?
                GROUP BY r.customer_id
            """, conn, params=(last_run,))

            col1, col2, col3 = st.columns(3)
            col1.metric("Avg Categories/User", f"{diversity['n_categories'].mean():.1f}")
            col2.metric("Min Categories", f"{diversity['n_categories'].min()}")
            col3.metric("Max Categories", f"{diversity['n_categories'].max()}")

            c1, c2 = st.columns(2)

            with c1:
                fig = px.histogram(
                    diversity, x="n_categories",
                    title="Distribution of Unique Categories per Recommendation Set",
                    nbins=10,
                    color_discrete_sequence=["#4ECDC4"],
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            with c2:
                rec_offers = pd.read_sql("""
                    SELECT COUNT(DISTINCT offer_id) AS n_rec_offers FROM recommendations
                    WHERE run_date = ?
                """, conn, params=(last_run,)).iloc[0]["n_rec_offers"]
                total_offers = conn.execute(
                    "SELECT COUNT(*) FROM offers WHERE start_date <= ? AND end_date >= ?",
                    (last_run, last_run),
                ).fetchone()[0]

                coverage = rec_offers / max(total_offers, 1)

                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=coverage * 100,
                    title={"text": "Offer Coverage (%)"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#4ECDC4"},
                        "steps": [
                            {"range": [0, 30], "color": "#FFE5E5"},
                            {"range": [30, 70], "color": "#FFFDE5"},
                            {"range": [70, 100], "color": "#E5FFE5"},
                        ],
                    },
                ))
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

            # Popularity bias
            st.subheader("Popularity Bias Analysis")
            pop_bias = pd.read_sql("""
                SELECT r.offer_id, COUNT(*) AS times_recommended,
                       of2.total_impressions, of2.historical_redemption_rate
                FROM recommendations r
                LEFT JOIN offer_features of2 ON r.offer_id = of2.offer_id
                WHERE r.run_date = ?
                GROUP BY r.offer_id
                ORDER BY times_recommended DESC
            """, conn, params=(last_run,))

            if not pop_bias.empty:
                fig = px.scatter(
                    pop_bias,
                    x="total_impressions",
                    y="times_recommended",
                    size="historical_redemption_rate",
                    title="Recommendation Frequency vs Historical Impressions",
                    hover_data=["offer_id"],
                    color="historical_redemption_rate",
                    color_continuous_scale="Viridis",
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Most Recommended Offers")
                st.dataframe(pop_bias.head(15), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
