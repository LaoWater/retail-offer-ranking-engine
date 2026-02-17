# Metro Personalized Offers Recommender — CLAUDE.md

## Project Overview

A **production-realistic personalized offer recommendation system** replicating the Metro (European supermarket/wholesale chain) database and ML recommendation pipeline. Metro has had a legacy recommender in production for 6-7 years — this project reconstructs that system from scratch, then demonstrates a clear improvement path.

**Two-phase approach:**
- **Phase 1 (Complete):** Replicate Metro's current architecture — batch-first, two-stage recommender with classical ML (LR/LightGBM), full pipeline from synthetic data to served predictions
- **Phase 2 (In Progress):** Modernize with deep learning — embeddings-based retrieval, Wide & Deep neural ranker, sequential models, causal inference

## Architecture

Two-stage recommender pattern (industry standard — YouTube, Amazon, Netflix):

```
Raw Data (50K customers, 10K products, 200 offers)
    → Feature Engineering (16 features: RFM, promo affinity, category entropy, interaction)
    → Candidate Retrieval (~200 offers/customer via 4 heuristic strategies)
    → Supervised Ranking (LR/LightGBM predicting P(redemption))
    → Top-10 Recommendations per customer
    → FastAPI serving + Streamlit dashboard
```

**Monitoring runs in parallel:** PSI-based drift detection + offline evaluation (NDCG@10, Precision, Recall, MRR).

## Tech Stack

- **Language:** Python (100%)
- **ML:** scikit-learn, LightGBM (Phase 1) → PyTorch, gensim, FAISS (Phase 2)
- **Database:** SQLite (WAL mode, foreign keys, 11 indexes)
- **API:** FastAPI + Pydantic
- **Dashboard:** Streamlit + Plotly
- **Monitoring:** scipy (PSI calculations)
- **Testing:** pytest + pytest-cov

## Project Structure

```
src/
  config.py          # Single source of truth — all params, paths, segments, categories
  db.py              # SQLite connection utilities (WAL mode, 64MB cache)
  generate_data.py   # Synthetic data: 50K customers, 10K products, temporal patterns
  features.py        # Feature engineering: customer (RFM), offer, interaction features
  candidates.py      # Candidate retrieval: 4 strategies (~200/customer)
  train_ranker.py    # Model training: LR + LightGBM, auto-selects best by AUC
  score_ranker.py    # Score candidates, rank, write top-10 per customer
  daily_run.py       # Pipeline orchestration — single command runs everything
  api.py             # FastAPI service with health, recommendations, batch, metrics
  evaluate.py        # Offline metrics: NDCG@10, Precision, Recall, MRR
  drift.py           # PSI drift monitoring with severity thresholds
  dashboard.py       # 6-tab Streamlit dashboard
data/
  schema.sql         # 8 core + 3 feature + 2 monitoring tables
  metro.db           # Generated at runtime
models/
  ranker_latest.pkl  # Saved model artifact
tests/
  conftest.py        # Session-scoped test fixtures (100 customers, 50 products)
  test_features.py   # Feature engineering tests
  test_candidates.py # Candidate generation tests
  test_api.py        # API endpoint tests
```

## Key Design Decisions

1. **config.py is the single source of truth.** All parameters (data sizes, model hyperparameters, thresholds, segment distributions, category definitions) live here. Never hardcode constants elsewhere.

2. **SQLite for reproducibility.** The entire pipeline runs locally in minutes with zero infrastructure. Schema uses foreign keys, WAL mode, and strategic indexes.

3. **Batch-first, not real-time.** Daily pipeline precomputes recommendations. API serves precomputed results. This mirrors Metro's actual architecture.

4. **Two-stage pattern.** Candidate retrieval (cheap heuristics, ~200/customer) filters before expensive ranking. Avoids scoring 10K offers x 50K customers = 500M pairs.

5. **Interpretability first.** Phase 1 uses LR/LightGBM deliberately — explainable to business stakeholders. Deep learning upgrades come in Phase 2.

## Running the Pipeline

```bash
# Generate synthetic data
python -m src.generate_data

# Run full daily pipeline (features → model → candidates → scoring → drift → eval)
python -m src.daily_run --date 2026-02-11

# Start API
uvicorn src.api:app --host 0.0.0.0 --port 8000

# Launch dashboard
streamlit run src/dashboard.py

# Run tests
pytest tests/ -v
```

## Phase 1: Replicating Metro's Current System (COMPLETE)

