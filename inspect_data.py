"""Data quality audit script for raw LUNA16 pulmonary nodule annotations.

Verifies schema integrity, missingness, entity cardinality, and physical
scanner coordinate ranges prior to feature engineering.

Reference:
- LUNA16 Challenge: https://luna16.grand-challenge.org/
- Dataset: Kaggle (eliasmarcon/luna-16)
"""

from pathlib import Path
from typing import Dict, Any
import pandas as pd


def audit_annotations(file_path: str) -> Dict[str, Any]:
  """Performs an integrity check on raw thoracic nodule annotations.

  Args:
      file_path: Relative or absolute path to the annotations CSV file.

  Returns:
      Dict[str, Any]: Dictionary containing summary audit metrics.

  Raises:
      FileNotFoundError: If the specified CSV does not exist.
      ValueError: If required columns are missing from the dataset.
  """
  path = Path(file_path)
  if not path.exists():
    raise FileNotFoundError(f"Target annotation file not found: {file_path}")

  df = pd.read_csv(path)

  required_columns = {
      "seriesuid",
      "coordX",
      "coordY",
      "coordZ",
      "diameter_mm",
  }
  missing_cols = required_columns - set(df.columns)
  if missing_cols:
    raise ValueError(f"Schema mismatch. Missing expected columns: {missing_cols}")

  # 1. Nullability and uniqueness
  null_counts = df.isnull().sum().to_dict()
  duplicate_count = int(df.duplicated().sum())
  total_findings = len(df)
  unique_studies = int(df["seriesuid"].nunique())

  # 2. Coordinate and size descriptive statistics
  numeric_cols = ["coordX", "coordY", "coordZ", "diameter_mm"]
  stats_summary = df[numeric_cols].describe().round(2).to_dict()

  print("=" * 60)
  print("LUNA16 RAW DATA INTEGRITY AUDIT REPORT")
  print("=" * 60)
  print(f"Total Finding Records : {total_findings}")
  print(f"Unique Studies (Scans): {unique_studies}")
  print(
      f"Findings / Study Ratio: {total_findings / unique_studies:.2f}"
  )
  print(f"Duplicate Rows Count  : {duplicate_count}")
  print("-" * 60)
  print("Missing Values Check:")
  for col, count in null_counts.items():
    print(f"  - {col:<12}: {count} nulls")
  print("-" * 60)
  print("Physical Scanner Coordinate Ranges (mm):")
  print(df[numeric_cols].describe().round(2))
  print("=" * 60)

  return {
      "total_findings": total_findings,
      "unique_studies": unique_studies,
      "null_counts": null_counts,
      "duplicates": duplicate_count,
      "statistics": stats_summary,
  }


if __name__ == "__main__":
  audit_annotations("annotations.csv")