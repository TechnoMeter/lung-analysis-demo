# lung-analysis-demo
A Three.js and vis.js interactive medical data mockup.

Obtained `./data/raw/annotations.csv` from the [LUNA16 Kaggle Dataset](https://www.kaggle.com/datasets/eliasmarcon/luna-16), containing 1,186 radiologist-confirmed pulmonary nodule findings across 601 thoracic CT studies.

We deliberately bypassed `candidates_V2.csv` (which contains over 750,000 entries). That file is 99.8% algorithmic scanner noise (false alarms like blood vessels or bone tissue) and lacks nodule diameter. Loading that many points would freeze a WebGL browser canvas. `./data/raw/annotations.csv` gives 1,186 true clinical lesions with physical dimensions, ideal for 60 FPS 3D rendering and meaningful multi-feature clustering. 

---
```t
lung-analysis-demo/
├── data/
│   ├── raw/
│   │   └── annotations.csv        # 1,186 raw LUNA16 findings
│   └── processed/
│       └── clean_findings.csv     # 1,186 cleaned rows with finding_id & volume_mm3
├── docs/
│   └── ui_states.png              # 4-state Excalidraw design
├── notebooks/
│   └── 1_exploratory_analysis.ipynb              # EDA, PCA, and K-means clustering
├── src/
│   └── data/
│       ├── inspect_data.py        # Automated quality & coordinate audit
│       └── clean_pipeline.py      # Production cleaning & derivation pipeline
├── data_dictionary.md             # Column definitions and types
└── README.md                      # Architecture, formulas, and clinical boundary

```

## Data Dictionary (Finding-Level)

The preprocessed dataset (`./data/processed/clean_findings.csv`) standardizes physical measurements and introduces derived volumetric features:

| Column | Type | Source | Description |
| :--- | :--- | :--- | :--- |
| `finding_id` | String | Pipeline Surrogate Key | Deterministic unique finding identifier (`F-0000` to `F-1185`). |
| `seriesuid` | String | LUNA16 | DICOM Series Instance UID (CT scan session; 601 unique scans). |
| `coordX` | Float | LUNA16 | Coronal/Sagittal physical position in millimeters ($X=0$ is thoracic midline). |
| `coordY` | Float | LUNA16 | Anterior/Posterior physical position in millimeters. |
| `coordZ` | Float | LUNA16 | Axial scanner couch position in millimeters. |
| `diameter_mm` | Float | LUNA16 | Measured nodule diameter in millimeters (3.25 mm to 32.27 mm). |
| `volume_mm3` | Float | Derived | Calculated spherical volume in cubic millimeters ($V = \frac{\pi}{6} d^3$). |

---

## Mathematical & Engineering Rationale

### 1. Relational Cardinality (1:N)
- **Context:** The dataset contains 1,186 findings across 601 unique `seriesuid` entries, establishing an average ratio of 1.97 findings per study.
- **Decision:** Because `seriesuid` maps to the CT session rather than an individual lesion, assigning a deterministic primary key (`finding_id`: `F-0000` through `F-1185`) ensures relational integrity for PostgreSQL foreign keys and WebGL raycaster hit-testing.

### 2. Derived Spherical Volume Metric
- **Mathematical Formula:**

$$V = \frac{4}{3}\pi r^3 = \frac{4}{3}\pi \left(\frac{d}{2}\right)^3 = \frac{\pi}{6} d^3 \approx 0.5236 \cdot d^3$$

- **Engineering Justification:** While nodule diameter spans linearly from 3.25 mm to 32.27 mm, volume scales cubically (~17.97 mm³ to ~17,590.28 mm³). This non-linear transformation expands feature variance, allowing distance-based algorithms (K-means) to separate sub-centimeter nodules from large, atypical masses.

### 3. Spatial Resolution & Precision Rounding
- **Observation:** Raw scanner coordinates include up to 6 decimal places ($10^{-6}\text{ mm}$).
- **Physical Boundary:** Clinical CT scanners operate at voxel resolutions between 0.5 mm and 1.0 mm. Sub-micrometer floating-point data represents scanner noise rather than anatomical precision.
- **Decision:** All continuous coordinates are normalized to two decimal places (0.01 mm), matching real sensor resolution while cutting network payload sizes.

### 4. Axial (Z-Axis) Offset & Normalization
- **Observation:** `coordZ` spans -790.07 mm to +1790.49 mm.
- **Root Cause:** In clinical DICOM systems, the Z-axis reflects scanner table travel position relative to the gantry isocenter, which varies based on patient orientation and acquisition protocols.
- **Decision:** Because raw coordinates reflect scanner table offsets rather than pure anatomical relationships, standardization (`StandardScaler`) and PCA dimensionality reduction are mandatory before clustering.

---

## Exploratory Data Analysis & Feature Selection

Exploratory analysis was conducted in `notebooks/1_exploratory_analysis.ipynb` to evaluate distributions, anatomical geometry, and feature correlations prior to clustering:

### 1. Empirical Observations
- **Anatomical Alignment:** The transverse (axial) projection (`coordX` vs `coordY`) reveals two distinct bilateral point clouds representing the right and left lung cavities, with an expected void at `coordX` ≈ 0 mm corresponding to the anatomical mediastinum.
- **Scanner Couch Variance:** The coronal projection (`coordX` vs `coordZ`) confirms that while the bulk of findings align within Z in [-400, 0] mm, scanner table travel offsets span -790.07 mm to +1790.49 mm, demonstrating why coordinate standardization is mandatory.
- **Morphological Skew:** Nodule diameter presents a median of 6.44 mm (range: 3.25 mm to 32.27 mm), while derived spherical volume expands variance cubically with a median of 139.43 mm³ and extreme masses exceeding 17,500 mm³.
- **Spatial Independence:** Pearson correlation coefficients between spatial coordinates (X, Y, Z) and size metrics (diameter, volume) remain |r| < 0.08, proving that nodule morphology is statistically independent of spatial lung position.
- **Morphological Collinearity:** Cross-feature analysis revealed an expected high correlation between diameter and volume (r = 0.893). Because volume is derived cubically from diameter, including both inside distance-based clustering algorithms would double-count nodule size.

### 2. Feature Selection Strategy: Clustering vs. Presentation
To maintain metric balance without losing clinical interpretability, the pipeline decouples the algorithmic feature vector from the database schema:

| Feature | In Clustering Matrix? | In Presentation Schema? | Justification & Role |
| :--- | :--- | :--- | :--- |
| `coordX` | Yes | Yes | Lateral physical coordinate; separates left vs. right pulmonary lobes. |
| `coordY` | Yes | Yes | Sagittal physical coordinate; ventral vs. dorsal thoracic depth. |
| `coordZ` | Yes | Yes | Axial physical coordinate; vertical table travel position. |
| `volume_mm3` | Yes | Yes | Non-linear cubic mass; provides high-variance separation for large atypical masses. |
| `diameter_mm` | **No (Pruned)** | **Yes (Retained)** | Pruned from K-means to prevent morphology from dominating 40% of Euclidean distance; retained in PostgreSQL/UI for standard clinical threshold inspection. |

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
- The prototype's anomaly scores only reflect mathematical distance from cluster centroids. 
- It does not provide medical diagnoses.