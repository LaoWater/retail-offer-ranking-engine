# Metro Personalized Offers Recommender
## Engineering Showcase & ML Interview Project Specification

**Repository:** [`retail-offer-ranking-engine`](https://github.com/LaoWater/retail-offer-ranking-engine.git)

**Version:** 1.0  
**Last Updated:** February 2026  
**Project Type:** ML Interview Showcase / Educational Demo

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Context & Objectives](#problem-context--objectives)
3. [System Architecture Overview](#system-architecture-overview)
4. [Data Model & Schema Design](#data-model--schema-design)
5. [Phase 1: Core Implementation (2-5 Days)](#phase-1-core-implementation-2-5-days)
6. [Phase 2: Modernization & Research Track](#phase-2-modernization--research-track)
7. [Repository Structure](#repository-structure)
8. [Development Workflow](#development-workflow)
9. [Team Roles & Task Breakdown](#team-roles--task-breakdown)
10. [Demo Day Script](#demo-day-script)
11. [Interview Preparation Guide](#interview-preparation-guide)
12. [Technical Dependencies](#technical-dependencies)
13. [Success Metrics](#success-metrics)

---

## Executive Summary

### What We're Building

A **production-realistic personalized offer recommendation system** for Metro (supermarket chain) that demonstrates modern ML engineering practices through a fully reproducible, end-to-end pipeline.

### Key Differentiators

- **Two-stage recommender pattern** (candidate generation → ranking) — industry standard approach
- **Realistic data simulation** with seasonality, customer segments, and promotional behavior
- **Complete MLOps lifecycle** including training, serving, evaluation, and drift monitoring
- **Interview-ready architecture** that demonstrates both practical engineering and theoretical depth

### Technology Stack (Phase 1)

- **Storage:** SQLite (demo), Supabase-ready (production)
- **ML:** scikit-learn / LightGBM
- **API:** FastAPI + Pydantic
- **Monitoring:** PSI-based drift detection
- **Deployment:** Single-command batch pipeline

### Timeline

- **Phase 1 (Core):** 2-5 days, fully functional demo
- **Phase 2 (Research):** 1-2 weeks, modern deep learning upgrades

---

## Problem Context & Objectives

### Business Context

**Client:** Metro (European supermarket/wholesale chain)  
**Domain:** Retail personalization, promotional targeting  
**Existing System:** Legacy recommender in production for 6-7 years (batch-first, older algorithms)

### Business Objectives

1. **Increase redemption rate** of personalized offers
2. **Optimize promotional spending** by targeting high-propensity customers
3. **Improve customer satisfaction** through relevant recommendations
4. **Measure incremental lift** from discounts (not just correlation with purchase history)

### Technical Objectives (This Showcase)

1. Build a **reproducible, educational demo** that mirrors real-world architecture
2. Demonstrate **end-to-end ML pipeline** from raw data to served predictions
3. Implement **monitoring and evaluation** patterns used in production systems
4. Show clear **upgrade path** to modern deep learning approaches (Phase 2)

### Constraints & Design Decisions

| Constraint | Design Choice | Rationale |
|------------|---------------|-----------|
| Must run locally | SQLite + local Python | Reproducible in minutes |
| Interview timeline | 2-5 day Phase 1 | Demonstrates core competency without overengineering |
| Must be explainable | Start with LR/GBDT ranker | Interpretable baseline before deep models |
| Real-world patterns | Two-stage architecture | Standard industry practice (retrieval → ranking) |

---

## System Architecture Overview

### High-Level Flow

```
┌─────────────────┐
│  Raw Data Gen   │  generate_data.py → SQLite (warehouse simulation)
│  (Simulation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Engine  │  features.py → Customer/Offer/Interaction features
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Candidate Gen  │  candidates.py → ~200 eligible offers per user
│  (Retrieval)    │  (Category affinity, segment rules, store scope)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Ranker       │  train_ranker.py + score_ranker.py
│  (Supervised)   │  → Predict P(redemption) → Top-N per user
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Recommendations │  recommendations(run_date, customer_id, offer_id, score, rank)
│     Table       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │  GET /recommendations?customer_id=X
│   (Serving)     │  → Returns today's precomputed offers (Pydantic models)
└─────────────────┘
```

### Monitoring & Evaluation (Parallel Tracks)

```
┌─────────────────┐
│ Offline Eval    │  evaluate.py → NDCG@10, Redemption Rate@N, MRR
└─────────────────┘

┌─────────────────┐
│ Drift Detection │  drift.py → PSI on feature distributions
└─────────────────┘
```

### Pipeline Orchestration

```bash
# Single command daily run
python src/daily_run.py --date 2026-02-11

# Steps executed:
# 1. Refresh features (incremental update)
# 2. Train or load model (retraining cadence: weekly)
# 3. Generate candidates (~200/user via heuristics)
# 4. Score candidates with ranker
# 5. Write top-N to recommendations table
# 6. Compute drift metrics (alert if PSI > threshold)
```

---

## Data Model & Schema Design

### Core Tables (SQLite)

#### 1. `customers`
```sql
CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    segment TEXT NOT NULL,  -- 'budget', 'premium', 'family', 'horeca'
    home_store_id INTEGER NOT NULL,
    join_date DATE NOT NULL,
    loyalty_tier TEXT,  -- 'bronze', 'silver', 'gold'
    email_consent BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Core customer identity + segmentation for targeting rules.

#### 2. `products`
```sql
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,  -- 'dairy', 'produce', 'bakery', 'meat', etc.
    subcategory TEXT,
    brand TEXT,
    base_price REAL NOT NULL,
    margin REAL,  -- Gross margin % (for business-aware ranking)
    shelf_life_days INTEGER,  -- For perishable goods
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Product catalog with business attributes (margin) for uplift modeling.

#### 3. `orders`
```sql
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    order_timestamp TIMESTAMP NOT NULL,
    total_amount REAL NOT NULL,
    num_items INTEGER NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
```

**Purpose:** Transaction-level metadata for RFM features.

#### 4. `order_items`
```sql
CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    is_promo BOOLEAN DEFAULT 0,  -- Was discount applied?
    discount_amount REAL DEFAULT 0.0,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

**Purpose:** Basket-level detail for category affinity + promo sensitivity.

#### 5. `offers`
```sql
CREATE TABLE offers (
    offer_id INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL,
    discount_type TEXT NOT NULL,  -- 'percentage', 'fixed_amount', 'bogo'
    discount_value REAL NOT NULL,  -- e.g., 20 (for 20% off) or 5.00 (for $5 off)
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    store_scope TEXT,  -- NULL = all stores, or comma-separated store IDs
    segment_scope TEXT,  -- NULL = all segments, or 'premium,family'
    max_redemptions INTEGER,  -- Budget cap
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

**Purpose:** Active promotional inventory with eligibility rules.

#### 6. `impressions`
```sql
CREATE TABLE impressions (
    impression_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    shown_timestamp TIMESTAMP NOT NULL,
    channel TEXT,  -- 'email', 'app', 'in-store'
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id)
);
```

**Purpose:** What was shown to users (enables learning from exposure, not just redemption).

#### 7. `redemptions`
```sql
CREATE TABLE redemptions (
    redemption_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    redeemed_timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

**Purpose:** Ground truth labels for supervised learning (shown → redeemed).

#### 8. `recommendations` (Output)
```sql
CREATE TABLE recommendations (
    recommendation_id INTEGER PRIMARY KEY,
    run_date DATE NOT NULL,
    customer_id INTEGER NOT NULL,
    offer_id INTEGER NOT NULL,
    score REAL NOT NULL,  -- Model's predicted P(redemption)
    rank INTEGER NOT NULL,  -- 1 = top recommendation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (offer_id) REFERENCES offers(offer_id),
    UNIQUE(run_date, customer_id, offer_id)
);
```

**Purpose:** Precomputed daily recommendations served by API.

---

## Phase 1: Core Implementation (2-5 Days)

### Component Breakdown

#### 1. Data Generation (`generate_data.py`)

**Objective:** Create a realistic supermarket simulation dataset.

**Key Behaviors to Simulate:**

1. **Customer Segments**
   - **Budget-conscious:** High promo affinity, lower basket size, infrequent purchases
   - **Premium:** Low promo affinity, higher basket size, weekly purchases
   - **Family:** Medium basket size, buys staples repeatedly
   - **Horeca (wholesale):** Large basket size, bulk purchases, low promo usage

2. **Temporal Patterns**
   - **Weekly cycles:** Grocery shopping peaks on weekends
   - **Monthly cycles:** Payday effect (end of month spike)
   - **Seasonality:** Holiday spikes (Christmas, Easter, summer BBQ)

3. **Product Preferences**
   - Category affinity varies by segment (families → dairy/bakery, horeca → bulk goods)
   - Brand loyalty simulation (some customers always buy brand X)

4. **Promotional Behavior**
   - Some customers **only** buy on promotion
   - Others are **discount-blind** (buy regardless)
   - Implement offer impression → redemption conversion funnel

**Output Scale (Default):**
- 50,000 customers
- 10,000 products (across 20 categories)
- 200 active offers
- 2,000,000 order items (6 months of history)
- 500,000 impressions
- 25,000 redemptions (5% conversion rate)

**Implementation Notes:**
```python
# Pseudocode structure
def generate_customers(n=50000):
    # Assign segments with realistic distribution
    # budget: 40%, premium: 20%, family: 30%, horeca: 10%
    pass

def generate_orders(customers, products, days=180):
    # For each customer, sample purchase frequency from segment distribution
    # Add weekly/monthly cycles using sine waves + noise
    # Apply seasonal multipliers
    pass

def generate_impressions_and_redemptions(orders, offers):
    # For each customer, show 5-10 offers per week
    # P(redemption | impression) depends on:
    #   - Discount depth
    #   - Category affinity
    #   - Customer promo sensitivity
    #   - Recency of last purchase in category
    pass
```

---

#### 2. Feature Engineering (`features.py`)

**Objective:** Transform raw tables into ML-ready features.

**Feature Categories:**

##### A. Customer Features (`customer_features` table)

| Feature | Description | SQL/Logic |
|---------|-------------|-----------|
| `recency_days` | Days since last order | `SELECT MAX(DATEDIFF(current_date, order_timestamp))` |
| `frequency` | Orders in last 90 days | `SELECT COUNT(*) FROM orders WHERE ...` |
| `monetary` | Total spend in last 90 days | `SELECT SUM(total_amount) FROM orders WHERE ...` |
| `promo_affinity` | % of items bought on discount | `SUM(is_promo) / COUNT(*)` from order_items |
| `avg_basket_size` | Average items per order | `AVG(num_items)` |
| `category_entropy` | Diversity of purchased categories | Shannon entropy over category distribution |
| `top_3_categories` | Most-purchased categories (comma-separated) | `SELECT category, COUNT(*) ... GROUP BY ... LIMIT 3` |

##### B. Offer Features (`offer_features` table)

| Feature | Description | SQL/Logic |
|---------|-------------|-----------|
| `discount_depth` | Normalized discount % | `discount_value / base_price` (if percentage) |
| `margin_impact` | How much margin is sacrificed | `base_price * margin * discount_depth` |
| `days_until_expiry` | Urgency signal | `DATEDIFF(end_date, current_date)` |
| `historical_redemption_rate` | Past performance of this offer | `redemptions / impressions` (if offer reused) |
| `category` | From linked product | JOIN with products table |
| `brand` | From linked product | JOIN with products table |

##### C. Customer × Offer Interaction Features (`interaction_features` table)

| Feature | Description | SQL/Logic |
|---------|-------------|-----------|
| `bought_product_before` | Binary flag | Check if customer_id + product_id in order_items |
| `days_since_last_purchase_in_category` | Category recency | Last order with this category |
| `category_affinity_score` | How much customer likes this category | `COUNT(orders with category) / COUNT(all orders)` |
| `discount_depth_vs_usual` | Is discount deeper than customer's avg? | `offer_discount_depth - customer_avg_discount` |
| `price_sensitivity_match` | Does customer segment match offer depth? | Budget customers → prefer deep discounts |

**Implementation:**
```python
# Save features to separate tables for clarity
def build_customer_features(conn, reference_date):
    query = """
    CREATE TABLE customer_features AS
    SELECT 
        customer_id,
        JULIANDAY(?) - MAX(JULIANDAY(order_timestamp)) AS recency_days,
        COUNT(*) AS frequency,
        SUM(total_amount) AS monetary,
        ...
    FROM orders
    WHERE order_timestamp <= ?
    GROUP BY customer_id
    """
    conn.execute(query, (reference_date, reference_date))

# Similar for offer_features, interaction_features
```

---

#### 3. Candidate Generation (`candidates.py`)

**Objective:** Retrieve ~200 eligible offers per customer (first stage of two-stage recommender).

**Why Candidate Generation?**
- **Scalability:** Can't score 10,000 offers × 50,000 customers = 500M pairs daily
- **Business rules:** Many offers aren't eligible (store scope, segment restrictions, expired)
- **Efficiency:** Heuristics are fast and explainable

**Candidate Retrieval Logic:**

```python
def generate_candidates(customer_id, max_candidates=200):
    candidates = []
    
    # Step 1: Filter by eligibility
    eligible_offers = get_active_offers()  # Check start_date <= today <= end_date
    eligible_offers = filter_by_store_scope(customer_id)
    eligible_offers = filter_by_segment_scope(customer_id)
    
    # Step 2: Heuristic retrieval (multiple strategies, union results)
    
    # Strategy A: Category affinity
    top_categories = get_customer_top_categories(customer_id, n=3)
    candidates += get_offers_in_categories(top_categories, limit=80)
    
    # Strategy B: Popular in segment
    segment = get_customer_segment(customer_id)
    candidates += get_popular_offers_in_segment(segment, limit=60)
    
    # Strategy C: Previously purchased products
    past_products = get_customer_purchased_products(customer_id, days=90)
    candidates += get_offers_for_products(past_products, limit=40)
    
    # Strategy D: High-margin offers (business priority)
    candidates += get_high_margin_offers(limit=20)
    
    # Deduplicate and cap at max_candidates
    return list(set(candidates))[:max_candidates]
```

**Output:** `candidate_pool(customer_id, offer_id, strategy)` table for transparency.

---

#### 4. Ranker Training (`train_ranker.py`)

**Objective:** Learn to predict `P(redemption | customer, offer, context)`.

**Training Data Construction:**

```python
def build_training_set(conn):
    """
    Positive examples: (customer_id, offer_id, 1) where redemption occurred within 7 days
    Negative examples: (customer_id, offer_id, 0) where impression shown but no redemption
    
    Sampling strategy:
    - All positives (rare class)
    - Random sample of negatives (common class) to balance 1:4 ratio
    """
    query = """
    SELECT 
        i.customer_id,
        i.offer_id,
        CASE WHEN r.redemption_id IS NOT NULL THEN 1 ELSE 0 END AS label,
        cf.*,  -- Customer features
        of.*,  -- Offer features
        ixf.*  -- Interaction features
    FROM impressions i
    LEFT JOIN redemptions r 
        ON i.customer_id = r.customer_id 
        AND i.offer_id = r.offer_id
        AND r.redeemed_timestamp BETWEEN i.shown_timestamp AND DATE(i.shown_timestamp, '+7 days')
    JOIN customer_features cf ON i.customer_id = cf.customer_id
    JOIN offer_features of ON i.offer_id = of.offer_id
    JOIN interaction_features ixf ON i.customer_id = ixf.customer_id AND i.offer_id = ixf.offer_id
    """
    return pd.read_sql(query, conn)
```

**Model Choice (Phase 1):**

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier

# Option A: Logistic Regression (interpretable, fast)
model = LogisticRegression(max_iter=500, class_weight='balanced')

# Option B: LightGBM (better accuracy, still explainable)
model = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1
)

# Train
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2)
model.fit(X_train, y_train)

# Save
joblib.dump(model, 'models/ranker_v1.pkl')
```

**Why Start with LR/GBDT?**
- Interpretable (feature importance, coefficients)
- Fast to train (<1 minute on demo dataset)
- Strong baseline (hard to beat without massive data)
- Interview-friendly (easier to explain than neural nets)

---

#### 5. Ranker Scoring (`score_ranker.py`)

**Objective:** Apply trained model to today's candidate pool.

```python
def score_candidates(model, run_date):
    candidates = get_todays_candidates(run_date)  # From candidate_pool table
    
    # Load features for (customer, offer) pairs
    features = []
    for cust_id, offer_id in candidates:
        features.append(get_features(cust_id, offer_id))
    
    X = pd.DataFrame(features)
    
    # Predict probability of redemption
    scores = model.predict_proba(X)[:, 1]  # P(redemption)
    
    # Sort and take top-N per customer
    results = []
    for cust_id in candidates['customer_id'].unique():
        cust_candidates = candidates[candidates['customer_id'] == cust_id]
        cust_scores = scores[cust_candidates.index]
        
        # Sort descending, take top 10
        top_indices = np.argsort(cust_scores)[::-1][:10]
        
        for rank, idx in enumerate(top_indices, start=1):
            results.append({
                'run_date': run_date,
                'customer_id': cust_id,
                'offer_id': cust_candidates.iloc[idx]['offer_id'],
                'score': cust_scores[idx],
                'rank': rank
            })
    
    # Write to recommendations table
    df = pd.DataFrame(results)
    df.to_sql('recommendations', conn, if_exists='append', index=False)
```

---

#### 6. Daily Pipeline (`daily_run.py`)

**Objective:** Single-command orchestration of entire pipeline.

```python
#!/usr/bin/env python3
"""
Daily batch pipeline for Metro offer recommendations.

Usage:
    python src/daily_run.py --date 2026-02-11
"""

import argparse
from datetime import datetime
import logging

from db import get_connection
from features import build_customer_features, build_offer_features, build_interaction_features
from candidates import generate_candidate_pool
from train_ranker import train_ranker
from score_ranker import score_candidates
from drift import check_drift
from evaluate import compute_offline_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_pipeline(run_date: str):
    conn = get_connection()
    
    logger.info(f"Starting daily run for {run_date}")
    
    # Step 1: Refresh features
    logger.info("Building features...")
    build_customer_features(conn, run_date)
    build_offer_features(conn, run_date)
    build_interaction_features(conn, run_date)
    
    # Step 2: Train model (weekly schedule)
    if should_retrain(run_date):
        logger.info("Retraining ranker...")
        model = train_ranker(conn)
    else:
        logger.info("Loading existing model...")
        model = load_model('models/ranker_v1.pkl')
    
    # Step 3: Generate candidates
    logger.info("Generating candidate pool...")
    generate_candidate_pool(conn, run_date)
    
    # Step 4: Score and rank
    logger.info("Scoring candidates...")
    score_candidates(model, run_date, conn)
    
    # Step 5: Drift detection
    logger.info("Checking for drift...")
    drift_alerts = check_drift(conn, run_date)
    if drift_alerts:
        logger.warning(f"Drift detected: {drift_alerts}")
    
    # Step 6: Offline evaluation (if ground truth available)
    logger.info("Computing offline metrics...")
    metrics = compute_offline_metrics(conn, run_date)
    logger.info(f"Metrics: {metrics}")
    
    logger.info("Daily run completed successfully")
    conn.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', required=True, help='Run date (YYYY-MM-DD)')
    args = parser.parse_args()
    
    run_pipeline(args.date)
```

---

#### 7. API Service (`api.py`)

**Objective:** Serve precomputed recommendations via REST API.

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List
from datetime import date
import sqlite3

app = FastAPI(
    title="Metro Offers Recommender API",
    description="Serve personalized offer recommendations",
    version="1.0.0"
)

# Pydantic models for type safety
class OfferRecommendation(BaseModel):
    offer_id: int
    product_id: int
    product_name: str
    discount_type: str
    discount_value: float
    score: float = Field(..., description="Model's predicted redemption probability")
    rank: int = Field(..., ge=1, le=10)
    expiry_date: date

class RecommendationResponse(BaseModel):
    customer_id: int
    run_date: date
    recommendations: List[OfferRecommendation]

def get_db():
    conn = sqlite3.connect('data/metro.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    customer_id: int = Query(..., description="Customer ID"),
    run_date: str = Query(None, description="Date for recommendations (default: today)")
):
    """
    Get top-N personalized offers for a customer.
    
    Returns precomputed recommendations from the most recent daily run.
    """
    if run_date is None:
        run_date = date.today().isoformat()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch recommendations with offer details
    query = """
    SELECT 
        r.offer_id,
        r.score,
        r.rank,
        o.product_id,
        p.name AS product_name,
        o.discount_type,
        o.discount_value,
        o.end_date AS expiry_date
    FROM recommendations r
    JOIN offers o ON r.offer_id = o.offer_id
    JOIN products p ON o.product_id = p.product_id
    WHERE r.customer_id = ?
      AND r.run_date = ?
    ORDER BY r.rank ASC
    """
    
    cursor.execute(query, (customer_id, run_date))
    rows = cursor.fetchall()
    
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No recommendations found for customer {customer_id} on {run_date}"
        )
    
    recommendations = [
        OfferRecommendation(
            offer_id=row['offer_id'],
            product_id=row['product_id'],
            product_name=row['product_name'],
            discount_type=row['discount_type'],
            discount_value=row['discount_value'],
            score=row['score'],
            rank=row['rank'],
            expiry_date=row['expiry_date']
        )
        for row in rows
    ]
    
    conn.close()
    
    return RecommendationResponse(
        customer_id=customer_id,
        run_date=run_date,
        recommendations=recommendations
    )

@app.get("/recommendations/batch")
def get_batch_recommendations(customer_ids: List[int] = Query(...)):
    """Get recommendations for multiple customers (for batch processing)."""
    # Implementation similar to single endpoint
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**API Usage Examples:**

```bash
# Start server
python src/api.py

# Get recommendations for customer
curl "http://localhost:8000/recommendations?customer_id=12345"

# Response:
{
  "customer_id": 12345,
  "run_date": "2026-02-11",
  "recommendations": [
    {
      "offer_id": 456,
      "product_id": 789,
      "product_name": "Organic Milk 1L",
      "discount_type": "percentage",
      "discount_value": 20.0,
      "score": 0.78,
      "rank": 1,
      "expiry_date": "2026-02-18"
    },
    ...
  ]
}
```

---

#### 8. Offline Evaluation (`evaluate.py`)

**Objective:** Measure recommendation quality against historical ground truth.

**Metrics:**

| Metric | Description | Formula |
|--------|-------------|---------|
| **NDCG@10** | Normalized Discounted Cumulative Gain | Standard ranking quality metric |
| **Redemption Rate@N** | % of users who redeemed ≥1 offer in top-N | `users_with_redemption / total_users` |
| **MRR** | Mean Reciprocal Rank | `1 / rank_of_first_redemption` |
| **Precision@N** | Fraction of top-N that were redeemed | `redeemed_in_topN / N` |
| **Recall@N** | Fraction of all redemptions captured in top-N | `redeemed_in_topN / total_redemptions` |

**Business Metrics:**

| Metric | Description | Why It Matters |
|--------|-------------|----------------|
| **Incremental Revenue** | Revenue from redeemed offers vs baseline | Measures true lift, not just correlation |
| **Discount ROI** | Revenue gain / discount cost | Business KPI for promotional efficiency |
| **Margin Impact** | Lost margin from discounts | Prevents over-discounting high-margin items |

**Implementation:**

```python
def compute_offline_metrics(conn, run_date):
    """
    Evaluate recommendations against future redemptions.
    
    Note: In real production, this has a time lag (need to wait for redemptions).
    For demo, we can evaluate against simulated ground truth.
    """
    # Get recommendations
    recs = pd.read_sql(f"""
        SELECT customer_id, offer_id, rank
        FROM recommendations
        WHERE run_date = '{run_date}'
    """, conn)
    
    # Get actual redemptions in next 7 days
    redemptions = pd.read_sql(f"""
        SELECT customer_id, offer_id
        FROM redemptions
        WHERE redeemed_timestamp BETWEEN '{run_date}' AND DATE('{run_date}', '+7 days')
    """, conn)
    
    # Compute NDCG@10
    ndcg = ndcg_score(recs, redemptions, k=10)
    
    # Compute Redemption Rate@10
    users_with_redemption = len(redemptions['customer_id'].unique())
    total_users = len(recs['customer_id'].unique())
    redemption_rate = users_with_redemption / total_users
    
    return {
        'ndcg_at_10': ndcg,
        'redemption_rate_at_10': redemption_rate,
        'precision_at_10': compute_precision(recs, redemptions, k=10),
        'recall_at_10': compute_recall(recs, redemptions, k=10)
    }
```

---

#### 9. Drift Monitoring (`drift.py`)

**Objective:** Detect when feature distributions shift (triggers retraining).

**Method: Population Stability Index (PSI)**

PSI measures how much a feature's distribution has changed between two time periods:

```
PSI = Σ (actual_pct - expected_pct) * ln(actual_pct / expected_pct)
```

**Interpretation:**
- PSI < 0.1: No significant shift
- 0.1 ≤ PSI < 0.25: Moderate shift (investigate)
- PSI ≥ 0.25: Large shift (retrain recommended)

**Implementation:**

```python
def compute_psi(baseline_dist, current_dist, bins=10):
    """
    Compute PSI between two distributions.
    
    Args:
        baseline_dist: Feature values from training period
        current_dist: Feature values from current period
        bins: Number of buckets for discretization
    """
    # Discretize into bins
    baseline_pct, bin_edges = np.histogram(baseline_dist, bins=bins, density=True)
    current_pct, _ = np.histogram(current_dist, bins=bin_edges, density=True)
    
    # Avoid log(0) by adding small epsilon
    epsilon = 0.0001
    baseline_pct = baseline_pct + epsilon
    current_pct = current_pct + epsilon
    
    # Normalize to sum to 1
    baseline_pct /= baseline_pct.sum()
    current_pct /= current_pct.sum()
    
    # Compute PSI
    psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    
    return psi

def check_drift(conn, run_date, threshold=0.25):
    """
    Check drift on key features.
    """
    alerts = []
    
    # Define features to monitor
    features_to_monitor = [
        'recency_days',
        'frequency',
        'monetary',
        'promo_affinity',
        'avg_basket_size',
        'discount_depth'
    ]
    
    # Load baseline (training period)
    baseline_date = '2026-01-01'  # Example
    baseline = load_features(conn, baseline_date)
    
    # Load current
    current = load_features(conn, run_date)
    
    for feature in features_to_monitor:
        psi = compute_psi(baseline[feature], current[feature])
        
        if psi >= threshold:
            alerts.append({
                'feature': feature,
                'psi': psi,
                'severity': 'high' if psi >= 0.5 else 'medium'
            })
            logging.warning(f"Drift detected on {feature}: PSI={psi:.3f}")
    
    return alerts
```

**Alerting Logic:**

```python
if alerts:
    # Log to monitoring system
    for alert in alerts:
        log_drift_alert(alert)
    
    # Trigger retraining if multiple features drifting
    if len(alerts) >= 3:
        trigger_retraining()
```

---

## Phase 2: Modernization & Research Track

### Overview

Phase 2 is **not a full rewrite** — it's a set of **research spikes** and **optional modules** that demonstrate awareness of modern deep learning techniques while staying practical.

**Timeline:** 1-2 weeks after Phase 1 completion  
**Objective:** Show upgrade path to state-of-the-art methods

---

### 2.1 Upgrade Candidate Generation with Embeddings

**Current (Phase 1):** Heuristic retrieval (category affinity, popularity)

**Upgrade (Phase 2):** Embedding-based retrieval using ANN (Approximate Nearest Neighbors)

**Approach:**

1. **Learn Item Embeddings** from co-occurrence in baskets
   ```python
   # Use Word2Vec-style approach on "basket sequences"
   from gensim.models import Word2Vec
   
   # Treat each basket as a "sentence" of products
   baskets = [
       ['product_1', 'product_5', 'product_12'],
       ['product_2', 'product_5', 'product_8'],
       ...
   ]
   
   model = Word2Vec(baskets, vector_size=64, window=5, min_count=5)
   model.save('embeddings/product2vec.model')
   ```

2. **Build ANN Index** for fast retrieval
   ```python
   import faiss
   
   # Extract embeddings
   embeddings = [model.wv[f'product_{i}'] for i in range(num_products)]
   
   # Build FAISS index
   index = faiss.IndexFlatIP(64)  # Inner product (cosine similarity)
   index.add(np.array(embeddings))
   
   faiss.write_index(index, 'embeddings/product_index.faiss')
   ```

3. **Retrieve Similar Products/Offers**
   ```python
   def get_embedding_candidates(customer_id, k=100):
       # Get customer's purchase history
       purchased_products = get_customer_products(customer_id)
       
       # Get embeddings for purchased products
       query_embeddings = [model.wv[p] for p in purchased_products]
       
       # Average embeddings (simple approach)
       customer_embedding = np.mean(query_embeddings, axis=0)
       
       # Search for similar products
       D, I = index.search(customer_embedding.reshape(1, -1), k)
       
       # Map products to active offers
       similar_products = [product_ids[i] for i in I[0]]
       return get_offers_for_products(similar_products)
   ```

**Expected Improvement:** 5-15% lift in NDCG@10 (varies by dataset)

**References:**
- Barkan & Koenigstein (2016) - "Item2Vec: Neural Item Embedding for Collaborative Filtering"
- Covington et al. (2016) - "Deep Neural Networks for YouTube Recommendations" (retrieval stage)

---

### 2.2 Upgrade Ranker: Wide & Deep Pattern

**Current (Phase 1):** Logistic Regression or LightGBM

**Upgrade (Phase 2):** Hybrid "Wide & Deep" model

**Architecture:**

```
                 Input Features
                       |
         +-------------+-------------+
         |                           |
    Wide Path                    Deep Path
    (Linear)                  (MLP Embeddings)
         |                           |
    [Sparse features]         [Dense features]
    [Linear combinations]     [Embedding layers]
         |                           |
         |                    [Hidden layers]
         |                           |
         +-------------+-------------+
                       |
                  Concatenate
                       |
                 Output Layer
                (P(redemption))
```

**Implementation (PyTorch):**

```python
import torch
import torch.nn as nn

class WideAndDeep(nn.Module):
    def __init__(self, num_wide_features, num_deep_features, embedding_dims):
        super().__init__()
        
        # Wide path (memorization)
        self.wide = nn.Linear(num_wide_features, 1)
        
        # Deep path (generalization)
        self.embeddings = nn.ModuleDict({
            'category': nn.Embedding(num_categories, embedding_dims['category']),
            'brand': nn.Embedding(num_brands, embedding_dims['brand']),
            'segment': nn.Embedding(num_segments, embedding_dims['segment'])
        })
        
        deep_input_size = sum(embedding_dims.values()) + num_deep_features
        self.deep = nn.Sequential(
            nn.Linear(deep_input_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)
        )
    
    def forward(self, wide_features, deep_features, categorical_features):
        # Wide path
        wide_out = self.wide(wide_features)
        
        # Deep path
        embedded = [self.embeddings[k](categorical_features[k]) 
                    for k in self.embeddings.keys()]
        deep_input = torch.cat(embedded + [deep_features], dim=1)
        deep_out = self.deep(deep_input)
        
        # Combine
        logits = wide_out + deep_out
        return torch.sigmoid(logits)
```

**Training Script:**

```python
def train_wide_and_deep(train_loader, val_loader, epochs=10):
    model = WideAndDeep(...)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCELoss()
    
    for epoch in range(epochs):
        model.train()
        for batch in train_loader:
            wide, deep, cat, labels = batch
            
            optimizer.zero_grad()
            preds = model(wide, deep, cat)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()
        
        # Validation
        val_metrics = evaluate(model, val_loader)
        print(f"Epoch {epoch}: Val AUC = {val_metrics['auc']:.3f}")
    
    return model
```

**When to Use Wide & Deep:**
- You have **both** sparse categorical features (category, brand) AND dense numerical features (RFM, discount depth)
- Dataset is large enough (>500K examples)
- You want to capture **both memorization** (cross-feature patterns) and **generalization** (embeddings)

**References:**
- Cheng et al. (2016) - ["Wide & Deep Learning for Recommender Systems"](https://arxiv.org/abs/1606.07792)
- Naumov et al. (2019) - ["Deep Learning Recommendation Model (DLRM)"](https://arxiv.org/abs/1906.00091)

---

### 2.3 Sequential Recommendation (Research Track)

**Motivation:** Supermarkets have **temporal patterns** (weekly grocery cycles, seasonal purchases).

**Sequential Models to Explore:**

| Model | Key Idea | Paper |
|-------|----------|-------|
| **SASRec** | Self-attention over purchase sequences | Kang & McAuley (2018) |
| **BERT4Rec** | Bidirectional masked language model for sequences | Sun et al. (2019) |
| **GRU4Rec** | RNN-based session recommendations | Hidasi et al. (2016) |

**Implementation Shortcut: Use RecBole**

[RecBole](https://recbole.io/) is a unified framework with 73+ recommender algorithms.

```bash
pip install recbole
```

**Example: Training SASRec**

```python
from recbole.quick_start import run_recbole

# Configure
config_dict = {
    'data_path': 'data/',
    'dataset': 'metro_sequences',
    'epochs': 50,
    'train_batch_size': 2048,
    'eval_batch_size': 4096,
    'metrics': ['NDCG', 'Hit', 'MRR'],
    'topk': [5, 10, 20],
    'valid_metric': 'NDCG@10'
}

# Train
run_recbole(model='SASRec', config_dict=config_dict)
```

**Data Format for RecBole:**

```
user_id:token  item_id:token  timestamp:float
1              product_123    1640995200
1              product_456    1641081600
...
```

**Expected Use Case:**
- Capture **"next-item prediction"** patterns (e.g., customers who buy milk often buy bread next)
- Useful for **replenishment offers** (predict when customer will run out)

**Caution:** Sequential models require more data (>1M interactions) and longer training time.

---

### 2.4 Uplift Modeling (Causal Inference)

**Problem:** Traditional recommender predicts `P(purchase | offer shown)`, but we want `P(purchase | offer shown) - P(purchase | no offer)`.

**Why?** Some customers will buy anyway (don't waste discount on them).

**Approach: Treatment/Control Simulation**

```python
def simulate_uplift_experiment(customers, offers):
    """
    Randomly assign customers to treatment/control.
    """
    treatment = customers.sample(frac=0.5)
    control = customers.drop(treatment.index)
    
    # Treatment: Show recommended offers
    treatment_purchases = simulate_purchases(treatment, offers_shown=True)
    
    # Control: No offers shown
    control_purchases = simulate_purchases(control, offers_shown=False)
    
    # Measure incremental lift
    treatment_rate = treatment_purchases / len(treatment)
    control_rate = control_purchases / len(control)
    
    uplift = treatment_rate - control_rate
    
    print(f"Treatment conversion: {treatment_rate:.2%}")
    print(f"Control conversion: {control_rate:.2%}")
    print(f"Incremental lift: {uplift:.2%}")
```

**Uplift Modeling Techniques:**

1. **Two-Model Approach:** Train separate models for treatment/control
2. **S-Learner:** Single model with treatment indicator as feature
3. **T-Learner:** Two separate models, predict difference
4. **X-Learner:** Meta-learner that combines treatment/control models

**References:**
- Gutierrez & Gérardy (2017) - "Causal Inference and Uplift Modelling: A Review"

**Phase 2 Goal:** Run simulation to measure **incremental revenue** vs. **wasted discounts**.

---

### 2.5 Multi-Armed Bandits (Online Learning)

**Current:** Batch recommendations updated daily

**Upgrade:** Real-time exploration/exploitation (optional for Phase 2, more of a Phase 3 topic)

**Algorithm: Thompson Sampling**

```python
class ThompsonSamplingBandit:
    def __init__(self, num_offers):
        self.successes = np.ones(num_offers)  # Prior
        self.failures = np.ones(num_offers)
    
    def select_offer(self):
        # Sample from Beta distribution for each offer
        sampled_probs = [
            np.random.beta(self.successes[i], self.failures[i])
            for i in range(len(self.successes))
        ]
        
        # Pick offer with highest sampled probability
        return np.argmax(sampled_probs)
    
    def update(self, offer_id, redeemed):
        if redeemed:
            self.successes[offer_id] += 1
        else:
            self.failures[offer_id] += 1
```

**When to Use Bandits:**
- You have **fast feedback loops** (redemptions within hours, not days)
- You want to **explore** new offers while **exploiting** known winners
- Traffic is high enough to learn quickly

**Caution:** Requires infrastructure for real-time feature serving and model updates.

---

## Repository Structure

```
retail-offer-ranking-engine/
│
├── README.md                          # Project overview + quickstart
├── PROJECT_SPECIFICATION.md           # This file
├── requirements.txt                   # Python dependencies
├── .gitignore
│
├── data/                              # SQLite database + schemas
│   ├── schema.sql                     # Table definitions
│   ├── metro.db                       # SQLite database (generated)
│   └── fixtures/                      # Test data samples
│       └── sample_customers.csv
│
├── src/                               # Source code
│   ├── __init__.py
│   ├── config.py                      # Configuration (paths, hyperparameters)
│   ├── db.py                          # Database connection utilities
│   │
│   ├── generate_data.py               # Synthetic data generator
│   ├── features.py                    # Feature engineering
│   ├── candidates.py                  # Candidate generation logic
│   ├── train_ranker.py                # Model training
│   ├── score_ranker.py                # Scoring/inference
│   ├── daily_run.py                   # Orchestration script
│   ├── evaluate.py                    # Offline evaluation
│   ├── drift.py                       # Drift monitoring
│   │
│   ├── api.py                         # FastAPI service
│   │
│   └── phase2/                        # Phase 2 upgrades (optional)
│       ├── embeddings.py              # Product2Vec, FAISS index
│       ├── wide_and_deep.py           # Neural ranker
│       └── sequential.py              # SASRec/BERT4Rec experiments
│
├── models/                            # Saved model artifacts
│   ├── ranker_v1.pkl
│   ├── product2vec.model
│   └── embeddings/
│       └── product_index.faiss
│
├── notebooks/                         # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_model_comparison.ipynb
│   └── 04_phase2_experiments.ipynb
│
├── tests/                             # Unit tests
│   ├── test_features.py
│   ├── test_candidates.py
│   └── test_api.py
│
└── docs/                              # Documentation
    ├── ARCHITECTURE.md                # System design deep-dive
    ├── DATA_MODEL.md                  # Schema documentation
    ├── API_REFERENCE.md               # FastAPI endpoints
    └── INTERVIEW_PREP.md              # Technical interview Q&A
```

---

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone https://github.com/LaoWater/retail-offer-ranking-engine.git
cd retail-offer-ranking-engine

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database schema
sqlite3 data/metro.db < data/schema.sql

# Generate synthetic data
python src/generate_data.py --customers 50000 --products 10000 --offers 200

# Verify
sqlite3 data/metro.db "SELECT COUNT(*) FROM customers;"
```

### Daily Development Loop

```bash
# Run full pipeline
python src/daily_run.py --date 2026-02-11

# Start API server (in separate terminal)
python src/api.py

# Test API
curl "http://localhost:8000/recommendations?customer_id=12345"

# Run tests
pytest tests/
```

### Phase 2 Experiments

```bash
# Train embedding model
python src/phase2/embeddings.py --output models/product2vec.model

# Train Wide & Deep ranker
python src/phase2/wide_and_deep.py --epochs 20 --batch-size 2048

# Compare models
python notebooks/03_model_comparison.ipynb
```

---

## Team Roles & Task Breakdown

### Option A: Solo Developer (You)

**Week 1 (Phase 1):**
- Day 1-2: Data generation + schema setup
- Day 3: Feature engineering
- Day 4: Candidate generation + ranker training
- Day 5: API + evaluation + drift monitoring

**Week 2 (Phase 2):**
- Day 1-2: Embedding-based retrieval
- Day 3-4: Wide & Deep ranker experiments
- Day 5: Documentation + demo prep

### Option B: Team of 4

| Role | Primary Responsibilities | Deliverables |
|------|--------------------------|--------------|
| **Data/ML Engineer A** | Data generation, schema, feature engineering | `generate_data.py`, `features.py`, `schema.sql` |
| **ML Engineer B** | Model training, evaluation, experiments | `train_ranker.py`, `evaluate.py`, Phase 2 models |
| **Backend Engineer** | API service, database utilities, monitoring | `api.py`, `db.py`, `drift.py` |
| **Platform Engineer** | Orchestration, testing, docs, CI/CD | `daily_run.py`, tests/, README.md |

**Collaboration Points:**
- **Day 2:** Data schema review (all team)
- **Day 3:** Feature contract definition (Engineers A + B)
- **Day 4:** API contract definition (Engineers B + Backend)
- **Day 5:** Integration testing (all team)

---

## Demo Day Script

### Scenario: 15-Minute Live Demo

**Objective:** Show end-to-end pipeline + explain design choices.

#### Part 1: Setup (2 minutes)

```bash
# Show clean slate
rm data/metro.db

# Generate data with narration
python src/generate_data.py --customers 10000 --days 90
# "We're simulating 10K customers with 3 months of purchase history..."
```

#### Part 2: Pipeline Execution (3 minutes)

```bash
# Run daily pipeline
python src/daily_run.py --date 2026-02-11

# Show logs:
# [INFO] Building features...
# [INFO] Retraining ranker...
# [INFO] Generating candidate pool...
# [INFO] Scoring candidates...
# [INFO] Drift check: PSI = 0.08 (OK)
```

**Talking Points:**
- "Two-stage architecture: retrieve 200 candidates, rank with supervised model"
- "Candidate generation uses category affinity + segment rules"
- "Ranker is Logistic Regression for interpretability"

#### Part 3: API Demo (3 minutes)

```bash
# Start server (background)
python src/api.py &

# Query recommendations
curl "http://localhost:8000/recommendations?customer_id=5678" | jq

# Response walkthrough:
# - Top 10 offers ranked by predicted redemption probability
# - Mix of categories (dairy, produce, bakery)
# - Discount depths range from 10-30%
```

**Talking Points:**
- "Precomputed batch recommendations served via FastAPI"
- "Pydantic models ensure type safety"
- "Real production would add authentication, rate limiting"

#### Part 4: Evaluation Metrics (2 minutes)

```bash
# Show offline metrics
python src/evaluate.py --date 2026-02-11

# Output:
# NDCG@10: 0.42
# Redemption Rate@10: 8.3%
# Precision@10: 12.5%
```

**Talking Points:**
- "NDCG@10 measures ranking quality"
- "Redemption Rate@10 is business KPI"
- "Baseline (random) would be ~2% redemption rate"

#### Part 5: Drift Scenario (3 minutes)

```bash
# Modify customer behavior (simulate Black Friday)
python src/generate_data.py --scenario black-friday --append

# Rerun pipeline
python src/daily_run.py --date 2026-02-12

# Show drift alert:
# [WARNING] Drift detected on promo_affinity: PSI=0.32
# [WARNING] Drift detected on avg_basket_size: PSI=0.28
# [INFO] Retraining triggered
```

**Talking Points:**
- "PSI monitoring detects distribution shifts"
- "Automatic retraining when multiple features drift"
- "Real production would have more sophisticated thresholds"

#### Part 6: Phase 2 Preview (2 minutes)

**Show notebook or slides:**
- Embedding-based retrieval (product2vec demo)
- Wide & Deep architecture diagram
- Comparison table: LR vs. Wide & Deep (5-10% NDCG improvement)

**Talking Points:**
- "Phase 1 proves the pipeline works"
- "Phase 2 explores modern deep learning upgrades"
- "Realistic approach: start simple, iterate based on data"

---

## Interview Preparation Guide

### Key Questions You Should Be Ready to Answer

#### 1. System Design

**Q: "Walk me through your recommendation system architecture."**

**A:**
> "It's a two-stage recommender:
> 
> **Stage 1 - Candidate Generation:** We retrieve ~200 eligible offers per customer using heuristics like category affinity, segment rules, and purchase history. This is fast and explainable.
> 
> **Stage 2 - Ranking:** We train a supervised model to predict P(redemption | customer, offer) using features like RFM, discount depth, category affinity, and interaction signals. The ranker sorts candidates and returns top-N.
> 
> We run this as a daily batch job, precompute recommendations, and serve them via FastAPI. We monitor drift using PSI and retrain weekly or when drift is detected."

**Follow-up: "Why two stages instead of one?"**

> "Scoring 10K offers × 50K customers = 500M pairs daily is computationally expensive and wasteful. Most offers aren't relevant (wrong store, expired, wrong segment). Candidate generation filters this down 50x using cheap heuristics, then we spend our compute budget on accurate ranking of the shortlist."

---

#### 2. Feature Engineering

**Q: "What features are most predictive of offer redemption?"**

**A:**
> "Top 5 features by importance:
> 1. **Category affinity:** Does customer regularly buy this category?
> 2. **Promo sensitivity:** % of items bought on discount historically
> 3. **Discount depth:** Deeper discounts convert better
> 4. **Recency:** When did customer last purchase in this category?
> 5. **Bought product before:** Binary flag (repeat purchases are safer bets)
> 
> We also include interaction features like 'discount depth vs. customer's usual discounts' to capture personalization."

**Follow-up: "How do you handle new customers with no history?"**

> "Cold start problem. We fall back to:
> 1. Segment-based defaults (premium customers → high-end brands)
> 2. Popular offers in their home store
> 3. Offers for essential categories (milk, bread, eggs)
> 
> Phase 2 could explore content-based filtering using product attributes."

---

#### 3. Model Selection

**Q: "Why did you choose Logistic Regression over deep learning for Phase 1?"**

**A:**
> "Three reasons:
> 1. **Interpretability:** Stakeholders need to understand why we recommended each offer
> 2. **Speed:** Trains in <1 minute on 1M examples, no GPU needed
> 3. **Strong baseline:** LR/GBDT are hard to beat without massive datasets (>10M examples)
> 
> We can always upgrade to Wide & Deep in Phase 2 if we prove the pipeline works and have data to support it."

**Follow-up: "When would you switch to deep learning?"**

> "When:
> 1. Dataset grows to >5M labeled examples
> 2. We add high-cardinality categorical features (product embeddings, user embeddings)
> 3. We see diminishing returns from feature engineering
> 4. We have GPU infrastructure for training
> 
> Deep learning shines when you have sparse categorical features (product IDs, brands) and need to learn representations automatically."

---

#### 4. Evaluation

**Q: "How do you measure if your recommender is good?"**

**A:**
> "Two dimensions:
> 
> **Offline metrics** (historical data):
> - NDCG@10: Measures ranking quality (0.42 in our demo)
> - Redemption Rate@10: Business KPI (8.3% vs. 2% baseline)
> - Precision/Recall@10: Standard ML metrics
> 
> **Business metrics** (A/B test in production):
> - Incremental revenue: Revenue from treatment - control
> - Discount ROI: Revenue gain / discount cost
> - Customer engagement: CTR on offers
> 
> Offline metrics predict online performance but aren't perfect. We need A/B tests for true validation."

**Follow-up: "What if your model has high NDCG but low business impact?"**

> "That's a sign of **dataset bias**. Example:
> - Model learns P(buy | shown offer) 
> - But high P(buy) might just mean customer would buy anyway
> - Solution: Uplift modeling (estimate P(buy | shown) - P(buy | not shown))
> 
> This is why Phase 2 includes causal inference experiments."

---

#### 5. Monitoring & Maintenance

**Q: "How do you know when your model is degrading?"**

**A:**
> "Three monitoring layers:
> 
> **1. Feature drift (PSI):**
> - Track distribution shifts on key features
> - Example: If 'promo_affinity' spikes (Black Friday), retrain
> 
> **2. Prediction drift:**
> - Monitor average predicted scores
> - Alert if mean score drops >10%
> 
> **3. Business KPIs:**
> - Weekly redemption rate tracking
> - Alert if drops below baseline
> 
> We retrain weekly by default, or immediately if drift detected."

**Follow-up: "What causes drift in retail?"**

> "Common sources:
> - **Seasonality:** Christmas shopping patterns differ from summer
> - **Promotions:** Black Friday changes behavior dramatically
> - **Assortment changes:** New products, discontinued items
> - **Economic shifts:** Inflation changes price sensitivity
> 
> This is why we need continuous monitoring + retraining."

---

#### 6. Production Considerations

**Q: "What would you change to deploy this in production?"**

**A:**
> "Phase 1 is a demo with shortcuts. For production:
> 
> **Infrastructure:**
> - Replace SQLite with PostgreSQL + caching layer (Redis)
> - Add job scheduler (Airflow/Prefect) instead of cron
> - Deploy API to Kubernetes with autoscaling
> 
> **ML Platform:**
> - Feature store (Feast/Tecton) for online/offline consistency
> - Model registry (MLflow) for versioning
> - A/B testing framework for safe rollouts
> 
> **Monitoring:**
> - Prometheus + Grafana for metrics
> - PagerDuty for alerts
> - Data quality checks (Great Expectations)
> 
> **Compliance:**
> - GDPR-compliant data handling
> - Explainability layer (SHAP values) for transparency
> - Bias audits (fairness across segments)
> 
> Estimated effort: 2-3 months with a team of 4."

---

#### 7. Phase 2 Deep Dive

**Q: "You mentioned Wide & Deep. How does it differ from your Phase 1 model?"**

**A:**
> "Wide & Deep combines two paths:
> 
> **Wide path (memorization):**
> - Linear model on cross-features
> - Example: 'customer_segment=premium AND category=wine'
> - Learns specific patterns from data
> 
> **Deep path (generalization):**
> - Embeddings for categorical features (product_id, brand)
> - MLP layers to learn interactions
> - Generalizes to unseen combinations
> 
> **Why it's better:**
> - Handles high-cardinality features (10K products → 64-dim embeddings)
> - Captures both specific rules and general patterns
> - Used at Google, Facebook, Alibaba
> 
> **When to use:**
> - Large dataset (>1M examples)
> - Many categorical features
> - Mixed feature types (dense + sparse)
> 
> References: Cheng et al. (2016) 'Wide & Deep Learning for Recommender Systems'."

**Follow-up: "What about sequential models like SASRec?"**

> "SASRec is great for capturing temporal dynamics:
> - Learns from sequence of purchases (milk → bread → eggs)
> - Self-attention mechanism finds patterns
> - Useful for 'next-item prediction'
> 
> **Trade-offs:**
> - Needs more data (>1M sequences)
> - Slower to train (days, not minutes)
> - Less interpretable than LR/GBDT
> 
> For Metro, I'd start with Wide & Deep (proven ROI) before investing in sequential models. Sequential might be Phase 3 if we see clear temporal patterns."

---

### Technical Deep Dives

#### A. Two-Stage Recommender Pattern

**Industry Standard Approach:**

```
┌────────────────────────────────────────────┐
│ Stage 1: Candidate Generation (Retrieval) │
│ - Fast (ms latency)                        │
│ - Recall-focused                           │
│ - Heuristic or embedding-based             │
│ - Reduces 1M items → 100-500 candidates    │
└────────────────────────────────────────────┘
                    ↓
┌────────────────────────────────────────────┐
│ Stage 2: Ranking                           │
│ - Slower (100ms latency)                   │
│ - Precision-focused                        │
│ - Complex model (GBDT, DNN)                │
│ - Sorts 100-500 → Top-N                    │
└────────────────────────────────────────────┘
```

**Real-World Examples:**
- **YouTube:** Retrieval (100 videos) → Ranking (Top 10)
- **Amazon:** Retrieval (500 products) → Ranking (Top 20)
- **Netflix:** Retrieval (200 titles) → Ranking (Personalized homepage)

**Why This Pattern?**
1. **Computational efficiency:** Can't score millions of pairs
2. **Latency requirements:** Retrieval must be fast, ranking can be slower
3. **Model complexity:** Retrieval uses simple signals, ranking uses everything

---

#### B. PSI (Population Stability Index) Math

**Formula:**
```
PSI = Σ (P_actual - P_baseline) × ln(P_actual / P_baseline)
```

Where:
- `P_actual` = Proportion in each bin (current period)
- `P_baseline` = Proportion in each bin (training period)

**Example:**

Feature: `discount_depth` (binned into 5 buckets)

| Bin | Baseline % | Current % | Calculation |
|-----|-----------|-----------|-------------|
| 0-10% | 20% | 18% | (0.18-0.20) × ln(0.18/0.20) = 0.002 |
| 10-20% | 30% | 28% | (0.28-0.30) × ln(0.28/0.30) = 0.001 |
| 20-30% | 25% | 30% | (0.30-0.25) × ln(0.30/0.25) = 0.009 |
| 30-40% | 15% | 18% | (0.18-0.15) × ln(0.18/0.15) = 0.005 |
| 40%+ | 10% | 6% | (0.06-0.10) × ln(0.06/0.10) = 0.020 |

**PSI = 0.002 + 0.001 + 0.009 + 0.005 + 0.020 = 0.037 (No drift)**

**Interpretation:**
- PSI < 0.1: No drift
- 0.1 ≤ PSI < 0.25: Moderate drift (investigate)
- PSI ≥ 0.25: Large drift (retrain)

---

#### C. Candidate Generation Strategies

**Multiple Retrieval Strategies (Union):**

```python
candidates = set()

# Strategy 1: Category affinity (80 candidates)
top_categories = get_top_categories(customer_id)
candidates.update(get_offers_in_categories(top_categories, limit=80))

# Strategy 2: Segment popularity (60 candidates)
segment = get_segment(customer_id)
candidates.update(get_popular_in_segment(segment, limit=60))

# Strategy 3: Repeat purchases (40 candidates)
past_products = get_purchased_products(customer_id)
candidates.update(get_offers_for_products(past_products, limit=40))

# Strategy 4: High-margin offers (20 candidates)
candidates.update(get_high_margin_offers(limit=20))

return list(candidates)[:200]
```

**Why Multiple Strategies?**
- **Diversity:** Avoids filter bubble (all dairy offers)
- **Coverage:** Different customers trigger different strategies
- **Business goals:** Balances relevance + margin optimization

---

## Technical Dependencies

### Core Dependencies (Phase 1)

```txt
# requirements.txt

# Data & ML
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.4.0
joblib==1.3.2

# Database
sqlite3  # Built-in to Python

# API
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3

# Utilities
python-dateutil==2.8.2
tqdm==4.66.1

# Monitoring
scipy==1.12.0  # For PSI calculations

# Development
pytest==7.4.4
pytest-cov==4.1.0
black==24.1.1
flake8==7.0.0
```

### Optional Dependencies (Phase 2)

```txt
# Deep Learning
torch==2.1.2
pytorch-lightning==2.1.3

# Embeddings
gensim==4.3.2
faiss-cpu==1.7.4  # Or faiss-gpu for GPU support

# Sequential Models
recbole==1.2.0

# Experiment Tracking
mlflow==2.9.2
wandb==0.16.2

# Visualization
matplotlib==3.8.2
seaborn==0.13.1
plotly==5.18.0
```

### System Requirements

| Resource | Phase 1 (Minimum) | Phase 2 (Recommended) |
|----------|-------------------|----------------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 5 GB | 20 GB |
| GPU | None | NVIDIA GPU (optional, for Phase 2) |

---

## Success Metrics

### Phase 1 Success Criteria

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Pipeline Completion** | ✅ End-to-end run completes | `python src/daily_run.py` exits successfully |
| **API Response Time** | < 100ms (p95) | Load test with `locust` or `ab` |
| **NDCG@10** | > 0.35 | Offline evaluation against holdout set |
| **Redemption Rate@10** | > 5% | Business metric (vs. 2% random baseline) |
| **Code Coverage** | > 80% | `pytest --cov=src` |
| **Documentation** | Complete | README, API docs, architecture diagrams |

### Phase 2 Success Criteria

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **NDCG@10 Improvement** | +5-10% vs. Phase 1 | A/B test or offline comparison |
| **Wide & Deep Training** | Converges in <20 epochs | Training logs |
| **Embedding Quality** | Clusters semantically similar products | t-SNE visualization |
| **Sequential Model** | Outperforms baseline on next-item prediction | RecBole evaluation |

### Interview Success Criteria

| Criterion | Target | Evidence |
|-----------|--------|----------|
| **System Design Fluency** | Can explain architecture end-to-end in 10 minutes | Mock interview practice |
| **Technical Depth** | Can answer follow-up questions on any component | Technical deep dives above |
| **Business Awareness** | Connects ML choices to business outcomes | "Why this model?", "What's the ROI?" |
| **Production Readiness** | Discusses real-world deployment challenges | Monitoring, A/B testing, compliance |
| **Research Awareness** | Knows modern techniques (embeddings, transformers) | Phase 2 references |

---

## Appendix: Additional Resources

### Key Papers to Reference

1. **Two-Stage Recommenders:**
   - Covington et al. (2016) - "Deep Neural Networks for YouTube Recommendations"

2. **Neural Ranking:**
   - Cheng et al. (2016) - "Wide & Deep Learning for Recommender Systems"
   - Naumov et al. (2019) - "Deep Learning Recommendation Model (DLRM)"

3. **Sequential Recommendations:**
   - Kang & McAuley (2018) - "Self-Attentive Sequential Recommendation" (SASRec)
   - Sun et al. (2019) - "BERT4Rec: Sequential Recommendation with Bidirectional Encoder Representations from Transformer"

4. **Embeddings:**
   - Barkan & Koenigstein (2016) - "Item2Vec: Neural Item Embedding for Collaborative Filtering"

5. **Evaluation:**
   - Rossetti et al. (2016) - "Are We Really Making Progress in Recommender Systems Research?"

6. **Causal Inference:**
   - Gutierrez & Gérardy (2017) - "Causal Inference and Uplift Modelling: A Review"

### Industry Blogs to Read

- **Netflix Tech Blog:** https://netflixtechblog.com/ (Recommender systems series)
- **Uber Engineering:** https://eng.uber.com/ (ML platform, A/B testing)
- **Spotify Engineering:** https://engineering.atspotify.com/ (Music recommendations)
- **Facebook Research:** https://research.facebook.com/publications/ (DLRM paper)

### Tools & Frameworks

- **RecBole:** https://recbole.io/ (Unified recommender framework)
- **FAISS:** https://github.com/facebookresearch/faiss (Similarity search)
- **MLflow:** https://mlflow.org/ (Experiment tracking)
- **Great Expectations:** https://greatexpectations.io/ (Data quality)

---

## Contact & Contribution

**Repository:** https://github.com/LaoWater/retail-offer-ranking-engine.git

**License:** MIT (for educational purposes)

For questions or suggestions, please open an issue on GitHub.

---

**End of Specification Document**

*Last Updated: February 2026*
*Version: 1.0*
