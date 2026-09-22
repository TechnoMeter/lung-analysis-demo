# src/api/routes/clusters.py
"""Aggregated cluster profile metrics for UI dashboard overview cards."""

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from src.api.schemas import ClusterProfile, ClusterSummaryResponse
from src.database.connection import get_db
from src.database.models import Finding

router = APIRouter(prefix="/api/v1/clusters", tags=["Clusters"])

CLUSTER_METADATA = {
    0: {
        "label": "Right Lung Typical",
        "description": "Standard-sized nodules distributed across the right pulmonary lobes.",
    },
    1: {
        "label": "High-Volume Lesions",
        "description": "Rare clinical masses with volumes up to 15x greater than typical nodules.",
    },
    2: {
        "label": "Left Lung Typical",
        "description": "Standard-sized nodules distributed across the left pulmonary lobes.",
    },
    3: {
        "label": "Axial Couch Outliers",
        "description": "Findings displaced along the Z-axis due to scanner table travel offsets.",
    },
}


@router.get(
    "/summary",
    response_model=ClusterSummaryResponse,
    summary="Aggregated Cluster Cohort Profiles",
)
def get_cluster_summary(db: Session = Depends(get_db)):
  """Computes mean dimensions, spatial positions, and sample counts grouped by cluster."""
  total_findings = db.query(Finding).count()

  stats = (
      db.query(
          Finding.cluster_id,
          func.count(Finding.finding_id).label("count"),
          func.avg(Finding.diameter_mm).label("mean_d"),
          func.avg(Finding.volume_mm3).label("mean_v"),
          func.avg(Finding.anomaly_score).label("mean_anomaly"),
          func.avg(Finding.coord_x).label("mean_x"),
          func.avg(Finding.coord_y).label("mean_y"),
          func.avg(Finding.coord_z).label("mean_z"),
      )
      .group_by(Finding.cluster_id)
      .order_by(Finding.cluster_id)
      .all()
  )

  profiles = []
  for row in stats:
    meta = CLUSTER_METADATA.get(
        row.cluster_id,
        {"label": f"Cluster {row.cluster_id}", "description": "Unclassified"},
    )
    count = row.count
    profiles.append(
        ClusterProfile(
            cluster_id=row.cluster_id,
            label=meta["label"],
            description=meta["description"],
            finding_count=count,
            percentage=round((count / total_findings) * 100, 2)
            if total_findings > 0
            else 0.0,
            mean_diameter_mm=round(float(row.mean_d), 2),
            mean_volume_mm3=round(float(row.mean_v), 2),
            mean_anomaly_score=round(float(row.mean_anomaly), 4),
            mean_coord_x=round(float(row.mean_x), 2),
            mean_coord_y=round(float(row.mean_y), 2),
            mean_coord_z=round(float(row.mean_z), 2),
        )
    )

  return ClusterSummaryResponse(
      total_findings=total_findings, clusters=profiles
  )