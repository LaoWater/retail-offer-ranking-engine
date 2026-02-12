"""
FastAPI service for Metro Personalized Offers Recommender.

Serves precomputed recommendations via REST API.

Usage:
    python -m src.api
    uvicorn src.api:app --host 0.0.0.0 --port 8000
"""

import os
from datetime import date, datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from src.config import DB_PATH, API_HOST, API_PORT
from src.db import get_connection

app = FastAPI(
    title="Metro Offers Recommender API",
    description="Serve personalized offer recommendations for Metro customers.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class OfferRecommendation(BaseModel):
    offer_id: int
    product_id: int
    category: str
    brand: str
    discount_type: str
    discount_value: float
    score: float = Field(..., ge=0.0, le=1.0, description="Predicted P(redemption)")
    rank: int = Field(..., ge=1)
    expiry_date: str


class RecommendationResponse(BaseModel):
    customer_id: int
    segment: str
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
    # Resolve run_date
    if run_date is None:
        row = conn.execute(
            "SELECT MAX(run_date) FROM recommendations"
        ).fetchone()
        if row is None or row[0] is None:
            raise HTTPException(status_code=404, detail="No recommendations available")
        run_date = row[0]

    # Check customer exists
    cust = conn.execute(
        "SELECT segment FROM customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if cust is None:
        raise HTTPException(
            status_code=404, detail=f"Customer {customer_id} not found"
        )
    segment = cust[0]

    # Fetch recommendations with offer/product details
    rows = conn.execute("""
        SELECT
            r.offer_id,
            r.score,
            r.rank,
            o.product_id,
            p.category,
            p.brand,
            o.discount_type,
            o.discount_value,
            o.end_date AS expiry_date
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
            discount_type=row[6],
            discount_value=row[7],
            expiry_date=row[8],
        )
        for row in rows
    ]

    return RecommendationResponse(
        customer_id=customer_id,
        segment=segment,
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


def main():
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    main()
