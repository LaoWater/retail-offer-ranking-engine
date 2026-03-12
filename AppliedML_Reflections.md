# Applied ML Reflections — Production Recommender Systems

Practical notes on production ML challenges encountered while building a personalized offer ranking engine for a B2B wholesale environment (Metro Cash & Carry Romania scale).

---

## 1. False Positive Recommendations — Model Predicts Buy, Customer Doesn't

When the ranking model consistently scores customers as likely to redeem offers but they never do, the problem falls into one of three categories: **calibration**, **data quality**, or **concept drift**.

### Diagnosis

**Check the label definition first.** If a "positive" means the customer redeemed an offer, but impressions that were never actually seen (email unopened, push notification ignored) are labeled as negatives — the negative class is noisy. The model learns from unreliable signal.

**Check the score distribution, not just the binary output.** If 2% of impressions lead to redemptions and the model predicts 0.03 probability for everyone, but the threshold sits at 0.02, suddenly every customer looks "positive." The model might be directionally correct but poorly calibrated.

**Check if the model is just predicting popularity.** If the top-10 recommendations are nearly identical across customers, the model isn't personalizing — it's reflecting base rates. Compare how much recommendations differ across customers. High overlap = the model learned global popularity, not individual preference.

**Pull features for the false-positive cohort.** Compare their feature distributions against true positives. Look for systematic patterns — concentrated in one segment? One product category? One time window?

### Fixes

