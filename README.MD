# Metro Personalized Offers Recommender

A production-grade personalized offer recommendation system for Metro (supermarket chain), demonstrating modern ML engineering practices through a fully reproducible end-to-end pipeline.

## Architecture

Two-stage recommender: **Candidate Retrieval** (~200 offers/customer via heuristics) → **Supervised Ranking** (LR/LightGBM predicting P(redemption)).

```
Raw Data → Features → Candidates → Ranker → API → Dashboard
     ↑                                  ↓
  50K customers                   Top-10 offers/user
  10K products                    Served via FastAPI
  200 offers                      Visualized in Streamlit
```

## Quickstart

```bash
# 1. Clone and setup
git clone https://github.com/LaoWater/retail-offer-ranking-engine.git
cd retail-offer-ranking-engine
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Generate synthetic data (50K customers, ~2M order items)
python -m src.generate_data

# 3. Run the full pipeline
python -m src.daily_run --date 2026-02-11

# 4. Start the API
uvicorn src.api:app --host 0.0.0.0 --port 8000
# Then: http://localhost:8000/docs

# 5. Launch the dashboard
streamlit run src/dashboard.py

# 6. Run tests
pytest tests/ -v
```

## Pipeline Components

| Component | File | Description |
|-----------|------|-------------|
| Data Generation | `src/generate_data.py` | 50K customers, 10K products, realistic temporal patterns |
| Feature Engineering | `src/features.py` | RFM, promo affinity, category entropy, interaction features |
| Candidate Generation | `src/candidates.py` | 4 strategies: category affinity, segment popularity, repeat purchase, high margin |
| Ranker Training | `src/train_ranker.py` | Logistic Regression + LightGBM, auto-selects best by AUC |
| Ranker Scoring | `src/score_ranker.py` | Score candidates, rank, write top-10 per customer |
| Daily Pipeline | `src/daily_run.py` | Single-command orchestration with structured logging |
| API Service | `src/api.py` | FastAPI with Pydantic models, health check, batch endpoint |
| Evaluation | `src/evaluate.py` | NDCG@10, Precision, Recall, MRR, random baseline comparison |
| Drift Monitoring | `src/drift.py` | PSI-based feature drift detection with alerting |
| Dashboard | `src/dashboard.py` | 6-tab Streamlit showcase with interactive visualizations |

## API Endpoints

```
GET /health                              → DB stats, last run date
GET /recommendations?customer_id=123     → Top-10 personalized offers
GET /recommendations/batch?customer_ids=1,2,3 → Batch recommendations
GET /customers/{id}                      → Customer profile + features
GET /metrics                             → Latest evaluation metrics
```

## Dashboard Tabs

1. **Customer Insights** — Segment distribution, purchase patterns, category heatmap
2. **Offer Analytics** — Redemption rates, discount depth analysis, time series
3. **Model Performance** — AUC comparison, feature importance, PR/ROC curves
4. **Feature Drift** — PSI heatmap, trend lines, alert thresholds
5. **Recommendation Explorer** — Pick a customer, see their offers with scores
6. **Diversity Metrics** — Category coverage, popularity bias, offer distribution

## Tech Stack

- **ML:** scikit-learn, LightGBM
- **Storage:** SQLite
- **API:** FastAPI + Pydantic
- **Dashboard:** Streamlit + Plotly
- **Monitoring:** PSI drift detection (scipy)

## Project Structure

```
src/
  config.py          # Single source of truth for all parameters
  db.py              # SQLite connection utilities
  generate_data.py   # Synthetic data generator
  features.py        # Feature engineering (customer, offer, interaction)
  candidates.py      # Candidate retrieval (4 strategies)
  train_ranker.py    # Model training (LR + LightGBM)
  score_ranker.py    # Candidate scoring and ranking
  daily_run.py       # Pipeline orchestration
  api.py             # FastAPI service
  evaluate.py        # Offline metrics (NDCG, Precision, Recall, MRR)
  drift.py           # PSI drift monitoring
  dashboard.py       # Streamlit dashboard
data/
  schema.sql         # Database schema
  metro.db           # Generated SQLite database
models/
  ranker_latest.pkl  # Saved model artifact
tests/
  test_features.py   # Feature engineering tests
  test_candidates.py # Candidate generation tests
  test_api.py        # API endpoint tests
```
