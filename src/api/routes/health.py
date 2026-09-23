# src/api/routes/health.py
"""Diagnostic health route with active database connection verification."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.api.schemas import HealthResponse
from src.database.connection import get_db
from src.database.models import Finding, Study

router = APIRouter(tags=["Diagnostics"])


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    summary="System Health Status",
)
@router.api_route(
    "/health/",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    include_in_schema=False,
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
        timestamp=datetime.now(timezone.utc),
    )
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Database unreachable: {str(e)}",
    )