| Approach | What It Does | When To Use |
|----------|-------------|-------------|
| **Raise the decision threshold** | Require higher confidence before recommending. Top-5 with a minimum score cutoff instead of top-10. | Precision matters more than recall (don't annoy customers). |
| **Add negative feedback signals** | `times_impressed_no_action` as a feature — if a customer was sent an offer 3x and never redeemed, that's strong signal. | Model lacks explicit non-interest signals. |
| **Platt scaling / isotonic regression** | Post-hoc calibration maps raw model scores to true redemption probabilities. LightGBM outputs aren't true probabilities by default. | Score distribution is shifted or compressed. |
| **Segment-specific thresholds** | A HoReCa customer visiting 5x/week has different base rates than a Freelancer visiting monthly. One threshold doesn't fit all. | Mixed customer segments with different activity levels. |
| **Retrain on fresh data** | If the model was trained on winter patterns and it's summer, seasonal drift invalidates learned associations. | PSI monitoring flags distribution shift. |
| **Stratified evaluation** | Break down precision/recall by segment, category, recency. Global metrics hide localized failures. | Overall metrics look fine but specific cohorts suffer. |

### Systematic Response Framework

1. Examine whether it's a **calibration problem** (scores are wrong), a **data quality problem** (labels are wrong), or a **concept drift problem** (patterns changed).
2. Apply the corresponding fix.
3. Monitor with segment-level metrics, not just global averages.

---

## 2. GCP Vertex AI — Production ML Platform

Vertex AI is Google Cloud's managed ML platform. It handles the infrastructure layer: training compute, feature management, model deployment, and monitoring.

### Core Components

| Component | What It Does | Production Use Case |
|-----------|-------------|---------------------|
| **Training Pipelines** | Managed compute (CPU/GPU/TPU) for model training | Train LightGBM or deep models on full customer base (17M+ customers across 20+ countries) |
| **Feature Store** | Centralized feature repository with point-in-time correctness | Store customer RFM features, offer features — prevents training/serving skew |
| **Model Registry** | Version and track model artifacts with metadata | Keep v1 (LR), v2 (LightGBM), v3 (Wide & Deep) — rollback if needed |
| **Endpoints** | Deploy models as REST APIs with autoscaling | Serve recommendations in real-time with traffic splitting for A/B tests |
| **Pipelines (Kubeflow)** | Orchestrate ML workflows as directed acyclic graphs | Equivalent of a `daily_run.py` pipeline — but distributed and scheduled |
| **Model Monitoring** | Detect drift, skew, feature attribution shifts | Automated alerts when feature distributions diverge from training baseline |
| **Experiments** | Track hyperparameters, metrics, compare runs | Compare LightGBM vs Wide & Deep across multiple training configurations |
| **Vector Search** | Managed ANN index for embedding-based retrieval | Product similarity search, candidate retrieval at scale |

### Mapping Local Development to Vertex AI

| Local (Development) | Vertex AI (Production) |
|---------------------|----------------------|
| `daily_run.py` orchestration | Vertex Pipeline (Kubeflow DAG) |
| `models/ranker_latest.pkl` | Model Registry with versioning |
| `api.py` (FastAPI) | Vertex Endpoint with autoscaling |
| `drift.py` (PSI monitoring) | Vertex Model Monitoring |
| `features.py` output to SQLite | Vertex Feature Store |
| Manual retraining | Triggered retraining on drift detection |

### Training/Serving Skew

The Feature Store solves one of the most insidious production bugs: **training/serving skew**. This happens when features are computed differently at training time (batch, from historical data) vs serving time (real-time, from live data). The Feature Store provides a single source of truth for both paths, with point-in-time lookups ensuring training features reflect what was known at prediction time — not future information.

---

## 3. Document Indexing, Chunking, and Vector Search

### What Is an Index?

An index is a **data structure that makes search fast**. A database index on a column avoids full table scans. A vector index avoids comparing a query against every stored vector.

For vector embeddings:

| Index Type | Mechanism | Complexity | Tradeoff |
|-----------|-----------|------------|----------|
| **Brute force** | Compare query against all N vectors | O(N) | Exact results, doesn't scale |
| **IVF (Inverted File)** | Cluster vectors into buckets, search nearest buckets only | O(√N) | Fast, slight accuracy loss |
| **HNSW (Hierarchical Navigable Small World)** | Graph-based — vectors are nodes connected to approximate neighbors, query walks the graph | O(log N) | Very fast, higher memory |
| **Product Quantization** | Compress vectors into compact codes, search in compressed space | O(N) but fast constant | Low memory, lower accuracy |

Production systems (FAISS, ScaNN, Vertex Vector Search, Pinecone) combine these — e.g., IVF + PQ for large-scale, memory-efficient search.

### How to Chunk a Document

Bad chunking leads to bad retrieval. The goal is to preserve semantic coherence within each chunk while keeping chunks small enough for precise matching.

| Strategy | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **Fixed-size** | 512 tokens per chunk, 50-token overlap | Simple, predictable | Cuts mid-sentence, loses context |
| **Semantic** | Split by paragraph, section, or heading boundaries | Preserves meaning | Uneven chunk sizes |
| **Recursive** | Try splitting by heading → paragraph → sentence → token count | Best of both worlds | More complex implementation |
| **Sliding window** | Fixed window with 10-20% overlap between adjacent chunks | No information lost at boundaries | Redundancy, more vectors |

**Practical default:** Chunk by semantic boundaries (sections/paragraphs), target 256-512 tokens, 10-20% overlap between adjacent chunks.

### What to Store Per Chunk

```
{
  "chunk_id": "doc_42_chunk_7",
  "text": "original text of this chunk",
  "embedding": [0.023, -0.891, ...],       // 768 or 1536 dimensions
  "metadata": {
    "source_document": "product_catalog_2026.pdf",
    "page": 12,
    "section": "Dairy & Eggs",
    "chunk_index": 7
  }
}
```

**Summary indexing** is an optional technique: generate a summary of each chunk, embed the summary (not the raw text), and use that for matching. The summary is what gets compared during search, but the full chunk is what gets retrieved. This helps when chunks are detail-heavy but queries are high-level.

### Search Flow

```
Query: "mozzarella for restaurants"
  → Embed the query with the same model used for indexing
  → ANN search in the vector index → top-K nearest chunks by cosine similarity
  → (Optional) Re-rank with a cross-encoder for higher precision
  → Return chunk text + metadata
```

The embedding model must be the **same** at index time and query time — different models produce incompatible vector spaces.

---

## 4. Text Features as Vector Embeddings in a Recommender

### The Problem

Traditional recommender features are numeric or categorical: RFM scores, tier ratios, category IDs. But production systems have text data that carries rich signal:

- **Product descriptions:** "Fresh Atlantic salmon fillet, sushi-grade, 200g"
- **Customer business profiles:** "Italian restaurant, downtown Bucharest"
- **Offer copy:** "20% off all METRO Chef dairy products this week"

Categorical encoding (one-hot, label encoding) treats "Sushi restaurant" and "Japanese bistro" as completely unrelated. Text embeddings capture the semantic similarity.

### How to Use Text as Features

```
Raw text → Embedding model → Dense vector (e.g., 384 dims)
  → Concatenate with numeric features
  → Feed into the ranking model
```

Example with sentence-transformers:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions

product_emb = model.encode("Mozzarella METRO Chef 1kg bloc")      # (384,)
customer_emb = model.encode("Restaurant italian, centru Bucuresti") # (384,)

# These vectors become features alongside RFM scores, tier ratios, etc.
```

### Model Compatibility

| Model Type | Handles High-Dim Embeddings? | Notes |
|-----------|---------------------------|-------|
| **Logistic Regression** | Poorly | Too many dimensions relative to signal, needs PCA reduction |
| **LightGBM / XGBoost** | Somewhat | Tree models struggle with dense high-dimensional features; reduce to 32-64 dims via PCA |
| **Wide & Deep (neural)** | Natively | Deep path with embedding layers handles high-dimensional inputs directly |
| **Two-tower models** | Natively | Separate towers for user and item embeddings, learned end-to-end |

This is a key motivation for moving from classical ML (Phase 1: LR/LightGBM) to neural architectures (Phase 2: Wide & Deep): neural models consume embeddings naturally without dimensionality reduction.

### Practical Considerations

- **Embedding dimensionality:** 384 (MiniLM) to 1536 (OpenAI ada-002). Higher dims = more expressiveness but more compute and storage.
- **Pre-compute and cache:** Don't run the embedding model at serving time for every request. Embed products and customers offline, store the vectors, look them up at inference.
- **Fine-tuning:** General-purpose embedding models work, but fine-tuning on domain-specific text (product catalogs, Romanian food terminology) improves relevance.
- **Multilingual:** For Romanian text, use multilingual models (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) or fine-tune on Romanian corpora.

---

## Connections Across These Topics

These four areas are tightly linked in a production recommender:

1. **False positives** surface through monitoring → Vertex AI Model Monitoring automates drift detection and can trigger retraining pipelines.
2. **Vertex AI** provides the infrastructure to train, serve, and monitor models at scale — including the Feature Store that prevents training/serving skew (a common source of false positives).
3. **Vector indexing** (FAISS, Vertex Vector Search) powers embedding-based candidate retrieval — replacing heuristic rules with learned similarity.
4. **Text embeddings** as features unlock semantic understanding that categorical features miss — but require neural architectures (Wide & Deep, two-tower) to consume effectively, which in turn require Vertex AI's managed GPU training to scale.
