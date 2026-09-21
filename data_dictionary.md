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