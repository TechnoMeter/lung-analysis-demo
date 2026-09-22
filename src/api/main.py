# src/api/main.py
"""FastAPI production entry point with CORS middleware, API routers, and Static SPA mount."""

from pathlib import Path
import sys

# Inject project root into sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
  sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers
app.include_router(health.router)
app.include_router(findings.router)
app.include_router(clusters.router)
app.include_router(graph.router)

# Mount Frontend Static Assets
frontend_dir = PROJECT_ROOT / "frontend"
if frontend_dir.exists():
  app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="static")