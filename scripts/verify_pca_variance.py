# scripts/verify_pca_variance.py
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("data/processed/clean_findings.csv")

# 1. Our 4D Parsimonious Vector (X, Y, Z, Volume)
features_4d = ["coordX", "coordY", "coordZ", "volume_mm3"]
X_4d = StandardScaler().fit_transform(df[features_4d].values)
pca_4d = PCA(n_components=3, random_state=42).fit(X_4d)
var_4d = pca_4d.explained_variance_ratio_

# 2. The Naive 5D Vector (X, Y, Z, Diameter, Volume)
features_5d = ["coordX", "coordY", "coordZ", "diameter_mm", "volume_mm3"]
X_5d = StandardScaler().fit_transform(df[features_5d].values)
pca_5d = PCA(n_components=3, random_state=42).fit(X_5d)
var_5d = pca_5d.explained_variance_ratio_

print("=" * 65)
print("PCA 3D PROJECTION: 4D vs. 5D VARIANCE COMPARISON")
print("=" * 65)
print(f"4D Model (X, Y, Z, Volume):")
print(
    f"  PC1: {var_4d[0]*100:.2f}% | PC2: {var_4d[1]*100:.2f}% | PC3:"
    f" {var_4d[2]*100:.2f}%"
)
print(f"  --> TOTAL 3D Variance Preserved: {var_4d.sum()*100:.2f}%\n")

print(f"5D Model (X, Y, Z, Diameter, Volume):")
print(
    f"  PC1: {var_5d[0]*100:.2f}% | PC2: {var_5d[1]*100:.2f}% | PC3:"
    f" {var_5d[2]*100:.2f}%"
)
print(f"  --> TOTAL 3D Variance Preserved: {var_5d.sum()*100:.2f}%")
print("=" * 65)
print(
    f"Net Variance Lost by adding Diameter: -{(var_4d.sum() - var_5d.sum())*100:.2f}%"
)
print("=" * 65)