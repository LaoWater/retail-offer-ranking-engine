# Applied ML Reflections V2 — Post-Interview Insights

What Metro actually uses under the hood, and what that means for this project.

---

## 1. Gensim + Skip-Gram — Product Embeddings from Basket Data

Metro uses **gensim's Word2Vec with skip-gram** to learn product embeddings. The key insight: a shopping basket is treated as a "sentence" and each product in it is a "word."

### How It Works

```
Basket 1: [salmon, rice, soy_sauce, wasabi, nori]
Basket 2: [chicken, paprika, sunflower_oil, flour, sour_cream]
Basket 3: [salmon, tuna, shrimp, lemon, dill]
```

Skip-gram trains on (center_product, context_product) pairs within a basket window. Products that consistently co-occur across thousands of baskets end up close in the embedding space — not because someone manually tagged them as related, but because **customers buy them together**.

```python
from gensim.models import Word2Vec

# Each basket is a list of product IDs (the "sentence")
baskets = [
    ["prod_001", "prod_042", "prod_189", "prod_007"],
    ["prod_042", "prod_189", "prod_301", "prod_015"],
    # ... millions of baskets
]

model = Word2Vec(
    sentences=baskets,
    vector_size=128,      # embedding dimensionality
    window=5,             # context window within basket
    sg=1,                 # skip-gram (not CBOW)
    min_count=5,          # ignore products bought fewer than 5 times
    workers=4,
    epochs=10,
)

# Now you can query:
model.wv.most_similar("prod_salmon_fillet")
# → [("prod_tuna_steak", 0.87), ("prod_shrimp_raw", 0.82), ("prod_nori_sheets", 0.79)]
```

### Why Skip-Gram Over CBOW

Skip-gram predicts context from center word. CBOW predicts center from context. For product embeddings:

| Property | CBOW | Skip-Gram |
|----------|------|-----------|
| **Rare products** | Smooths them out (bad — long tail matters) | Gives them distinct embeddings (good) |
| **Training speed** | Faster | Slower |
| **Best for** | Frequent items, general patterns | Full catalog including niche products |

Metro has ~10K SKUs. Many are niche (sushi-grade hamachi, specific Romanian cheeses). Skip-gram preserves these distinctions instead of averaging them away. For a wholesaler where a sushi restaurant needs very specific fish products, this matters.

### Why This Is Better Than Category-Based Similarity

Our Phase 1 candidate retrieval uses **category affinity** — if a customer buys a lot of dairy, recommend dairy offers. This has two problems:

1. **Too coarse.** "Dairy" contains both industrial mozzarella blocks (HoReCa) and small yogurt packs (individual). Category doesn't distinguish use case.
2. **Misses cross-category patterns.** A sushi restaurant buys salmon (seafood), rice (grocery), soy sauce (condiments), nori (grocery), wasabi (condiments). Category affinity would recommend more seafood. Basket embeddings know these products cluster together regardless of category.

Skip-gram embeddings capture **functional similarity** (products that serve the same meal/use case) rather than taxonomic similarity (products in the same category tree).

### Application to This System

**Candidate retrieval upgrade:**
```
Current:  category_affinity → SQL query → candidates
Upgraded: customer_embedding = mean(purchased_product_embeddings)
          → ANN search (FAISS) against offer product embeddings
          → candidates
```

**Customer embedding:** Average the embeddings of a customer's last N purchased products. This implicitly encodes their business type, cuisine, purchasing pattern — all without explicit feature engineering.

**Cold-start for new products:** A new SKU has no purchase history. But if its product description is similar to existing products (same category, similar name), you can initialize its embedding from the nearest neighbors. Not perfect, but far better than having no embedding at all.

---

## 2. Matrix Factorization — The Interaction Signal

Alongside skip-gram embeddings, Metro uses **matrix factorization** on the customer-product interaction matrix.

### The Core Idea

Build a sparse matrix where rows = customers, columns = products, values = interaction strength (purchase count, total spend, or implicit feedback like 1/0 bought):

```
              prod_1  prod_2  prod_3  ...  prod_10K
customer_1    [  5      0       3     ...    0    ]
customer_2    [  0      12      0     ...    7    ]
customer_3    [  2      0       0     ...    0    ]
...
customer_50K  [  0      0       8     ...    1    ]
```

Factorize into two low-rank matrices:

```
R ≈ U × V^T

U: (50K customers × k latent factors)
V: (10K products  × k latent factors)
```

