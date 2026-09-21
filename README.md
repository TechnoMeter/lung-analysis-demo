# lung-analysis-demo
A Three.js and vis.js interactive medical data mockup.

Obtained `./data/raw/annotations.csv` from the [LUNA16 Kaggle Dataset](https://www.kaggle.com/datasets/eliasmarcon/luna-16), containing 1,186 radiologist-confirmed pulmonary nodule findings across 601 thoracic CT studies.

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
| `finding_id` | String | Pipeline PK | Deterministic unique finding identifier (`F-0000` to `F-1185`). |
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

## Interface Design & Wireframes

The 4 core interface states were designed in [Excalidraw](https://excalidraw.com) to establish spatial hierarchy, interaction flows, and camera transitions before frontend development:

![Interface States](docs/ui_states.png)

1. **Macro Overview**: Full 3D coordinate space with faint anatomical lung silhouettes, global dataset indicators (601 studies, 1,186 findings), and filter controls.
2. **Cluster Focus**: Zoomed view isolating a single cluster, dimming background groups to reveal peripheral outlier points.
3. **Finding Details**: Direct target lock on a single nodule accompanied by a side panel displaying coordinates, diameter, and relative centroid distance.
4. **Relational Knowledge Graph**: A 2D vis.js network view mapping parent `Study (seriesuid)` down to `Finding`, `Cluster`, and measurement properties.

---

## Clinical Boundary and Disclaimer
This prototype is built strictly for pattern discovery and visual exploration. It does not provide medical diagnoses.