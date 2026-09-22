# scripts/seed_cloud_db.py
import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.models import Base, Study, Finding

CSV_PATH = PROJECT_ROOT / "data" / "processed" / "enriched_findings.csv"


def seed_database():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL environment variable is not set.")
        print("Usage: DATABASE_URL=\"postgresql://...\" python scripts/seed_cloud_db.py")
        sys.exit(1)

    # SQLAlchemy 2.0 requires the 'postgresql://' dialect prefix
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    print(f"Connecting to database: {database_url.split('@')[-1]}")
    engine = create_engine(database_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 1. Create tables if they do not exist
        print("Creating relational tables (studies, findings)...")
        Base.metadata.create_all(bind=engine)

        # 2. Check if already seeded
        existing_findings = session.scalar(select(func.count(Finding.finding_id)))
        if existing_findings and existing_findings > 0:
            print(f"[SKIP] Database already seeded with {existing_findings} findings.")
            return

        # 3. Read enriched dataset
        if not CSV_PATH.exists():
            print(f"[ERROR] Data file not found at: {CSV_PATH}")
            sys.exit(1)

        print(f"Reading {CSV_PATH.name}...")
        df = pd.read_csv(CSV_PATH)

        # 4. Insert Parent Studies (1:N Hierarchy)
        print("Seeding parent studies...")
        study_counts = df["seriesuid"].value_counts().to_dict()
        study_objects = [
            Study(seriesuid=uid, finding_count=count)
            for uid, count in study_counts.items()
        ]
        session.bulk_save_objects(study_objects)
        session.flush()

        # 5. Insert Child Findings
        print("Seeding child findings...")
        finding_objects = []
        for _, row in df.iterrows():
            finding_objects.append(
                Finding(
                    finding_id=row["finding_id"],
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
            )
        session.bulk_save_objects(finding_objects)
        session.commit()

        # 6. Audit & Verification
        total_studies = session.scalar(select(func.count(Study.seriesuid)))
        total_findings = session.scalar(select(func.count(Finding.finding_id)))
        print("\n==========================================")
        print("Cloud Database Seeding Complete!")
        print(f"  • Parent Studies:  {total_studies} (Expected: 601)")
        print(f"  • Child Findings:  {total_findings} (Expected: 1,186)")
        print("==========================================")

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Seeding failed with exception: {e}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()