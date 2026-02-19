# Metro Romania — Personalized Offers Recommender

A production-realistic personalized offer recommendation system replicating **Metro Cash & Carry Romania's** database, tiered pricing philosophy, and ML recommendation pipeline.

## Running System
I. Start back-end FastAPI: 
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000
II. Start front-end:
npm run dev


## Research Findings — Metro Romania's Real Business

### Metro Is B2B-Only (with Dual-Mode Checkout)
- Cannot enter without a **Metro Card** linked to a registered business (CUI/CIF required)
- **100% of transactions are card-linked** — complete purchase history for every customer
- This is a wholesale cash-and-carry, not a consumer supermarket
- **Dual-mode purchasing:** Card holders choose at checkout — "business" (~87%) or "individual" (~13%, personal/family purchases with household quantities)

### Customer Segments
| Segment | ~Share | Who They Are |
|---------|--------|--------------|
| **HoReCa** | 50% | Restaurants, hotels, cafes, catering, ghost kitchens |
| **Traders** | 30% | Small shop owners (magazine de cartier), kiosk operators |
| **SCO** | 12% | Service companies, offices, institutions |
| **Freelancers** | 8% | PFA/SRL independent professionals |

### Tiered Pricing — "Buy More, Pay Less"
Every product in Metro has 2-3 price tiers. This is **not a promotion** — it's the permanent pricing structure:

```
1 buc    →  24.90 RON/kg          (base price)
6+ buc   →  21.90 RON/kg  (-12%)  (case)
24+ buc  →  18.90 RON/kg  (-24%)  (bulk/pallet)
```
- Tier 2: typically 5-15% off base
- Tier 3: typically 15-35% off (max ~40%)
- Thresholds vary: units for packaged goods, kg for fresh products

### Product Assortment (~90% Food / ~10% Non-Food)
- **Food (flagship: fish/seafood and meat):** Fish/seafood is #1 in Metro's app (sushi restaurants rely on Metro's imports). Meat & poultry has professional butchery. Plus dairy (telemea, cascaval), produce, bakery, beverages, frozen, staples (sunflower oil, mamaliga flour), deli (Sibiu salami, slanina), confectionery, coffee
- **Non-food (~10%, "first line" only):** Cleaning/detergents, kitchen utensils, basic HoReCa equipment, paper/packaging — not deep assortment
- **Own brands:** METRO Chef, METRO Professional, aro, Rioba, Horeca Select, H-Line

### Promotion Types (Layered on Top of Tiered Pricing)
- Weekly catalog offers (percentage/monetary discounts)
- Gift incentives (buy X get Y free)
- Personalized digital offers (CDP-driven via email, SMS, WhatsApp)
- RFM-based reactivation campaigns
- Seasonal campaigns (Christmas, Easter, BBQ season)
- New customer onboarding sequences

### Metro's Real Tech Stack (What We Replicate in Simplified Form)
- **Recommender serving:** Go + Kubernetes + Seldon Core → we use FastAPI
- **ML training:** Google Vertex AI → we use scikit-learn + LightGBM
- **Customer data:** Adobe CDP, 17M+ customers across 20 countries → we use SQLite
- **Marketing:** Maestra automation (600M emails/year) → we simulate impressions/redemptions

---

## Architecture

Two-stage recommender (same pattern as YouTube, Amazon, Netflix, Metro):

```
Synthetic Data (50K customers, 10K products, 200 offers)
    → Feature Engineering (23 features: RFM, tier ratios, promo affinity, interaction signals)
    → Candidate Retrieval (~200 offers/customer via 7 strategies)
    → Supervised Ranking (LR/LightGBM → P(redemption))
    → Top-10 Recommendations per customer
    → API serving + Interactive dashboard
```

## Quickstart

```bash
git clone https://github.com/LaoWater/retail-offer-ranking-engine.git
cd retail-offer-ranking-engine
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m src.generate_data          # Generate synthetic Metro Romania data
python -m src.daily_run --date 2026-02-17  # Run full pipeline
uvicorn src.api:app --port 8000      # Start API (docs at /docs)
streamlit run src/dashboard.py       # Launch dashboard
pytest tests/ -v                     # Run tests
```

