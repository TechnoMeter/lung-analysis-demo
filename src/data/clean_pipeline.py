# src/data/clean_pipeline.py
"""
Data preprocessing pipeline for LUNA16 pulmonary nodule annotations.
Cleans raw coordinates, derives volumetric metrics, and enforces schema integrity.

Reference:
- LUNA16 Benchmark (Grand Challenge): https://luna16.grand-challenge.org/
- Dataset Source: Kaggle (eliasmarcon/luna-16)
"""

from pathlib import Path
import numpy as np
import pandas as pd


def preprocess_annotations(raw_path: str, output_path: str) -> pd.DataFrame:
    """Ingests raw LUNA16 annotations.csv, assigns primary keys, computes derived

    spherical volume, and exports a standardized findings table.

    Args:
        raw_path: Path to the raw LUNA16 annotations CSV.
        output_path: Destination path for the processed CSV.

    Returns:
        pd.DataFrame: Cleaned and structured findings dataframe.
    """
    raw_file = Path(raw_path)
    if not raw_file.exists():
        raise FileNotFoundError(f"Input file not found at {raw_path}")

    df = pd.read_csv(raw_file)

    # Deterministic finding-level primary key
    df.insert(0, "finding_id", [f"F-{i:04d}" for i in range(len(df))])

    # Spherical volume approximation: V = (pi / 6) * diameter^3
    df["volume_mm3"] = (np.pi / 6.0) * (df["diameter_mm"] ** 3)

    # Physical scanner precision alignment (0.01 mm)
    numeric_cols = ["coordX", "coordY", "coordZ", "diameter_mm", "volume_mm3"]
    df[numeric_cols] = df[numeric_cols].round(2)

    df["seriesuid"] = df["seriesuid"].astype(str)

    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_file, index=False)

    return df


if __name__ == "__main__":
  clean_df = preprocess_annotations(
      raw_path="./data/raw/annotations.csv",
      output_path="./data/processed/clean_findings.csv",
  )
  print(
      f"Pipeline executed successfully. Processed {len(clean_df)} findings."
  )
  print("\nProcessed Sample: (3 count)")
  print(clean_df.head(3))