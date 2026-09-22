# lung-analysis-demo
> **Interactive Thoracic Computed Tomography Discovery Platform** powered by Three.js (3D Spatial Viewport), vis.js (2D Relational Knowledge Graph), FastAPI, and Dockerized PostgreSQL.

Obtained `./data/raw/annotations.csv` from the [LUNA16 Kaggle Benchmark](https://www.kaggle.com/datasets/eliasmarcon/luna-16), containing 1,186 radiologist-confirmed pulmonary nodule findings across 601 thoracic CT studies.

We deliberately bypassed `candidates_V2.csv` (which contains over 750,000 entries). That file is 99.8% algorithmic scanner noise (false alarms like blood vessels or bone tissue) and lacks nodule diameter. Loading that many points would freeze a WebGL browser canvas. `./data/raw/annotations.csv` gives 1,186 true clinical lesions with physical dimensions, enabling 60 FPS 3D rendering and meaningful multi-feature clustering.

---

```text
lung-analysis-demo/
├── docker-compose.yml              # Container specification (postgres:16-alpine)
├── .env.example                    # Environment variable template for DB connection
├── data/
│   ├── raw/
│   │   └── annotations.csv        # 1,186 raw LUNA16 confirmed findings
│   └── processed/
│       ├── clean_findings.csv     # 1,186 cleaned rows with finding_id & volume_mm3
│       └── enriched_findings.csv  # 1,186 modeled rows with clusters, scores & PCA
├── docs/
│   └── ui_states.png              # 4-state Excalidraw UI architecture
├── notebooks/
│   └── 1_exploratory_analysis.ipynb # Distribution, spatial Exploratory Data Analysis, & clustering
├── src/
│   ├── data/
│   │   ├── inspect_data.py        # Automated quality & coordinate audit
│   │   └── clean_pipeline.py      # Production cleaning & derivation pipeline
│   ├── models/
│   │   └── train_baseline.py      # Unsupervised K-means, anomaly scoring & PCA
│   └── database/
│       ├── connection.py          # SQLAlchemy 2.0 engine & session factory
│       ├── models.py              # Normalized 1:N ORM models (Study & Finding)
│       └── ingest_data.py         # Idempotent bulk ingestion pipeline
├── scripts/
│   ├── verify_pca_variance.py     # Empirical PCA 4D vs 5D variance comparison
│   └── verify_db_queries.py       # Live PostgreSQL query, join & aggregation audit
├── models/
│   ├── scaler.joblib              # Serialized StandardScaler for inference
│   ├── kmeans.joblib              # Serialized KMeans (k=4) model
│   └── pca.joblib                 # Serialized 3D PCA projection model
├── data_dictionary.md             # Complete 12-column entity dictionary
└── README.md                      # Architecture, mathematics, and system design
```

---

## Relational Schema & Data Architecture

To transition from static CSV files to a transactional data layer supporting real-time spatial filtering and relational graph queries, findings are modeled across two normalized tables enforcing Third Normal Form (3NF):

```text
┌────────────────────────────────────────────────────────┐
│                     studies (Parent)                   │
├────────────────────────────────────────────────────────┤
│ PK  seriesuid     VARCHAR(128)                         │
│     finding_count INT                                  │
│     created_at    TIMESTAMP                            │
└────────────────────────────────────────────────────────┘
                            │ 1
                            │
                            │ N (FK: seriesuid, ON DELETE CASCADE)
                            ▼
┌────────────────────────────────────────────────────────┐
│                    findings (Child)                    │
├────────────────────────────────────────────────────────┤
│ PK  finding_id    VARCHAR(16)                          │
│ FK  seriesuid     VARCHAR(128) -> studies(seriesuid)   │
│     coord_x       FLOAT                                │
│     coord_y       FLOAT                                │
│     coord_z       FLOAT                                │
│     diameter_mm   FLOAT                                │
│     volume_mm3    FLOAT                                │
│ IX  cluster_id    INTEGER                              │
│ IX  anomaly_score FLOAT                                │
│     pca_x         FLOAT                                │
│     pca_y         FLOAT                                │
│     pca_z         FLOAT                                │
│     created_at    TIMESTAMP                            │
└────────────────────────────────────────────────────────┘
```

### Relational Attribute Dictionary (`findings`)

| Column | Type | Source | Description |
| :--- | :--- | :--- | :--- |
| `finding_id` | String | Pipeline Surrogate Key | Deterministic unique finding identifier (`F-0000` to `F-1185`). Primary Key. |
| `seriesuid` | String | LUNA16 Benchmark | Foreign key referencing parent `studies.seriesuid` (601 unique CT scans). |
| `coord_x` | Float | LUNA16 Benchmark | Lateral physical coordinate in millimeters ($X=0$ is sagittal thoracic midline). |
| `coord_y` | Float | LUNA16 Benchmark | Anterior/Posterior physical coordinate in millimeters. |
| `coord_z` | Float | LUNA16 Benchmark | Axial scanner couch travel coordinate in millimeters. |
| `diameter_mm` | Float | LUNA16 Benchmark | Measured cross-sectional nodule diameter in millimeters (3.25 mm to 32.27 mm). |
| `volume_mm3` | Float | Derived Feature | Calculated continuous spherical volume ($V = \frac{\pi}{6} d^3$) in mm³. |
| `cluster_id` | Integer | K-Means ($k=4$) | Assigned cluster index (0: Right Typical, 1: High-Volume Outliers, 2: Left Typical, 3: Axial Couch Outliers). Indexed. |
| `anomaly_score` | Float | Centroid Distance | Normalized Euclidean distance from assigned cluster centroid ($[0.0, 1.0]$). Indexed. |
| `pca_x` | Float | PCA Dimension 1 | First principal component coordinate for WebGL 3D scene rendering (32.07% variance). |
| `pca_y` | Float | PCA Dimension 2 | Second principal component coordinate for WebGL 3D scene rendering (25.65% variance). |
| `pca_z` | Float | PCA Dimension 3 | Third principal component coordinate for WebGL 3D scene rendering (24.42% variance). |

---

## Mathematical & Engineering Rationale

### 1. Relational Cardinality ($1:N$)
- **Context:** The dataset contains 1,186 confirmed findings distributed across 601 unique `seriesuid` entries, establishing an average ratio of 1.97 findings per study.
- **Decision:** Because `seriesuid` maps to the CT session rather than an individual lesion, assigning an immutable surrogate key (`finding_id`: `F-0000` through `F-1185`) ensures relational integrity for PostgreSQL foreign keys and WebGL raycaster hit-testing.

### 2. Derived Spherical Volume for 3D Graphics & Feature Variance
- **Mathematical Formula:**

$$V = \frac{4}{3}\pi r^3 = \frac{4}{3}\pi \left(\frac{d}{2}\right)^3 = \frac{\pi}{6} d^3 \approx 0.5236 \cdot d^3$$

- **Graphics Justification (Three.js):** Raw data provides only a 1D linear span (`diameter_mm`). Human lungs are 3D spatial volumes, and our visualization engine renders physical 3D spherical meshes in WebGL. Deriving continuous volume gives the graphics engine the physical basis to scale and render true volumetric mass in the thoracic viewport.
- **Machine Learning Justification:** Fleischner Society clinical guidelines evaluate lesion progression by volumetric doubling time. In Euclidean distance math, diameter scales linearly ($3.25\text{ mm}$ to $32.27\text{ mm}$), while volume scales cubically ($17.97\text{ mm}^3$ to $17,590.28\text{ mm}^3$). This non-linear transformation expands feature variance, allowing K-Means to clearly separate sub-centimeter nodules from massive, atypical lesions.

### 3. Spatial Resolution & Precision Rounding
- **Observation:** Raw scanner coordinates include up to 6 decimal places ($10^{-6}\text{ mm} = 1\text{ nanometer}$).
- **Physical Boundary:** Clinical CT scanners operate at voxel resolutions between $0.5\text{ mm}$ and $1.0\text{ mm}$. A macro medical scanner cannot physically resolve nanometers; the extra decimals represent digital floating-point sensor noise.
- **Decision:** All continuous coordinates are normalized to two decimal places ($0.01\text{ mm}$), matching real hardware limits while reducing JSON network payload size.

### 4. Axial ($Z$-Axis) Offset & Normalization
- **Observation:** `coordZ` spans $-790.07\text{ mm}$ to $+1790.49\text{ mm}$.
- **Root Cause:** In clinical DICOM systems, the $Z$-axis reflects scanner table travel position relative to the gantry isocenter, which varies based on patient orientation and hospital acquisition protocols.
- **Decision:** Because raw coordinates reflect scanner table offsets rather than pure anatomical relationships, standardization (`StandardScaler`) is mandatory before distance-based clustering.

---

## Exploratory Data Analysis & Feature Selection

Exploratory analysis was conducted in `notebooks/1_exploratory_analysis.ipynb` to evaluate distributions, anatomical geometry, and feature correlations prior to clustering:

### 1. Empirical Observations
- **Anatomical Alignment:** The transverse (axial) projection (`coord_x` vs `coord_y`) reveals two distinct bilateral point clouds representing the right and left lung cavities, with an expected void at `coord_x` $\approx 0\text{ mm}$ corresponding to the anatomical mediastinum (spine, heart, trachea).
- **Scanner Couch Variance:** The coronal projection (`coord_x` vs `coord_z`) confirms that while the bulk of findings align within $Z \in [-400, 0]\text{ mm}$, scanner table travel offsets span $-790.07\text{ mm}$ to $+1790.49\text{ mm}$, demonstrating why coordinate standardization is mandatory.
- **Morphological Skew:** Nodule diameter presents a median of $6.44\text{ mm}$ (range: $3.25\text{ mm}$ to $32.27\text{ mm}$), while derived spherical volume expands variance cubically with a median of $139.43\text{ mm}^3$ and extreme masses exceeding $17,500\text{ mm}^3$.
- **Spatial Independence:** Pearson correlation coefficients between spatial coordinates ($X, Y, Z$) and size metrics ($d, V$) remain $|r| < 0.08$, proving that nodule morphology is statistically independent of spatial lung position.
- **Morphological Collinearity:** Cross-feature analysis revealed a high correlation between diameter and volume ($r = 0.893$). Because volume is derived cubically from diameter, including both inside distance-based clustering algorithms would double-count nodule size.

### 2. Feature Selection Strategy: Clustering vs. Presentation
To maintain metric balance without losing clinical interpretability, the pipeline decouples the algorithmic feature vector from the database schema:

| Feature | In Clustering Matrix? | In Presentation Schema? | Justification & Role |
| :--- | :--- | :--- | :--- |
| `coord_x` | Yes | Yes | Lateral physical coordinate; separates left vs. right pulmonary lobes. |
| `coord_y` | Yes | Yes | Sagittal physical coordinate; ventral vs. dorsal thoracic depth. |
| `coord_z` | Yes | Yes | Axial physical coordinate; vertical table travel position. |
| `volume_mm3` | Yes | Yes | Non-linear cubic mass; provides high-variance separation for large atypical masses. |
| `diameter_mm` | **No (Pruned)** | **Yes (Retained)** | Pruned from K-means to prevent morphology from dominating 40% of Euclidean distance; retained in PostgreSQL/UI for standard clinical threshold inspection. |

---

## Unsupervised AI Baseline & Latent Projection 

To power visual clustering and explainable outlier identification without ground-truth diagnostic labels, findings are processed through an unsupervised learning pipeline in `src/models/train_baseline.py`:

```text
Input Vector (1,186 findings)
│
├── Preserved (passthrough): [finding_id, seriesuid, diameter_mm]
│
└── Clustering Vector: [coordX, coordY, coordZ, volume_mm3]
    │
    ▼
    1. StandardScaler (Z-Score Normalization)
    │
    ▼
    2. K-Means Clustering (k=4, k-means++ initialization)
    │
    ├──► 3. Relative Anomaly Scoring (distance to assigned centroid)
    │
    └──► 4. PCA Dimensionality Reduction (4D -> 3D WebGL coordinates)
    │
    ▼
    Enriched Dataset: data/processed/enriched_findings.csv
```

### 1. Model Configuration & Validation Metrics
- **Feature Standardization:** Features are scaled to zero mean and unit variance ($z = \frac{x - \mu}{\sigma}$) to prevent volumetric cubic variance from dominating physical coordinates in Euclidean space.
- **Cluster Count ($k=4$):** Evaluated at a **Silhouette Score of 0.3726**. Partitions findings into bilateral anatomical regions (Cluster 0: Right Lung Typical, Cluster 2: Left Lung Typical) while isolating rare high-volume lesions into dedicated outlier groups (Clusters 1 and 3).
- **PCA 3D Projection:** Projects 4D feature space to 3 visual coordinates (`pca_x`, `pca_y`, `pca_z`) for Three.js rendering, preserving **82.13% of total dataset variance** (PC1: 32.07%, PC2: 25.65%, PC3: 24.42%).

### 2. Empirical Verification: 4D  vs. 5D  PCA
An empirical experiment was executed in `scripts/verify_pca_variance.py` to evaluate the impact of feature collinearity ($r = 0.893$ between diameter and volume) on dimensionality reduction:

| Metric |  4D ($X, Y, Z, V$) |  5D ($X, Y, Z, d, V$) | Variance / Structural Impact |
| :--- | :--- | :--- | :--- |
| **PC1 Variance** | 32.07% | 38.09% | **+6.02%** artificial inflation due to duplicated size signal. |
| **PC2 Variance** | 25.65% | 25.46% | -0.19% |
| **PC3 Variance** | 24.42% | 19.99% | **-4.43%** compression of tertiary spatial signal. |
| **Total 3D Variance** | 82.13% | 83.53% | Naive 5D discards 2 full dimensions; 4D only discards 1. |

*Takeaway:* While the 5D model yields a marginally higher nominal variance (+1.40%), PC1 inflates because PCA captures the duplicated size concept twice. Pruning diameter retains an equitable balance across all spatial axes ($X, Y, Z$) and volume.

### 3. Empirical Cluster Profiles (Empirical Means)

| Cluster ID | Findings ($n$) | Description | Mean $X$ (mm) | Mean $Y$ (mm) | Mean $Z$ (mm) | Mean $d$ (mm) | Mean $V$ (mm³) | Mean Anomaly |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cluster 0** | 593 (50.0%) | Right Lung Typical | -77.07 | +7.65 | -209.57 | 7.48 | 383.74 | 0.13 |
| **Cluster 1** | 67 (5.6%) | High-Volume Outliers | +8.79 | +17.81 | -170.15 | 22.00 | 5,859.90 | 0.22 |
| **Cluster 2** | 494 (41.7%) | Left Lung Typical | +80.70 | +10.74 | -190.26 | 7.46 | 381.91 | 0.12 |
| **Cluster 3** | 32 (2.7%) | Axial Couch Outliers | -23.79 | -32.54 | +1,241.12 | 8.03 | 456.87 | 0.24 |

### 4. Relative Anomaly Scoring Metric
To provide an intuitive metric for the UI Finding Detail drawer without making medical diagnoses, anomaly scores represent normalized Euclidean distance from each finding $i$ to its assigned cluster centroid $\boldsymbol{\mu}_{c(i)}$:

$$d_i = \|\mathbf{z}_i - \boldsymbol{\mu}_{c(i)}\|_2 = \sqrt{\sum_{j=1}^{4} (z_{ij} - \mu_{c(i), j})^2}$$

$$\text{AnomalyScore}_i = \frac{d_i - d_{\min}}{d_{\max} - d_{\min}} \in [0.0, 1.0]$$

Findings near $0.0$ represent typical, centrally clustered nodules; findings approaching $1.0$ reflect geometric or volumetric outliers located on the periphery of their cluster.

---

## Relational Schema, Dockerization & Data Ingestion 

To transition from static CSV files to a transactional data layer supporting real-time spatial filtering and relational graph queries, findings were modeled and ingested into a Dockerized PostgreSQL database:

### 1. Database Architecture & Containerization
- **Docker Compose Deployment:** The database runs via `docker-compose.yml` on `postgres:16-alpine`, keeping host operating systems clean and ensuring reproducible dev-to-prod parity.
- **The 12-Factor App Standard:** Configured entirely through dynamic `DATABASE_URL` environment variables, enabling the system to run locally against Docker (`postgresql://postgres:postgres@localhost:5432/lung_analysis_db`) and switch to cloud managed PostgreSQL (Neon/Supabase) with zero code changes.
- **Relational Normalization (3NF):** Segregating CT acquisition sessions (`studies`, 601 rows) from individual nodule detections (`findings`, 1,186 rows) eliminates redundant metadata storage and prevents orphaned child records via `ON DELETE CASCADE`.
- **Index Optimization:** B-Tree indexes on `cluster_id` and `anomaly_score` allow the FastAPI backend to execute sub-millisecond range scans and categorical filtering.

### 2. Ingestion Pipeline (`src/database/ingest_data.py`)
- **Ordered Ingestion:** Evaluates and seeds parent studies first before attaching child findings, satisfying foreign key constraints.
- **Idempotency & Bulk Operations:** Employs `bulk_save_objects` wrapped inside an atomic transaction block. Rerunning the script checks existing keys to prevent primary key collisions.
- **Live Ingestion Audit Verification:**
  - Parent Studies Ingested: **601** (100% canonical match)
  - Child Findings Ingested: **1,186** (100% canonical match)
  - Enforced Cardinality: **1.97 findings / study**
  - High-Anomaly Verification: Identified isolated outliers `F-0765` (score: `1.0`, volume: $17,595.3\text{ mm}^3$) and `F-0034` (score: `0.7737`, volume: $15,017.8\text{ mm}^3$).

---

## Interface Design & Wireframes

The 4 core interface states were designed in [Excalidraw](https://excalidraw.com) to establish spatial hierarchy, interaction flows, and camera transitions before frontend development:

![Interface States](docs/ui_states.png)

1. **Macro Overview**: Full 3D coordinate space with faint anatomical lung silhouettes, global dataset indicators (601 studies, 1,186 findings), and filter controls.
2. **Cluster Focus**: Zoomed view isolating a single cluster, dimming background groups to reveal peripheral outlier points.
3. **Finding Details**: Direct target lock on a single nodule accompanied by a side panel displaying coordinates, diameter, and relative centroid distance.
4. **Relational Knowledge Graph**: A 2D vis.js network view mapping parent `Study (seriesuid)` down to `Finding`, `Cluster`, and measurement properties.

---

## Clinical Boundary and Disclaimer
- This prototype is built strictly for pattern discovery and visual exploration.
- The prototype's anomaly scores only reflect mathematical distance from cluster centroids in standardized feature space.
- It does not provide medical diagnoses, tumor staging, or clinical risk assessments.