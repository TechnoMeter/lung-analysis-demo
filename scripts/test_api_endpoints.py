# scripts/test_api_endpoints.py
"""Automated verification script for Lung Insight FastAPI endpoints."""

import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000"

endpoints = [
    ("/health", "Health Diagnostic"),
    ("/api/v1/clusters/summary", "Cluster Summaries"),
    ("/api/v1/findings?limit=3", "Spatial Findings Sample"),
    ("/api/v1/graph", "Knowledge Graph Payload"),
]

print("=" * 65)
print("FASTAPI LIVE ENDPOINT AUDIT")
print("=" * 65)

for path, label in endpoints:
  url = f"{BASE_URL}{path}"
  try:
    req = urllib.request.Request(url, headers={"User-Agent": "SmokeTest/1.0"})
    with urllib.request.urlopen(req) as response:
      status_code = response.getcode()
      raw_data = response.read().decode("utf-8")
      data = json.loads(raw_data)

      print(f"[PASS] {status_code} OK -> {label} ({path})")

      if path == "/health":
        print(
            f"       Status: {data.get('status')} | DB:"
            f" {data.get('database')} | Studies: {data.get('total_studies')} |"
            f" Findings: {data.get('total_findings')}"
        )
      elif path == "/api/v1/clusters/summary":
        print(f"       Clusters Returned: {len(data.get('clusters', []))}")
        for c in data.get("clusters", []):
          print(
              f"         * Cluster {c['cluster_id']}: {c['label']} (n="
              f" {c['finding_count']}, {c['percentage']}%)"
          )
      elif "findings" in path:
        print(
            f"       Total in DB: {data.get('total')} | Sampled:"
            f" {data.get('count')}"
        )
        sample = data.get("findings", [])[0]
        print(
            f"         * First Finding: [{sample['finding_id']}] 3D PCA: ("
            f"{sample['pca_x']}, {sample['pca_y']}, {sample['pca_z']})"
        )
      elif path == "/api/v1/graph":
        print(
            f"       Study UID: {data.get('seriesuid')[:20]}... | Nodes:"
            f" {len(data.get('nodes', []))} | Edges:"
            f" {len(data.get('edges', []))}"
        )

  except Exception as e:
    print(f"[FAIL] Error testing {label} ({path}): {e}")

print("=" * 65)