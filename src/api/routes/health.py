# src/api/routes/health.py
"""Diagnostic health route with active database connection verification."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.schemas import HealthResponse
from src.database.connection import get_db
from src.database.models import Finding, Study

router = APIRouter(tags=["Diagnostics"])


@router.get(
    "/health", response_model=HealthResponse, summary="System Health Status"
)
def check_health(db: Session = Depends(get_db)):
  """Pings PostgreSQL to verify live pool connectivity and checks record counts."""
  try:
    db.execute(text("SELECT 1"))
    studies_count = db.query(Study).count()
    findings_count = db.query(Finding).count()

    return HealthResponse(
        status="healthy",
        database="connected",
        total_studies=studies_count,
        total_findings=findings_count,
        timestamp=datetime.utcnow(),
    )
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Database unreachable: {str(e)}",
    )