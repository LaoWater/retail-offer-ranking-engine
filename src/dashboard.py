"""
Streamlit dashboard for Metro Personalized Offers Recommender.

Interactive showcase with 6 tabs:
  1. Customer Insights
  2. Offer Analytics
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

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    DB_PATH, MODELS_DIR, CATEGORY_NAMES, SEGMENT_PROFILES,
    PSI_WARN_THRESHOLD, PSI_ALERT_THRESHOLD, TOP_N_RECOMMENDATIONS,
)
from src.db import get_connection

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Metro Offers Recommender",
    page_icon="🛒",
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
        "budget": "#FF6B6B",
        "premium": "#4ECDC4",
        "family": "#45B7D1",
        "horeca": "#FFA07A",
    }


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("Metro Offers Recommender")
st.sidebar.markdown("---")

# DB status
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
    "Stage 2: Supervised ranking (LR/LightGBM)"
)

# ---------------------------------------------------------------------------
# Main content - Tabs
# ---------------------------------------------------------------------------

st.title("Metro Personalized Offers Recommender")

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
        # Segment distribution
        seg_counts = customers["segment"].value_counts().reset_index()
        seg_counts.columns = ["segment", "count"]
        fig = px.pie(
            seg_counts, values="count", names="segment",
            title="Customer Segment Distribution",
            color="segment", color_discrete_map=color_palette(),
            hole=0.4,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Loyalty tier by segment
        loyalty = customers.groupby(["segment", "loyalty_tier"]).size().reset_index(name="count")
        fig = px.bar(
            loyalty, x="segment", y="count", color="loyalty_tier",
            title="Loyalty Tiers by Segment",
            barmode="stack",
            color_discrete_sequence=px.colors.sequential.Teal,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        # Purchase frequency by segment
        merged = cust_feats.merge(customers[["customer_id", "segment"]], on="customer_id", suffixes=("_feat", "_cust"))
        seg_col = "segment_cust" if "segment_cust" in merged.columns else "segment"
        fig = px.histogram(
            merged, x="frequency", color=seg_col,
            title="Purchase Frequency (90d) by Segment",
            barmode="overlay", opacity=0.7, nbins=30,
            color_discrete_map=color_palette(),
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        # Basket size by segment
        fig = px.box(
            merged, x=seg_col, y="avg_basket_size",
            title="Average Basket Size by Segment",
            color=seg_col, color_discrete_map=color_palette(),
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Category-segment heatmap
    st.subheader("Category Preferences by Segment")
    try:
        cat_seg = load_table(
            "cat_seg",
            """
            SELECT c.segment, p.category, COUNT(*) AS purchase_count
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN customers c ON o.customer_id = c.customer_id
            GROUP BY c.segment, p.category
            """
        )
        pivot = cat_seg.pivot_table(
            index="category", columns="segment", values="purchase_count", fill_value=0
        )
        # Normalize to percentages per segment
        pivot_pct = pivot.div(pivot.sum(axis=0), axis=1) * 100

        fig = px.imshow(
            pivot_pct,
            title="Category Purchase Share by Segment (%)",
            color_continuous_scale="YlOrRd",
            aspect="auto",
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not generate heatmap: {e}")


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
        # Discount depth vs redemption rate scatter
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

    # Daily impressions/redemptions over time
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

    # Discount type distribution
    c1, c2 = st.columns(2)
    with c1:
        dtype_counts = offers["discount_type"].value_counts().reset_index()
        dtype_counts.columns = ["discount_type", "count"]
        fig = px.pie(
            dtype_counts, values="count", names="discount_type",
            title="Discount Type Distribution",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        # Top performing offers
        top_offers = offer_feats.nlargest(10, "historical_redemption_rate")[
            ["offer_id", "category", "brand", "discount_depth", "historical_redemption_rate", "total_impressions"]
        ]
        st.subheader("Top 10 Offers by Redemption Rate")
        st.dataframe(top_offers, use_container_width=True)


# =========================================================================
# Tab 3: Model Performance
# =========================================================================

with tab3:
    st.header("Model Performance")

    # Load model artifact
    artifact_path = MODELS_DIR / "ranker_latest.pkl"
    if artifact_path.exists():
        import joblib
        artifact = joblib.load(artifact_path)
        metrics = artifact.get("metrics", {})

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("LR AUC", f"{metrics.get('lr_auc', 0):.4f}")
        col2.metric("LightGBM AUC", f"{metrics.get('lgbm_auc', 0):.4f}")
        col3.metric("Best Model", metrics.get("best_model", "N/A"))
        col4.metric("Best AUC", f"{metrics.get('best_auc', 0):.4f}")

        st.markdown("---")

        c1, c2 = st.columns(2)

        with c1:
            # Feature importance
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
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            # Model comparison bar chart
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

        # Offline evaluation metrics (if available)
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
            # Current drift summary
            latest_date = drift_log["run_date"].max()
            latest_drift = drift_log[drift_log["run_date"] == latest_date]

            st.subheader(f"Latest Drift Report ({latest_date})")
            for _, row in latest_drift.iterrows():
                icon = "🟢" if row["severity"] == "ok" else ("🟡" if row["severity"] == "warn" else "🔴")
                st.markdown(
                    f"{icon} **{row['feature_name']}**: PSI = {row['psi_value']:.4f} ({row['severity']})"
                )

            st.markdown("---")

            c1, c2 = st.columns(2)

            with c1:
                # PSI heatmap over time
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
                # PSI line chart with thresholds
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

            # Alert summary
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

        # Customer selector
        sample_customers = pd.read_sql("""
            SELECT DISTINCT r.customer_id, c.segment, c.loyalty_tier
            FROM recommendations r
            JOIN customers c ON r.customer_id = c.customer_id
            LIMIT 200
        """, conn)

        if sample_customers.empty:
            st.info("No recommendations available. Run the pipeline first.")
        else:
            options = [
                f"{row['customer_id']} ({row['segment']}, {row['loyalty_tier']})"
                for _, row in sample_customers.iterrows()
            ]
            selected = st.selectbox("Select a customer:", options)
            customer_id = int(selected.split(" ")[0])

            # Customer profile
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
                    st.markdown(f"**Segment:** {cust['segment']}")
                    st.markdown(f"**Loyalty Tier:** {cust['loyalty_tier']}")
                    st.markdown(f"**Home Store:** {cust['home_store_id']}")
                    st.markdown(f"**Joined:** {cust['join_date']}")

                if feats:
                    st.markdown("---")
                    st.markdown("**Features (90-day)**")
                    fc1, fc2, fc3 = st.columns(3)
                    fc1.metric("Recency", f"{feats['recency_days']:.0f} days")
                    fc2.metric("Frequency", f"{feats['frequency']}")
                    fc3.metric("Monetary", f"€{feats['monetary']:.0f}")

                    fc4, fc5, fc6 = st.columns(3)
                    fc4.metric("Promo Affinity", f"{feats['promo_affinity']:.1%}")
                    fc5.metric("Basket Size", f"{feats['avg_basket_size']:.1f}")
                    fc6.metric("Cat Entropy", f"{feats['category_entropy']:.2f}")

            with c2:
                # Category affinity radar chart
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
                    o.discount_type, o.discount_value,
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
                # Score distribution
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
            # Unique categories per customer's top-N
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
                # Offer coverage: what % of offers appear in any recommendation?
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

                # Top recommended offers
                st.subheader("Most Recommended Offers")
                st.dataframe(pop_bias.head(15), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