## Pipeline Components

| Component | File | What It Does |
|-----------|------|--------------|
| Config | `src/config.py` | Single source of truth — segments, categories, tiered pricing, all parameters |
| Data Generation | `src/generate_data.py` | Synthetic Metro Romania data with realistic B2B patterns |
| Feature Engineering | `src/features.py` | RFM, promo affinity, category entropy, interaction features |
| Candidate Generation | `src/candidates.py` | 7 strategies: category affinity, business type popularity, repeat purchase, high margin, tier upgrade, cross-sell, own brand switch |
| Ranker Training | `src/train_ranker.py` | LR + LightGBM, auto-selects best model by AUC |
| Scoring | `src/score_ranker.py` | Score candidates, rank, write top-10 per customer |
| Pipeline | `src/daily_run.py` | Single-command orchestration |
| API | `src/api.py` | FastAPI with health, recommendations, batch, metrics endpoints |
| Evaluation | `src/evaluate.py` | NDCG@10, Precision, Recall, MRR vs random baseline |
| Drift Monitoring | `src/drift.py` | PSI-based feature drift detection |
| Dashboard | `src/dashboard.py` | Interactive UI — simulate any customer, compare algorithms |

## Two-Phase Roadmap

### Phase 1 — Replicate Metro's Current System (In Progress)
Classical ML pipeline: LR/LightGBM ranker, heuristic candidate retrieval, batch scoring, interpretable features. Faithful to how Metro's legacy recommender works.

### Phase 2 — Modernize with Deep Learning (Planned)
- **Embedding retrieval:** Product2Vec + FAISS replacing heuristic candidates
- **Wide & Deep ranker:** PyTorch neural ranker replacing LightGBM
- **Sequential models:** SASRec/BERT4Rec for temporal purchase patterns
- **Uplift modeling:** Causal inference to avoid unnecessary discounts
- **Online learning:** Thompson Sampling for exploration-exploitation

Target: +5-10% NDCG@10 over Phase 1.

## Key Design Decisions

- **B2B segments only** — HoReCa, Traders, SCO, Freelancers (no consumer segments)
- **Dual-mode checkout** — business (~87%) vs individual (~13%) purchase modes
- **Tiered pricing is structural** — encoded in `products` table, not in offers
- **Food-dominant** — ~90% food (fish/seafood and meat as flagship), ~10% non-food
- **Romania-specific data** — Romanian brands, RON currency, local product names
- **Batch-first** — daily pipeline precomputes recommendations (mirrors Metro's original architecture)
- **SQLite** — zero infrastructure, full pipeline runs locally in minutes
- **config.py** — single source of truth for all parameters

## Tech Stack

Python | scikit-learn | LightGBM | SQLite | FastAPI | Streamlit | Plotly | scipy

## Sources & References

- [Metro AG Strategy (sCore 2030)](https://www.metroag.de/en/about-us/strategy)
- [Metro Price Tag Design (Art. Lebedev Studio)](https://www.artlebedev.com/metro-cc/)
- [Metro Bulk Pricing Explained (MPULSE)](https://www.mpulse.de/en/customer/whats-behind-the-metro-bulk-price)
- [metro.digital Data Science Hub](https://metro.digital/hubs/data-science-hub)
- [Metro E-Commerce Architecture (freiheit.com)](https://freiheit.com/what-we-do/case-studies/case-study-metro/)
- [Metro MarTech Platform (IBM iX)](https://ibmix.de/en/projects/metro-becomes-a-martech-pioneer/)
- [Metro Marketing Automation (Maestra)](https://maestra.io/blog/cases/metro-e-commerce/)
- [Metro Romania Catalogs](https://www.metro.ro/cataloagele-metro)
- [Cheng et al. (2016) — Wide & Deep Learning](https://arxiv.org/abs/1606.07792)
- [Barkan & Koenigstein (2016) — Item2Vec](https://arxiv.org/abs/1603.04259)
- [Kang & McAuley (2018) — SASRec](https://arxiv.org/abs/1808.09781)
