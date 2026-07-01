from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.dependencies import get_db
import time

router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
def check_health(db: Session = Depends(get_db)):
    """Health check endpoint to verify API and Database status."""
    start_time = time.time()
    db_status = "unhealthy"
    db_latency_ms = None
    
    try:
        db_start = time.time()
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - db_start) * 1000, 2)
        db_status = "healthy"
    except Exception:
        # Gracefully handle database checks without crashing health endpoint
        pass

    api_latency_ms = round((time.time() - start_time) * 1000, 2)
    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "timestamp": time.time(),
        "api": {
            "status": "healthy",
            "latency_ms": api_latency_ms
        },
        "database": {
            "status": db_status,
            "latency_ms": db_latency_ms
        }
    }
