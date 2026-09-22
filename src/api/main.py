# src/api/main.py
"""FastAPI production entry point with CORS middleware and API routers."""

import sys
from pathlib import Path

# Inject project root into sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import clusters, findings, graph, health

app = FastAPI(
    title="Lung Insight API",
    description=(
        "Production backend serving 3D spatial coordinates, unsupervised"
        " clusters, and relational knowledge graphs from the LUNA16 benchmark."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development and future cloud web deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev and cloud preview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(health.router)
app.include_router(findings.router)
app.include_router(clusters.router)
app.include_router(graph.router)


@app.get("/", tags=["Root"])
def root():
  """Root endpoint providing quick navigation links."""
  return {
      "message": (
          "Welcome to Lung Insight API - Interactive AI Medical Pattern"
          " Explorer"
      ),
      "documentation": "/docs",
      "health_check": "/health",
      "findings_endpoint": "/api/v1/findings",
      "clusters_endpoint": "/api/v1/clusters/summary",
      "graph_endpoint": "/api/v1/graph",
  }