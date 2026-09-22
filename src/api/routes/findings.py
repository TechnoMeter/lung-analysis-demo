# src/api/routes/findings.py
"""Spatial finding endpoints delivering 3D WebGL coordinates and filtered subsets."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.api.schemas import FindingListResponse, FindingResponse
from src.database.connection import get_db
from src.database.models import Finding

router = APIRouter(prefix="/api/v1/findings", tags=["Findings"])


@router.get(
    "",
    response_model=FindingListResponse,
    summary="Query Filtered Findings for 3D Viewport",
)
def get_findings(
    cluster_id: Optional[int] = Query(
        None, ge=0, le=3, description="Filter by cluster ID (0-3)"
    ),
    min_anomaly: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum relative anomaly score"
    ),
    max_anomaly: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Maximum relative anomaly score"
    ),
    limit: int = Query(
        1200, ge=1, le=2000, description="Maximum records to return"
    ),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
  """Retrieves findings with PCA coordinates.

  Uses PostgreSQL B-Tree indexes on cluster_id and anomaly_score.
  """
  query = db.query(Finding)

  if cluster_id is not None:
    query = query.filter(Finding.cluster_id == cluster_id)
  if min_anomaly is not None:
    query = query.filter(Finding.anomaly_score >= min_anomaly)
  if max_anomaly is not None:
    query = query.filter(Finding.anomaly_score <= max_anomaly)

  total_matches = query.count()
  records = (
      query.order_by(Finding.finding_id).offset(offset).limit(limit).all()
  )

  return FindingListResponse(
      total=total_matches, count=len(records), findings=records
  )


@router.get(
    "/{finding_id}",
    response_model=FindingResponse,
    summary="Get Single Finding by Surrogate ID",
)
def get_finding_by_id(finding_id: str, db: Session = Depends(get_db)):
  """Retrieves a single finding by surrogate key (e.g. F-0284) for the inspector drawer."""
  record = (
      db.query(Finding).filter(Finding.finding_id == finding_id.upper()).first()
  )
  if not record:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Finding '{finding_id}' not found.",
    )
  return record