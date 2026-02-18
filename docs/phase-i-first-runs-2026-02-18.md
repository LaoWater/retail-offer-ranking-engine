# Phase I: First Runs (February 18, 2026)
## Journey Notes on a Retail Ranking ML System

This document captures the Phase I journey of a batch recommendation system: how raw retail events are transformed into model features, how ranking models are trained and selected, and how production-style pipeline behavior is interpreted.

---

## 1. System Objective

The system produces daily ranked offers per customer using a two-stage architecture:
1. Candidate generation (retrieve plausible offers)
2. Ranking (score and sort candidates by predicted redemption probability)

The pipeline is batch-first, with precomputed recommendations served downstream.

---

## 2. End-to-End Pipeline Flow

Run command:

```bash
./.venv/bin/python -m src.daily_run --date YYYY-MM-DD
```

Stage sequence:
1. Feature computation
2. Model training/loading
3. Candidate generation
4. Candidate scoring and ranking
5. Drift checks
6. Offline evaluation

Observed runtime profile during first runs:
- Feature and interaction computation dominates wall-clock time.
- Model fitting itself is comparatively fast on the current dataset size.

---

## 3. Data -> Features: The Core Transformation

The ranking model consumes a fixed numeric vector (`FEATURE_COLUMNS`) for each `(customer, offer)` pair. Feature engineering is the bridge from transactional logs to mathematical model input.

### 3.1 Customer features (behavior summary)

Built over a 90-day lookback window from `orders`, `order_items`, and `products`.

Representative features:
- `recency_days`: days since most recent order
- `frequency`: distinct orders in lookback
- `monetary`: total spend
- `promo_affinity`: promo-line share
- `avg_basket_size`, `avg_basket_quantity`
- `tier2_purchase_ratio`, `tier3_purchase_ratio`
- `fresh_category_ratio`
- `business_order_ratio`
- `category_entropy` (Shannon entropy of category mix)

Why it matters:
- Converts irregular purchase histories into stable behavioral signals.
- Adds purchasing-style structure (price-tier usage, promo response, category breadth).

### 3.2 Offer features (commercial profile)

Built from `offers`, `products`, `impressions`, `redemptions`.

Representative features:
- `discount_depth`
- `margin_impact`
- `days_until_expiry`
- `historical_redemption_rate`
- `is_own_brand`

Why it matters:
- Encodes offer mechanics and economics in normalized numeric form.

### 3.3 Interaction features (personalization layer)

Built per `(customer, offer)` pair.

Representative features:
- `bought_product_before`
- `days_since_last_cat_purchase`
- `category_affinity_score`
- `discount_depth_vs_usual`
- `price_sensitivity_match`
- `business_type_match`

Why it matters:
- Captures compatibility between a specific customer and a specific offer.
- This layer is typically where most ranking lift appears.

---

## 4. Labeling Strategy and Training Set Design

Supervision target:
- Positive label (`1`): impression followed by redemption within 7 days
- Negative label (`0`): impression without redemption in that window

Class imbalance handling:
- Negatives are downsampled to a configured ratio relative to positives.

Result:
- A balanced-enough training matrix that preserves ranking signal while reducing majority-class dominance.

---

## 5. Model Stack and Selection

Two models are trained and compared each scheduled retrain:
1. Logistic Regression (linear baseline)
2. LightGBM (gradient-boosted decision trees)

Validation metric:
- ROC AUC

Observed first-run pattern:
- Both models perform strongly.
- LightGBM consistently wins on AUC in tested runs.

### LightGBM in context

LightGBM is a Microsoft gradient-boosting framework that became broadly adopted in the 2016-2018 period for industrial tabular ML.

Why this is a strong fit for this architecture:
- High performance on heterogeneous numeric/tabular features
- Captures nonlinear interactions unavailable to linear models
- Efficient training/inference for batch ranking workloads

This is a custom-trained model on domain data, not a pretrained foundation model.

---

## 6. Interpreting AUC Correctly

Operational interpretation:
- AUC approximates the probability that a random positive receives a higher score than a random negative.

Implication of high AUC:
- Strong global ranking separation.

Important boundaries:
- High AUC does not imply perfect pair-level ordering.
- High AUC does not, by itself, prove top-k business lift.
- Additional metrics are needed for business impact validation (coverage, conversion lift, margin lift, diversity).

---

## 7. Pair-Level Analysis: Why It Matters

Aggregate metrics were complemented with pair-level inspection of real `(customer, offer)` examples.

What pair analysis reveals:
- Which engineered features drove a specific high/low score
- How interaction features can dominate decisions
- Why occasional local misrankings can still coexist with strong global AUC

This analysis is essential for debugging, trust, and stakeholder explainability.

---

## 8. Retraining Cadence and Compute Reality

Retraining policy in this phase:
- Scheduled by weekday rule (e.g., Monday) or missing artifact fallback.

Key runtime insight:
- The expensive component is usually feature pipeline execution (joins, aggregations, interaction assembly).
- Model `fit()` time can remain low when feature dimensionality and sample size are moderate.

This explains why end-to-end model stage duration can be much larger than raw estimator training time.

---

## 9. First-Run Outcome Summary

Phase I first runs established:
1. End-to-end batch orchestration is functional.
2. Feature/model pipeline produces strong ranking quality by AUC.
3. Output volume depends on business preconditions (not only model health), especially active-offer availability.
4. Feature engineering quality and schema discipline are core reliability levers.

---

## 10. Next Engineering Priorities

1. Add explicit run-health counters:
- active offers
- candidate pool size
- recommendations written

2. Expand evaluation beyond AUC:
- precision/recall@k
- expected margin lift@k
- coverage and diversity

3. Harden explainability workflow:
- persist sampled feature contribution diagnostics per run

4. Evolve retraining policy:
- combine schedule with drift/data-change triggers

---

## 11. Repro Commands

```bash
./.venv/bin/python -m src.daily_run --date 2026-02-16
./.venv/bin/python -m src.daily_run --date 2026-02-17
```

```bash
sqlite3 -header -column data/metro.db \
"SELECT run_date, step, status FROM pipeline_runs ORDER BY rowid DESC LIMIT 30;"
```

```bash
sqlite3 -header -column data/metro.db \
"SELECT COUNT(*) AS active_offers FROM offers WHERE DATE(start_date)<=DATE('2026-02-16') AND DATE(end_date)>=DATE('2026-02-16');"
```
