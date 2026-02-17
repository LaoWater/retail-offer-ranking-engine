# Metro Romania — Personalized Offers Recommender

## What This Project Is

A **production-realistic personalized offer recommendation system** replicating the **Metro Cash & Carry Romania** database, pricing philosophy, and ML recommendation pipeline. Metro has had a legacy recommender in production for 6-7 years — this project reconstructs that system from scratch, then demonstrates a clear improvement path.

**Two-phase approach:**
- **Phase 1 (In Progress):** Replicate Metro Romania's current architecture — batch-first, two-stage recommender with classical ML (LR/LightGBM), full pipeline from synthetic data to served predictions
- **Phase 2 (Planned):** Modernize with deep learning — embeddings-based retrieval, Wide & Deep neural ranker, sequential models, causal inference

---

## Metro Romania — The Real Business Model

### Core Identity

Metro is **NOT a consumer supermarket**. It is a **B2B cash-and-carry wholesaler**. You cannot enter a Metro store without a **Metro Card** tied to a registered business (certificate of incorporation required). This means:

- **100% of transactions are linked to a known customer** — complete purchase history visibility
- **Every customer is a business** — restaurants, hotels, cafes, small shops, caterers
- The catalog is optimized for **professional buyers**, not households

### Customer Segments (Romania-Specific)

Metro Romania's customer base is approximately:

| Segment | Share | Description | Behavior |
|---------|-------|-------------|----------|
| **HoReCa** | ~50% | Hotels, restaurants, cafes, catering, ghost kitchens | High frequency (3-5x/week), large baskets (30-80 items), bulk buying, ultra-fresh focus |
| **Traders** | ~30% | Small shop owners (magazine de cartier), kiosk operators | Buy for resale, margin-sensitive, broad category coverage, medium frequency |
| **SCO** | ~12% | Service companies, offices, institutions, hospitals, schools | Corporate procurement, predictable periodic orders, non-food heavy |
| **Freelancers** | ~8% | Independent professionals (PFA/SRL), small businesses | Smallest baskets, least frequent, mix of food and office supplies |

**Key insight:** ~70% of Metro Romania's floor space and assortment is dedicated to human-consumable/usable goods (food, beverages, cleaning, kitchen supplies). Professional HoReCa equipment and office supplies fill the remaining ~30%.

### The Tiered Pricing Model — "Buy More, Pay Less" (Staffelpreise)

This is Metro's **signature pricing mechanism** — not a promotion, but the **permanent structure on every price tag**:

```
Product: Mozzarella METRO Chef 1kg
┌─────────────────────────────────────┐
│  1 buc    →  24.90 RON/kg           │  ← Tier 1: single unit (base price)
│  6+ buc   →  21.90 RON/kg  (-12%)   │  ← Tier 2: case quantity
│  24+ buc  →  18.90 RON/kg  (-24%)   │  ← Tier 3: bulk/pallet quantity
└─────────────────────────────────────┘
```

**Pricing rules:**
- Every product has 2-3 price tiers with quantity thresholds
- Tier 2 discount: typically 5-15% off base price
- Tier 3 discount: typically 15-35% off base price (max observed ~40%)
- Thresholds vary by product type: units for packaged goods, weight (kg) for fresh products
- Ultra-fresh items (meat, fish, dairy) may have daily-recalculated prices (*Tagespreis*)
- The **best available price** always occupies the same visual position on every price tag

### Product Categories (Romania Assortment)

Metro Romania carries ~8,000-12,000 SKUs. Categories weighted toward the Romanian market:

**Food & Beverage (~70% of assortment):**

