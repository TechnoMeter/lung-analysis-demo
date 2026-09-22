# scripts/verify_db_queries.py
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import func
from src.database.connection import SessionLocal
from src.database.models import Finding, Study

session = SessionLocal()

try:
  print("=" * 65)
  print("POSTGRESQL LIVE QUERY & AGGREGATION AUDIT")
  print("=" * 65)

  # 1. Relational Join: Query a scan and inspect its child findings
  sample_study = (
      session.query(Study).filter(Study.finding_count >= 3).first()
  )
  print(f"Sample Parent Study: {sample_study.seriesuid}")
  print(f"Child Finding Count: {len(sample_study.findings)}")
  for f in sample_study.findings:
    print(
        f"  - [{f.finding_id}] Cluster: {f.cluster_id} | d:"
        f" {f.diameter_mm:.2f}mm | Score: {f.anomaly_score:.2f} | 3D:"
        f" ({f.pca_x}, {f.pca_y}, {f.pca_z})"
    )

  # 2. Aggregation: Verify cluster counts match Day 4 K-means output
  print("-" * 65)
  print("Cluster Distribution in PostgreSQL:")
  cluster_counts = (
      session.query(Finding.cluster_id, func.count(Finding.finding_id))
      .group_by(Finding.cluster_id)
      .order_by(Finding.cluster_id)
      .all()
  )

  for c_id, count in cluster_counts:
    print(f"  Cluster {c_id}: {count} findings")

  # 3. Index Test: Retrieve high-anomaly outliers
  print("-" * 65)
  outliers = (
      session.query(Finding)
      .filter(Finding.anomaly_score >= 0.50)
      .order_by(Finding.anomaly_score.desc())
      .all()
  )
  print(f"High-Anomaly Outliers (Score >= 0.50): {len(outliers)}")
  for o in outliers[:3]:
    print(
        f"  - [{o.finding_id}] Score: {o.anomaly_score} | Vol:"
        f" {o.volume_mm3:.1f}mm³ | Study: {o.seriesuid[:18]}..."
    )
  print("=" * 65)

finally:
  session.close()