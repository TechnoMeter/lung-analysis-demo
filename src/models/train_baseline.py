# src/models/train_baseline.py
"""
Unsupervised baseline pipeline for LUNA16 pulmonary nodules.
Executes feature scaling, K-Means clustering, centroid-relative anomaly scoring,
and 3D PCA projection for WebGL visualization.
"""

from pathlib import Path
from typing import Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def build_unsupervised_baseline(
    input_path: str = "data/processed/clean_findings.csv",
    output_data_path: str = "data/processed/enriched_findings.csv",
    n_clusters: int = 4,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, float]:
  """Fits StandardScaler, KMeans, and PCA on nodule findings.

  Args:
      input_path: Path to clean findings CSV.
      output_data_path: Export path for enriched findings.
      n_clusters: Number of clusters (k) for K-Means.
      random_state: Seed for deterministic centroid initialization.

  Returns:
      Tuple[pd.DataFrame, float]: Enriched DataFrame and silhouette score.
  """
  clean_file = Path(input_path)
  if not clean_file.exists():
    raise FileNotFoundError(f"Input file not found at {input_path}")

  df = pd.read_csv(clean_file)

  # 1. Parsimonious 4-feature vector (excluding collinear diameter_mm)
  feature_cols = ["coordX", "coordY", "coordZ", "volume_mm3"]
  X = df[feature_cols].values

  # 2. Standardize features to zero mean, unit variance
  scaler = StandardScaler()
  X_scaled = scaler.fit_transform(X)

  # 3. Fit K-Means clustering
  kmeans = KMeans(
      n_clusters=n_clusters, init="k-means++", n_init=10, random_state=random_state
  )
  cluster_labels = kmeans.fit_predict(X_scaled)
  df["cluster_id"] = cluster_labels

  # Evaluate clustering cohesion
  sil_score = silhouette_score(X_scaled, cluster_labels)

  # 4. Compute Relative Anomaly Scores (Centroid Distances)
  centroids = kmeans.cluster_centers_
  assigned_centroids = centroids[cluster_labels]
  euclidean_distances = np.linalg.norm(X_scaled - assigned_centroids, axis=1)

  # Normalize distance to [0, 1] range for UI progress indicators
  min_max_scaler = MinMaxScaler()
  df["anomaly_score"] = min_max_scaler.fit_transform(
      euclidean_distances.reshape(-1, 1)
  ).round(4)

  # 5. PCA Projection for WebGL (4D -> 3D)
  pca = PCA(n_components=3, random_state=random_state)
  pca_coords = pca.fit_transform(X_scaled)

  df["pca_x"] = pca_coords[:, 0].round(3)
  df["pca_y"] = pca_coords[:, 1].round(3)
  df["pca_z"] = pca_coords[:, 2].round(3)

  # 6. Export Enriched Findings
  out_file = Path(output_data_path)
  out_file.parent.mkdir(parents=True, exist_ok=True)
  df.to_csv(out_file, index=False)

  # Save trained models for production inference
  models_dir = Path("models")
  models_dir.mkdir(exist_ok=True)
  joblib.dump(scaler, models_dir / "scaler.joblib")
  joblib.dump(kmeans, models_dir / "kmeans.joblib")
  joblib.dump(pca, models_dir / "pca.joblib")

  # Console Audit Report
  explained_var = pca.explained_variance_ratio_
  print("=" * 60)
  print("UNSUPERVISED AI BASELINE EXECUTION REPORT")
  print("=" * 60)
  print(f"Findings Processed     : {len(df)}")
  print(f"Clustering Features    : {feature_cols}")
  print(f"Optimal Clusters (k)   : {n_clusters}")
  print(f"Silhouette Score       : {sil_score:.4f}")
  print(f"PCA Variance Explained : {explained_var.sum() * 100:.2f}%")
  print(
      f"  - PC1: {explained_var[0]*100:.2f}%, PC2: {explained_var[1]*100:.2f}%,"
      f" PC3: {explained_var[2]*100:.2f}%"
  )
  print("-" * 60)
  print("Cluster Distribution:")
  print(df["cluster_id"].value_counts().sort_index())
  print("-" * 60)
  print(f"Enriched dataset written to: {output_data_path}")
  print("=" * 60)

  return df, sil_score


if __name__ == "__main__":
  build_unsupervised_baseline()