Each customer and product gets a k-dimensional latent vector. The dot product `U[i] · V[j]` predicts customer i's affinity for product j.

### Algorithms

| Method | Mechanism | Pros | Cons |
|--------|-----------|------|------|
| **SVD** | Exact decomposition | Clean, interpretable | Doesn't handle sparsity well |
| **ALS (Alternating Least Squares)** | Iteratively fix U, solve V, then fix V, solve U | Handles implicit feedback, parallelizable | Needs tuning of regularization |
| **BPR (Bayesian Personalized Ranking)** | Pairwise loss: rank purchased items above non-purchased | Optimizes ranking directly | Slower convergence |
| **NMF (Non-negative MF)** | Like MF but forces non-negative factors | Interpretable factors (topics/themes) | More constrained |

For implicit feedback (which is what Metro has — they see purchases, not ratings), **ALS with implicit feedback** (Hu, Koren & Volinsky 2008) is the standard choice.

```python
from implicit.als import AlternatingLeastSquares
import scipy.sparse as sparse

# Build sparse interaction matrix
# rows=customers, cols=products, values=purchase_count
interaction_matrix = sparse.csr_matrix(...)  # (50K × 10K)

model = AlternatingLeastSquares(
    factors=64,
    regularization=0.01,
    iterations=15,
)
model.fit(interaction_matrix)

# Get recommendations for customer 42
customer_id = 42
ids, scores = model.recommend(
    customer_id,
    interaction_matrix[customer_id],
    N=20,
    filter_already_liked_items=True,
)
```

### What MF Captures That Skip-Gram Doesn't (And Vice Versa)

| Aspect | Skip-Gram (Basket Co-occurrence) | Matrix Factorization (Customer × Product) |
|--------|----------------------------------|-------------------------------------------|
| **Signal** | "These products are bought *together* in one trip" | "These products are bought by *similar customers*" |
| **Captures** | Functional complementarity (meal ingredients, recipe sets) | Taste/preference similarity (customer segments, business type patterns) |
| **Cold start** | New product needs to appear in baskets | New product needs purchases from any customer |
| **Strength** | Cross-category discovery | Personalization depth |

**They're complementary.** Skip-gram says "salmon and wasabi go together." MF says "customers who buy salmon also tend to buy this specific brand of soy sauce, and this particular knife set." Using both gives you richer signal than either alone.

### Application to This System

**As a candidate retrieval strategy:**
- Train ALS on the customer × product purchase matrix
- For each customer, MF directly produces a ranked list of products they haven't bought but are predicted to like
- These become candidates alongside the skip-gram ANN results

**As ranking features:**
- The MF score `U[customer] · V[product]` is itself a powerful feature for the downstream ranker
- Concatenate the customer's latent factors `U[i]` as features in the LightGBM/neural ranker

---

## 3. Two Types of Recommendations — Personalized vs. General

Metro runs **two parallel recommendation streams**, not one. This is a critical architectural distinction.

### General Recommendations

"What should we show to *everyone* (or a segment) this week?"

- **Input:** Global sales data, margin targets, inventory levels, seasonal calendar
- **Logic:** Popularity-weighted, business-rule-driven, merchandiser-curated
- **Examples:**
  - Weekly catalog offers (same for all HoReCa customers)
  - Seasonal pushes (Christmas hampers, Easter lamb)
  - Overstock clearance (high inventory → promote harder)
  - New product launches (METRO Chef new SKU → blast to relevant segment)
- **Who decides:** Category managers / merchandisers, with data support
- **Frequency:** Weekly catalog cycle, aligned with print/digital flyer

### Personalized Recommendations

"What should we show to *this specific customer* based on their history?"

- **Input:** Individual purchase history, browsing behavior, RFM state, redemption history
- **Logic:** ML-driven (skip-gram retrieval, MF scoring, supervised ranking)
- **Examples:**
  - "You bought salmon 3 times last month — here's a discount on METRO Chef salmon fillet"
  - "Customers like you also buy X" (collaborative filtering via MF)
  - "You haven't bought from dairy in 3 weeks — reactivation offer"
  - Cross-sell based on basket embeddings
- **Who decides:** The ML pipeline, with business guardrails (min margin, inventory check)
- **Frequency:** Triggered by CDP events (email cadence, app open, approaching store)

### Why Both Exist

