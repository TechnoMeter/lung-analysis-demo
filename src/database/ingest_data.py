# src/database/ingest_data.py
"""Automated data ingestion pipeline populating PostgreSQL from enriched_findings.csv."""

import sys
from pathlib import Path

# Automatically inject project root into sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

# Existing imports follow
import pandas as pd
from sqlalchemy.orm import Session
from src.database.connection import Base, SessionLocal, engine
from src.database.models import Finding, Study


def ingest_findings(
    csv_path: str = "data/processed/enriched_findings.csv",
) -> None:
  """Initializes schema and ingests studies and findings in strict relational order."""
  data_file = Path(csv_path)
  if not data_file.exists():
    raise FileNotFoundError(f"Source CSV not found at: {csv_path}")

  print("[1/4] Connecting to PostgreSQL and creating schema tables...")
  Base.metadata.create_all(bind=engine)

  print(f"[2/4] Reading enriched dataset from {csv_path}...")
  df = pd.read_csv(data_file)
  total_findings = len(df)

  session: Session = SessionLocal()
  try:
    # 1. Ingest Parent Studies (Idempotent upsert verification)
    print("[3/4] Processing and inserting parent Study entities...")
    study_counts = df["seriesuid"].value_counts().to_dict()

    existing_studies = {
      s.seriesuid for s in session.query(Study.seriesuid).all()
    }
    new_studies = []

    for seriesuid, count in study_counts.items():
      if seriesuid not in existing_studies:
        new_studies.append(Study(seriesuid=seriesuid, finding_count=count))

    if new_studies:
      session.bulk_save_objects(new_studies)
      session.commit()
      print(f"      -> Inserted {len(new_studies)} new parent studies.")
    else:
      print("      -> All parent studies already present.")

    # 2. Ingest Child Findings
    print("[4/4] Processing and inserting child Finding records...")
    existing_finding_ids = {
      f.finding_id for f in session.query(Finding.finding_id).all()
    }

    new_findings = []
    for _, row in df.iterrows():
      fid = row["finding_id"]
      if fid not in existing_finding_ids:
        finding = Finding(
          finding_id=fid,
          seriesuid=row["seriesuid"],
          coord_x=float(row["coordX"]),
          coord_y=float(row["coordY"]),
          coord_z=float(row["coordZ"]),
          diameter_mm=float(row["diameter_mm"]),
          volume_mm3=float(row["volume_mm3"]),
          cluster_id=int(row["cluster_id"]),
          anomaly_score=float(row["anomaly_score"]),
          pca_x=float(row["pca_x"]),
          pca_y=float(row["pca_y"]),
          pca_z=float(row["pca_z"]),
        )
        new_findings.append(finding)

    if new_findings:
      session.bulk_save_objects(new_findings)
      session.commit()
      print(f"      -> Inserted {len(new_findings)} new nodule findings.")
    else:
      print("      -> All nodule findings already present.")

    # Ingestion Audit Verification
    study_total = session.query(Study).count()
    finding_total = session.query(Finding).count()

    print("=" * 60)
    print("DATABASE INGESTION AUDIT VERIFICATION")
    print("=" * 60)
    print(f"Parent Studies in DB   : {study_total} (Expected: 601)")
    print(f"Child Findings in DB   : {finding_total} (Expected: 1,186)")
    print(f"Relational Ratio       : {finding_total / study_total:.2f} findings/study")
    print("=" * 60)

    if study_total == 601 and finding_total == 1186:
      print("VERIFICATION SUCCESS: Exact record counts match dataset schema!")
    else:
      print(
        "VERIFICATION WARNING: Row counts deviate from canonical LUNA16 finding totals."
      )

  except Exception as e:
    session.rollback()
    print(f"ERROR: Ingestion failed. Transaction rolled back: {e}")
    raise
  finally:
    session.close()


if __name__ == "__main__":
  ingest_findings()