| Category | Weight | Subcategories | Notes |
|----------|--------|---------------|-------|
| **Meat & Poultry** | 10% | beef, pork, chicken, lamb, sausages, mici (Romanian) | Butchery counter with custom cuts for HoReCa |
| **Dairy & Eggs** | 9% | milk, cheese (telemea, cascaval, branza), yogurt, butter, cream, eggs | Large blocks for HoReCa (15kg gouda, 5kg telemea) |
| **Fruits & Vegetables** | 9% | seasonal produce, herbs, salads, potatoes, onions, root vegetables | Local sourcing emphasis |
| **Beverages (Non-Alcoholic)** | 7% | water, juice, soft drinks, energy drinks, mineral water | Borsec, Dorna, Bucovina prominent |
| **Bakery & Pastry** | 6% | bread, rolls, pastries, covrigi, frozen pre-baked | Both fresh-baked and frozen |
| **Frozen Foods** | 6% | frozen vegetables, prepared meals, ice cream, frozen proteins | Highest own-brand share |
| **Grocery Staples** | 6% | rice, pasta, flour, oil (sunflower prominent), canned goods, sugar | Romanian staples: sunflower oil, polenta/mamaliga flour |
| **Beverages (Alcoholic)** | 5% | beer (Ursus, Timisoreana), wine (Romanian varieties), spirits (tuica, palinca) | Strong local brands |
| **Seafood** | 4% | fish (crap, pastrav), shrimp, salmon, preserved fish | Seasonal spikes (Christmas carp) |
| **Confectionery & Snacks** | 4% | chocolate, candy, chips, crackers, nuts, biscuits | Romanian brands: ROM, Joe, Heidi |
| **Condiments & Spices** | 3% | ketchup, mustard, mayo, sauces, spices, bors (fermented wheat bran) | Bors is uniquely Romanian |
| **Deli & Charcuterie** | 3% | ham, salami (Sibiu salami), slanina, olives, pickles (murături) | Romanian specialty meats |
| **Coffee & Tea** | 3% | ground, whole bean, pods, instant | Rioba (Metro own brand) |

**Non-Food (~30% of assortment):**

| Category | Weight | Subcategories | Notes |
|----------|--------|---------------|-------|
| **Cleaning & Detergents** | 5% | industrial cleaning, dishwashing, laundry, disinfectants | Essential for HoReCa compliance |
| **Kitchen Utensils & Tableware** | 4% | pots, pans, knives, cutting boards, plates, glasses | METRO Professional brand |
| **HoReCa Equipment** | 4% | commercial ovens, refrigerators, display cases, buffet systems | High-value, low-frequency |
| **Paper & Packaging** | 3% | napkins, takeaway containers, foil, cling wrap, bags | Ghost kitchen demand growing |
| **Personal Care & Hygiene** | 3% | soap, shampoo, dental, skincare, hand sanitizer | Institutional sizes |
| **Household Goods** | 2% | storage, textiles (aprons, table linens), work clothing | Professional-grade |
| **Office Supplies** | 2% | paper, stationery, printer supplies | SCO segment primary buyer |
| **Electronics & Small Appliances** | 2% | small electronics, calculators, POS accessories | Limited assortment |

### Metro's Own Brands

| Brand | Segment | What It Covers |
|-------|---------|----------------|
| **METRO Chef** | Food (premium) | Largest own brand — A-brand quality food for gastronomy |
| **METRO Premium** | Food (high-end) | Distinctive high-end ingredients for culinary experiences |
| **METRO Professional** | Non-food | Kitchen equipment, utensils, appliances, textiles |
| **aro** | Value (food & non-food) | Basic catering needs at best price-performance ratio |
| **Rioba** | Coffee & beverages | Professional coffee and beverage solutions |
| **Horeca Select** | HoReCa food | Professional food service products |
| **Tarrington House** | Household | Home and household products |
| **H-Line** | HoReCa supplies | Hospitality industry disposables and supplies |
| **Sigma** | Office | Office supplies and equipment |

Own-brand target: **>35% of total sales by 2030** (currently growing steadily).

### Offer & Promotion Types

Metro Romania runs a multi-layered promotion system:

| Type | Mechanic | Channel |
|------|----------|---------|
| **Volume discount** (always-on) | Tiered pricing on every product | In-store price tags |
| **Weekly catalog** | Themed flyers (food, non-food, seasonal), 1-2 week validity | Print + digital (metro.ro) |
| **Percentage discount** | X% off on specific products | Catalog, personalized |
| **Monetary discount** | Fixed RON amount off | Catalog, personalized |
| **Gift incentive** | Buy product set X, get Y free | Catalog |
| **Volume bonus** | Buy N, get extra M free | In-store |
| **Personalized offers** | CDP-driven, based on purchase history | Email, SMS, WhatsApp |
| **RFM reactivation** | Triggered when purchase frequency drops | Email, SMS |
| **Birthday campaign** | Personalized birthday discount | Email |
| **Abandoned browse** | Retarget products viewed but not purchased | Email |
| **New customer onboarding** | Welcome sequence with introductory offers | Email |
| **Seasonal campaigns** | Christmas, Easter, BBQ season, back-to-school | Multi-channel |