| Concern | General | Personalized |
|---------|---------|--------------|
| **Coverage** | Ensures every customer sees *something* | Can't recommend if no history (cold start) |
| **Business control** | Merchandisers set strategy | ML optimizes within guardrails |
| **Margin management** | Push high-margin or overstock SKUs | May recommend low-margin items customer loves |
| **Novelty** | Introduces new products | Tends toward exploitation (repeat what worked) |
| **Cost** | Cheap — one set for a segment | Expensive — per-customer computation |

The general stream provides a **floor** — every customer gets reasonable offers. The personalized stream provides **lift** — individual relevance on top of the baseline.

### How They Combine in Practice

```
Final offer set for Customer X:
├── Slots 1-3: Personalized (highest ML-scored offers for this customer)
├── Slots 4-6: General (this week's catalog highlights for their segment)
├── Slot 7:   Personalized (cross-sell / discovery)
└── Slots 8-10: General (seasonal / new product push)
```

The mix ratio is itself tunable — loyal high-frequency customers get more personalized slots (the ML has strong signal). New or infrequent customers get more general slots (safer, less risk of irrelevant recommendations).

### Application to This System

Our Phase 1 is **entirely personalized** — every recommendation is ML-scored per customer. To be architecturally faithful to Metro's actual system:

1. **Add a general recommendation path** — segment-level "top offers" based on popularity, margin, and merchandiser rules. No ML needed, just smart SQL aggregation.
2. **Blend the two streams** — configurable mix ratio per customer based on their history depth. Customers with <5 orders get 70% general, 30% personalized. Customers with 50+ orders get 30% general, 70% personalized.
3. **Separate evaluation** — measure personalized NDCG and general NDCG independently, plus the blended result. The personalized model should beat the general baseline; the blend should beat both.

---

## 4. Takeaways — What Changes in This Project

### Immediate (Phase 2 Adjustments)

| Component | Current Plan | Updated Plan |
|-----------|-------------|--------------|
| **Candidate retrieval** | Generic "embedding-based retrieval" | Specifically: gensim Word2Vec skip-gram on basket sequences, not sentence-transformers on product descriptions |
| **Collaborative filtering** | Not explicitly planned | Add ALS matrix factorization as a parallel retrieval + feature source |
| **Recommendation types** | Single personalized stream | Dual stream: personalized (ML) + general (business rules), with blending |
| **Embedding model** | Sentence-transformers (text) | Product2Vec via skip-gram (behavioral) — text embeddings are supplementary, not primary |

### Architectural Insight

The most important learning: **Metro's embeddings are behavioral, not semantic.** They don't embed product *descriptions* — they embed product *purchase patterns*. A product's meaning is defined by who buys it and what they buy it with, not by its text label.

This is the Word2Vec insight applied to commerce: "You shall know a product by the company it keeps (in baskets)."

### The Skip-Gram + MF + Supervised Ranker Stack

This is a clean, proven three-layer architecture:

```
Layer 1 — Representation Learning (offline, periodic)
├── Skip-gram on baskets → product embeddings (functional similarity)
└── ALS on interactions  → customer & product latent factors (preference similarity)

Layer 2 — Candidate Retrieval (batch or near-real-time)
├── ANN search with customer embedding → skip-gram candidates
├── MF top-N for customer             → collaborative filtering candidates
├── Business rules                     → general/catalog candidates
└── Merge + dedup                      → ~200 candidates per customer

Layer 3 — Supervised Ranking (batch)
├── Features: RFM + offer attributes + MF score + embedding similarity + ...
├── Model: LightGBM (or neural ranker)
└── Output: ranked top-10 per customer (personalized + general blend)
```

Each layer has a clear job. Representation learning is expensive but infrequent (retrain weekly/monthly). Candidate retrieval is cheap and can run daily. Ranking is the precision layer that orders the final set.

### What This Means for Interview Conversations

When discussing this project, the framing shifts from "I built a recommender" to:

- "I replicated Metro's actual stack — skip-gram basket embeddings, matrix factorization, supervised ranking — and understand *why* each layer exists"
- "I know why behavioral embeddings (skip-gram on purchase sequences) beat semantic embeddings (sentence-transformers on descriptions) for this domain — because a product's meaning in a wholesale context is defined by its purchase context, not its text description"
- "I understand the dual recommendation architecture (personalized vs. general) and how the blend ratio adapts to customer maturity"
- "I can explain the tradeoffs between skip-gram (captures co-purchase complementarity) and matrix factorization (captures cross-customer preference similarity) and why you want both"
