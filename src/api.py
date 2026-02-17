"""
FastAPI service for Metro Romania Personalized Offers Recommender.

Serves precomputed recommendations via REST API.

Usage:
    python -m src.api
    uvicorn src.api:app --host 0.0.0.0 --port 8000
"""

import json
import os
import logging
import threading
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import DB_PATH, API_HOST, API_PORT
from src.db import get_connection

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Metro Romania Offers Recommender API",
    description="Serve personalized offer recommendations for Metro Romania B2B customers.",
    version="1.0.0",
)

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class OfferRecommendation(BaseModel):
    offer_id: int
    product_id: int
    category: str
    brand: str
    offer_type: str
    discount_value: float
    tier1_price: float
    campaign_type: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0, description="Predicted P(redemption)")
    rank: int = Field(..., ge=1)
    expiry_date: str


class RecommendationResponse(BaseModel):
    customer_id: int
    business_type: str
    business_subtype: str
    run_date: str
    recommendations: List[OfferRecommendation]
    generated_at: str


class HealthResponse(BaseModel):
    status: str
    db_size_mb: float
    last_run_date: Optional[str] = None
    total_customers: int
    total_recommendations: int


class MetricsResponse(BaseModel):
    run_date: str
    metrics: dict


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

def get_db():
    """Dependency that provides a database connection."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health_check(conn=Depends(get_db)):
    """Health check with database stats."""
    try:
        total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        total_recs = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]

        last_run = conn.execute(
            "SELECT MAX(run_date) FROM recommendations"
        ).fetchone()[0]

        db_size = 0.0
        if os.path.exists(str(DB_PATH)):
            db_size = round(os.path.getsize(str(DB_PATH)) / (1024 * 1024), 1)

        return HealthResponse(
            status="healthy",
            db_size_mb=db_size,
            last_run_date=last_run,
            total_customers=total_customers,
            total_recommendations=total_recs,
        )
    except Exception as e:
        return HealthResponse(
            status=f"unhealthy: {e}",
            db_size_mb=0.0,
            total_customers=0,
            total_recommendations=0,
        )


@app.get("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    customer_id: int = Query(..., description="Customer ID"),
    run_date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), default: latest"),
    conn=Depends(get_db),
):
    """
    Get top-N personalized offers for a customer.

    Returns precomputed recommendations from the most recent daily run.
    """
    if run_date is None:
        row = conn.execute(
            "SELECT MAX(run_date) FROM recommendations"
        ).fetchone()
        if row is None or row[0] is None:
            raise HTTPException(status_code=404, detail="No recommendations available")
        run_date = row[0]

    # Check customer exists
    cust = conn.execute(
        "SELECT business_type, business_subtype FROM customers WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()
    if cust is None:
        raise HTTPException(
            status_code=404, detail=f"Customer {customer_id} not found"
        )
    business_type = cust[0]
    business_subtype = cust[1]

    # Fetch recommendations with offer/product details
    rows = conn.execute("""
        SELECT
            r.offer_id,
            r.score,
            r.rank,
            o.product_id,
            p.category,
            p.brand,
            o.offer_type,
            o.discount_value,
            o.end_date AS expiry_date,
            p.tier1_price,
            o.campaign_type
        FROM recommendations r
        JOIN offers o ON r.offer_id = o.offer_id
        JOIN products p ON o.product_id = p.product_id
        WHERE r.customer_id = ?
          AND r.run_date = ?
        ORDER BY r.rank ASC
    """, (customer_id, run_date)).fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No recommendations for customer {customer_id} on {run_date}",
        )

    recommendations = [
        OfferRecommendation(
            offer_id=row[0],
            score=round(row[1], 4),
            rank=row[2],
            product_id=row[3],
            category=row[4],
            brand=row[5],
            offer_type=row[6],
            discount_value=row[7],
            expiry_date=row[8],
            tier1_price=row[9],
            campaign_type=row[10],
        )
        for row in rows
    ]

    return RecommendationResponse(
        customer_id=customer_id,
        business_type=business_type,
        business_subtype=business_subtype,
        run_date=run_date,
        recommendations=recommendations,
        generated_at=datetime.now().isoformat(),
    )


@app.get("/recommendations/batch")
def get_batch_recommendations(
    customer_ids: str = Query(..., description="Comma-separated customer IDs"),
    run_date: Optional[str] = Query(None),
    conn=Depends(get_db),
):
    """Get recommendations for multiple customers."""
    ids = [int(x.strip()) for x in customer_ids.split(",") if x.strip()]

    if not ids:
        raise HTTPException(status_code=400, detail="No customer IDs provided")
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="Max 100 customers per batch")

    results = []
    errors = []

    for cid in ids:
        try:
            result = get_recommendations(customer_id=cid, run_date=run_date, conn=conn)
            results.append(result.model_dump())
        except HTTPException:
            errors.append(cid)

    return {
        "results": results,
        "total_requested": len(ids),
        "total_returned": len(results),
        "missing_customer_ids": errors,
        "run_date": run_date,
    }


@app.get("/customers/{customer_id}")
def get_customer_profile(customer_id: int, conn=Depends(get_db)):
    """Get customer profile and feature summary."""
    cust = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()

    if cust is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    feats = conn.execute(
        "SELECT * FROM customer_features WHERE customer_id = ?", (customer_id,)
    ).fetchone()

    profile = dict(cust)
    if feats:
        profile["features"] = dict(feats)

    return profile


# ---------------------------------------------------------------------------
# New endpoints for frontend
# ---------------------------------------------------------------------------

@app.get("/customers/sample")
def get_customer_sample(
    business_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    conn=Depends(get_db),
):
    """Get a random sample of customers for the selector dropdown."""
    if business_type:
        rows = conn.execute(
            """SELECT customer_id, business_name, business_type, business_subtype,
                      loyalty_tier, home_store_id
               FROM customers
               WHERE business_type = ?
               ORDER BY RANDOM() LIMIT ?""",
            (business_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT customer_id, business_name, business_type, business_subtype,
                      loyalty_tier, home_store_id
               FROM customers
               ORDER BY RANDOM() LIMIT ?""",
            (limit,),
        ).fetchall()

    return [dict(r) for r in rows]