### Digital Infrastructure (What We're Replicating)

**Metro's actual tech stack:**
- **Recommender:** Go + Kubernetes + Seldon Core for real-time serving
- **ML Training:** Google Cloud Platform + Vertex AI
- **Customer Data Platform:** Adobe CDP + Journey Optimizer
- **Marketing Automation:** Maestra (600M emails + 120M SMS across 21 countries)
- **E-commerce:** Microservices architecture (200+ services), React frontend, Kubernetes
- **Data:** 17M+ customers across 20+ countries, 100% card-linked transactions

**What we replicate (simplified but structurally faithful):**
- SQLite instead of distributed DB (same schema patterns)
- Python ML pipeline instead of Go/Vertex AI (same algorithms)
- FastAPI instead of Seldon Core (same serving pattern)
- Batch pipeline instead of real-time (matches their original architecture)

---

## Architecture

Two-stage recommender pattern (industry standard — YouTube, Amazon, Netflix, Metro):

```
Raw Data (50K customers, 10K products, 200 offers)
    → Feature Engineering (16 features: RFM, promo affinity, category entropy, interaction)
    → Candidate Retrieval (~200 offers/customer via 4 heuristic strategies)
    → Supervised Ranking (LR/LightGBM predicting P(redemption))
    → Top-10 Recommendations per customer
    → FastAPI serving + Interactive dashboard
```

**Monitoring runs in parallel:** PSI-based drift detection + offline evaluation (NDCG@10, Precision, Recall, MRR).

## Tech Stack

- **Language:** Python (100%)
- **ML:** scikit-learn, LightGBM (Phase 1) → PyTorch, gensim, FAISS (Phase 2)
- **Database:** SQLite (WAL mode, foreign keys, indexed)
- **API:** FastAPI + Pydantic
- **Dashboard:** Streamlit + Plotly (may migrate to PyScript or lightweight web app for better UX)
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
  evaluate.py        # Offline metrics: NDCG@10, Precision@10, Recall@10, MRR
  drift.py           # PSI drift monitoring with severity thresholds
  dashboard.py       # Interactive dashboard
data/
  schema.sql         # Core + feature + monitoring tables
  metro.db           # Generated at runtime
models/
  ranker_latest.pkl  # Saved model artifact
tests/
  conftest.py        # Session-scoped test fixtures
  test_features.py   # Feature engineering tests
  test_candidates.py # Candidate generation tests
  test_api.py        # API endpoint tests
```

## Key Design Decisions

1. **config.py is the single source of truth.** All parameters (data sizes, model hyperparameters, thresholds, segment distributions, category definitions, tiered pricing rules) live here. Never hardcode constants elsewhere.

2. **SQLite for reproducibility.** The entire pipeline runs locally in minutes with zero infrastructure. Schema uses foreign keys, WAL mode, and strategic indexes.

3. **Batch-first, not real-time.** Daily pipeline precomputes recommendations. API serves precomputed results. This mirrors Metro's original architecture before their modern migration.

4. **Two-stage pattern.** Candidate retrieval (cheap heuristics, ~200/customer) filters before expensive ranking. Avoids scoring all offers for all customers.

5. **Tiered pricing is structural, not promotional.** The `products` table encodes tier thresholds and tier prices directly — this is not an offer/promotion, it's how every product is priced at Metro.

6. **B2B segments only.** No consumer segments. Every customer is a registered business: HoReCa, Traders, SCO, or Freelancers.

## Running the Pipeline

```bash
# Generate synthetic data
python -m src.generate_data

# Run full daily pipeline (features → model → candidates → scoring → drift → eval)
python -m src.daily_run --date 2026-02-17

# Start API
uvicorn src.api:app --host 0.0.0.0 --port 8000

# Launch dashboard
streamlit run src/dashboard.py

