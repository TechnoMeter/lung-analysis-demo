# Data Dictionary: Pulmonary Nodule Findings

The preprocessed and modeled dataset (`./data/processed/enriched_findings.csv`) and corresponding PostgreSQL `findings` table contain 1,186 records across 12 physical, clinical, and latent attributes:

| Column (CSV) | SQL Column | Type | Origin | Description |
| :--- | :--- | :--- | :--- | :--- |
| `finding_id` | `finding_id` | String / VARCHAR(16) | Pipeline Surrogate Key | Deterministic unique finding identifier (`F-0000` to `F-1185`). Primary Key. |
| `seriesuid` | `seriesuid` | String / VARCHAR(128) | LUNA16 Benchmark | DICOM Series Instance UID (CT scan session; 601 unique studies). Foreign Key to `studies`. |
| `coordX` | `coord_x` | Float / FLOAT | LUNA16 Benchmark | Coronal/Sagittal physical position in millimeters ($X=0$ is thoracic midline). |
| `coordY` | `coord_y` | Float / FLOAT | LUNA16 Benchmark | Anterior/Posterior physical position in millimeters. |
| `coordZ` | `coord_z` | Float / FLOAT | LUNA16 Benchmark | Axial scanner couch travel position in millimeters. |
| `diameter_mm` | `diameter_mm` | Float / FLOAT | LUNA16 Benchmark | Measured cross-sectional nodule diameter in millimeters (3.25 mm to 32.27 mm). |
| `volume_mm3` | `volume_mm3` | Float / FLOAT | Derived Feature | Calculated spherical volume ($V = \frac{\pi}{6} d^3$) in cubic millimeters. |
| `cluster_id` | `cluster_id` | Integer / INTEGER | K-Means ($k=4$) | Assigned cluster index (0: Right Typical, 1: High-Volume Outliers, 2: Left Typical, 3: Axial Couch Outliers). B-Tree Indexed. |
| `anomaly_score` | `anomaly_score` | Float / FLOAT | Derived Metric | Normalized Euclidean distance from assigned cluster centroid ($[0.0, 1.0]$). B-Tree Indexed. |
| `pca_x` | `pca_x` | Float / FLOAT | PCA Dimension 1 | First principal component coordinate for WebGL 3D scene rendering (32.07% variance). |
| `pca_y` | `pca_y` | Float / FLOAT | PCA Dimension 2 | Second principal component coordinate for WebGL 3D scene rendering (25.65% variance). |
| `pca_z` | `pca_z` | Float / FLOAT | PCA Dimension 3 | Third principal component coordinate for WebGL 3D scene rendering (24.42% variance). |