@app.get("/customers/search")
def search_customers(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, le=100),
    conn=Depends(get_db),
):
    """Search customers by business name."""
    rows = conn.execute(
        """SELECT customer_id, business_name, business_type, business_subtype,
                  loyalty_tier, home_store_id
           FROM customers
           WHERE business_name LIKE ?
           ORDER BY business_name
           LIMIT ?""",
        (f"%{q}%", limit),
    ).fetchall()

    return [dict(r) for r in rows]


@app.get("/products/{product_id}")
def get_product_detail(product_id: int, conn=Depends(get_db)):
    """Get product details with tier pricing."""
    row = conn.execute(
        "SELECT * FROM products WHERE product_id = ?", (product_id,)
    ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

    return dict(row)


@app.get("/metrics")
def get_latest_metrics(conn=Depends(get_db)):
    """Get metrics from the latest pipeline run."""
    row = conn.execute("""
        SELECT run_date, metadata
        FROM pipeline_runs
        WHERE step = 'evaluate' AND status = 'completed'
        ORDER BY run_date DESC
        LIMIT 1
    """).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="No evaluation metrics available")

    return {"run_date": row[0], "metadata": row[1]}


@app.get("/stats")
def get_db_stats(conn=Depends(get_db)):
    """Database summary statistics."""
    def count(table: str) -> int:
        return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]

    last_run = conn.execute("SELECT MAX(run_date) FROM recommendations").fetchone()[0]

    db_size = 0.0
    if os.path.exists(str(DB_PATH)):
        db_size = round(os.path.getsize(str(DB_PATH)) / (1024 * 1024), 1)

    return {
        "total_customers": count("customers"),
        "total_products": count("products"),
        "total_offers": count("offers"),
        "total_orders": count("orders"),
        "total_recommendations": count("recommendations"),
        "db_size_mb": db_size,
        "last_run_date": last_run,
    }


@app.get("/pipeline/runs")
def get_pipeline_runs(
    limit: int = Query(10, le=100),
    conn=Depends(get_db),
):
    """Recent pipeline run log."""
    rows = conn.execute(
        """SELECT run_id, run_date, step, status, duration_seconds, metadata, created_at
           FROM pipeline_runs
           ORDER BY run_id DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()

    return [dict(r) for r in rows]


@app.post("/pipeline/simulate-day")
def simulate_day(conn=Depends(get_db)):
    """Run the daily pipeline for the next date."""
    # Get last run date
    row = conn.execute("SELECT MAX(run_date) FROM pipeline_runs").fetchone()
    last_date_str = row[0] if row and row[0] else None
    conn.close()

    if last_date_str:
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        next_date = last_date + timedelta(days=1)
    else:
        next_date = date.today()

    run_date = next_date.strftime("%Y-%m-%d")

    from src.daily_run import run_pipeline
    results = run_pipeline(run_date)

    return {
        "status": "completed",
        "run_date": run_date,
        "results": {
            k: {"status": v.get("status", "unknown"), "duration": v.get("duration", 0)}
            for k, v in results.items()
        },
    }


@app.post("/pipeline/simulate-week")
def simulate_week(conn=Depends(get_db)):
    """Run the daily pipeline for 7 consecutive days."""
    row = conn.execute("SELECT MAX(run_date) FROM pipeline_runs").fetchone()
    last_date_str = row[0] if row and row[0] else None
    conn.close()

    if last_date_str:
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    else:
        last_date = date.today() - timedelta(days=1)

    from src.daily_run import run_pipeline

    all_results = {}
    for i in range(1, 8):
        run_date = (last_date + timedelta(days=i)).strftime("%Y-%m-%d")
        results = run_pipeline(run_date)
        all_results[run_date] = {
            k: {"status": v.get("status", "unknown"), "duration": v.get("duration", 0)}
            for k, v in results.items()
        }

    final_date = (last_date + timedelta(days=7)).strftime("%Y-%m-%d")
    return {
        "status": "completed",
        "run_date": final_date,
        "results": all_results,
    }


@app.get("/drift/latest")
def get_drift_latest(conn=Depends(get_db)):
    """Latest drift report."""
    # Get the most recent run_date with drift data
    row = conn.execute(
        "SELECT MAX(run_date) FROM drift_log"
    ).fetchone()

    if row is None or row[0] is None:
        return {"run_date": None, "entries": [], "retrain_recommended": False}

    run_date = row[0]

    rows = conn.execute(
        """SELECT feature_name AS feature, psi_value AS psi, severity
           FROM drift_log
           WHERE run_date = ?
           ORDER BY psi_value DESC""",
        (run_date,),
    ).fetchall()

    entries = [dict(r) for r in rows]
    n_alerts = sum(1 for e in entries if e["severity"] == "alert")

    from src.config import DRIFT_RETRAIN_MIN_FEATURES
    return {
        "run_date": run_date,
        "entries": entries,
        "retrain_recommended": n_alerts >= DRIFT_RETRAIN_MIN_FEATURES,
    }


def main():
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    main()