# Run tests
pytest tests/ -v
```

## Phase 1: Replicating Metro Romania's Current System (IN PROGRESS)

Phase 1 replicates what Metro already has — a batch-first recommender with classical ML:

- **Synthetic data generator** modeling Metro Romania's actual business:
  - B2B customer segments (HoReCa 50%, Traders 30%, SCO 12%, Freelancers 8%)
  - Tiered pricing on every product (2-3 tiers with quantity thresholds)
  - Romanian-specific product catalog (mici, telemea, bors, tuica, Sibiu salami)
  - Metro own brands (METRO Chef, METRO Professional, aro, Rioba, Horeca Select)
  - Seasonal patterns (Christmas 2.5x, Easter 1.8x, summer)
  - Weekly cycles reflecting restaurant supply patterns (Monday/Thursday peaks for HoReCa)
- **Feature engineering:** 16 ML features across customer (RFM, promo_affinity, category_entropy), offer (discount_depth, margin_impact, days_until_expiry), and interaction (bought_before, category_affinity_score, price_sensitivity_match)
- **Candidate generation:** 4 strategies — category affinity, segment popularity, repeat purchase, high margin
- **Model training:** LR + LightGBM trained on impression-redemption pairs
- **Scoring & serving:** Top-10 per customer written to DB, served via FastAPI
- **Monitoring:** PSI drift detection
- **Evaluation:** NDCG@10, Precision@10, Recall@10, MRR vs random baseline
- **Dashboard:** Interactive UI where you can simulate any customer, see their recommendations, and switch between Phase 1/Phase 2 algorithms

## Phase 2: Improving Over Metro's System (PLANNED)

Phase 2 is **not a full rewrite** — it's targeted research spikes that demonstrate modern deep learning upgrades:

### 2.1 Embedding-Based Candidate Retrieval
**Replace:** Heuristic retrieval → ANN (Approximate Nearest Neighbors)
- Learn item embeddings via Word2Vec on basket co-occurrence (Product2Vec)
- Build FAISS index for fast similarity search
- Customer embedding = mean of purchased product embeddings
- **Expected lift:** 5-15% NDCG@10 improvement

### 2.2 Wide & Deep Neural Ranker
**Replace:** LR/LightGBM → Hybrid Wide & Deep model (PyTorch)
- Wide path (memorization): Linear on sparse features
- Deep path (generalization): Embedding layers for categorical features → MLP

### 2.3 Sequential Recommendation
**Add:** SASRec / BERT4Rec for temporal modeling of purchase sequences
- Captures weekly grocery cycles, seasonal patterns

### 2.4 Uplift Modeling (Causal Inference)
**Add:** "Would this customer buy without the discount?" — avoid discounting customers who'd buy anyway

### 2.5 Online Learning (Thompson Sampling)
**Add:** Multi-armed bandit for exploration-exploitation in offer optimization

### Phase 2 Success Criteria

| Metric | Target |
|--------|--------|
| NDCG@10 Improvement | +5-10% vs Phase 1 |
| Wide & Deep Training | Converges in <20 epochs |
| Embedding Quality | Clusters semantically similar products |
| Sequential Model | Outperforms baseline on next-item prediction |

## Database Schema

**Core tables:** customers, products, orders, order_items, offers, impressions, redemptions, recommendations
**Feature tables:** customer_features, offer_features, candidate_pool
**Monitoring tables:** drift_log, pipeline_runs

Key schema features:
- `products` table includes tiered pricing columns (tier thresholds + tier prices)
- `customers` table includes business_type and metro_card fields
- `offers` table supports multiple promotion mechanics
- All schema definitions in `data/schema.sql`

## Development Guidelines

- **Always read `config.py` first** when working on any component
- **Use `python -m src.<module>`** to run modules (ensures correct imports)
- **Test with smaller data:** `python -m src.generate_data --customers 1000 --products 500`
- **Idempotent operations:** Pipeline steps clear and rebuild their tables, safe to re-run
- **Seed everything:** `SEED = 42` in config for reproducibility
- **Schema changes** go in `data/schema.sql` — `init_db()` in `db.py` applies them
- **Romania-specific data** should feel authentic — use real brand names, Romanian product names where appropriate, RON currency