Phase 1 replicates what Metro already has — a batch-first recommender with classical ML:

- **Synthetic data generator** with realistic patterns: customer segments (Budget 40%, Premium 20%, Family 30%, Horeca 10%), seasonal multipliers (Christmas 2.5x, Easter 1.8x), weekly/monthly cycles, brand loyalty
- **Feature engineering:** 16 ML features across customer (RFM, promo_affinity, category_entropy), offer (discount_depth, margin_impact, days_until_expiry), and interaction (bought_before, category_affinity_score, price_sensitivity_match)
- **Candidate generation:** 4 strategies — category affinity (80), segment popularity (60), repeat purchase (40), high margin (20)
- **Model training:** LR + LightGBM trained on impression-redemption pairs (positives: redemption within 7 days; negatives: downsampled 1:4)
- **Scoring & serving:** Top-10 per customer written to DB, served via FastAPI
- **Monitoring:** PSI drift detection (warn 0.10, alert 0.25, retrain if 3+ features drift)
- **Evaluation:** NDCG@10, Precision@10, Recall@10, MRR vs random baseline
- **Dashboard:** 6-tab Streamlit app (Customer Insights, Offer Analytics, Model Performance, Feature Drift, Recommendation Explorer, Diversity Metrics)

## Phase 2: Improving Over Metro's System (IN PROGRESS)

Phase 2 is **not a full rewrite** — it's targeted research spikes that demonstrate modern deep learning upgrades:

### 2.1 Embedding-Based Candidate Retrieval
**Replace:** Heuristic retrieval → ANN (Approximate Nearest Neighbors)
- Learn item embeddings via Word2Vec on basket co-occurrence (Product2Vec)
- Build FAISS index for fast similarity search
- Customer embedding = mean of purchased product embeddings
- **Expected lift:** 5-15% NDCG@10 improvement
- **Reference:** Barkan & Koenigstein (2016) — Item2Vec

### 2.2 Wide & Deep Neural Ranker
**Replace:** LR/LightGBM → Hybrid Wide & Deep model (PyTorch)
- **Wide path (memorization):** Linear on sparse features (cross-feature patterns)
- **Deep path (generalization):** Embedding layers for categorical features → MLP
- Captures both explicit rules and latent patterns
- **Reference:** Cheng et al. (2016) — Wide & Deep Learning for Recommender Systems

### 2.3 Sequential Recommendation
**Add:** Temporal modeling of purchase sequences
- SASRec (self-attention over purchase history) or BERT4Rec (bidirectional masked LM)
- Captures weekly grocery cycles, seasonal patterns
- **Reference:** Kang & McAuley (2018) — SASRec

### 2.4 Uplift Modeling (Causal Inference)
**Add:** Measure true incremental lift, not just correlation
- "Would this customer buy without the discount?" — avoid discounting customers who'd buy anyway
- Meta-learner approach (T-Learner, X-Learner)
- **Reference:** Gutierrez & Gerardy (2017)

### 2.5 Online Learning (Thompson Sampling)
**Add:** Exploration-exploitation for real-time offer optimization
- Multi-armed bandit treating each offer as an arm
- Beta posterior on redemption probability
- Balance between exploiting known good offers and exploring uncertain ones

### Phase 2 Success Criteria

| Metric | Target |
|--------|--------|
| NDCG@10 Improvement | +5-10% vs Phase 1 |
| Wide & Deep Training | Converges in <20 epochs |
| Embedding Quality | Clusters semantically similar products (t-SNE) |
| Sequential Model | Outperforms baseline on next-item prediction |

## Database Schema (13 tables)

**Core (8):** customers, products, orders, order_items, offers, impressions, redemptions, recommendations
**Feature (3):** customer_features, offer_features, candidate_pool
**Monitoring (2):** drift_log, pipeline_runs

All schema definitions in `data/schema.sql`. Feature tables are rebuilt daily by the pipeline.

## Development Guidelines

- **Always read `config.py` first** when working on any component — it defines all constants, paths, and parameters
- **Use `python -m src.<module>`** to run modules (ensures correct imports)
- **Test with smaller data:** `python -m src.generate_data --customers 1000 --products 500`
- **Idempotent operations:** Pipeline steps clear and rebuild their tables, safe to re-run
- **Seed everything:** `SEED = 42` in config for reproducibility
- **Schema changes** go in `data/schema.sql` — `init_db()` in `db.py` applies them
