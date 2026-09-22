# src/api/schemas.py
"""Pydantic v2 schemas defining input validation and serialization contracts."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------------------
# Finding Schemas
# -----------------------------------------------------------------------------
class FindingBase(BaseModel):
  """Core attributes of a nodule finding."""

  finding_id: str
  seriesuid: str
  coord_x: float
  coord_y: float
  coord_z: float
  diameter_mm: float
  volume_mm3: float
  cluster_id: int
  anomaly_score: float
  pca_x: float
  pca_y: float
  pca_z: float


class FindingResponse(FindingBase):
  """Finding serialization schema mapped directly from SQLAlchemy models."""

  created_at: datetime

  model_config = ConfigDict(from_attributes=True)


class FindingListResponse(BaseModel):
  """Envelope response for collection queries and 3D point cloud loading."""

  total: int
  count: int
  findings: List[FindingResponse]


# -----------------------------------------------------------------------------
# Cluster Summary Schemas
# -----------------------------------------------------------------------------
class ClusterProfile(BaseModel):
  """Aggregated statistics for a single unsupervised cluster."""

  cluster_id: int
  label: str
  description: str
  finding_count: int
  percentage: float
  mean_diameter_mm: float
  mean_volume_mm3: float
  mean_anomaly_score: float
  mean_coord_x: float
  mean_coord_y: float
  mean_coord_z: float


class ClusterSummaryResponse(BaseModel):
  """Envelope containing profiles for all discovered cohorts."""

  total_findings: int
  clusters: List[ClusterProfile]


# -----------------------------------------------------------------------------
# Knowledge Graph Schemas (vis.js contract)
# -----------------------------------------------------------------------------
class GraphNode(BaseModel):
  """vis.js node representation."""

  id: str
  label: str
  group: str = Field(
      ..., description="Category: study, finding, cluster, or metric"
  )
  title: Optional[str] = Field(
      None, description="HTML tooltip content on hover"
  )
  value: Optional[float] = Field(
      None, description="Node size scaler (e.g. diameter or anomaly)"
  )


class GraphEdge(BaseModel):
  """vis.js directed edge representation."""

  source: str = Field(..., alias="from")
  target: str = Field(..., alias="to")
  label: Optional[str] = None

  model_config = ConfigDict(populate_by_name=True)


class GraphResponse(BaseModel):
  """Complete node-edge network payload for vis.js rendering."""

  seriesuid: str
  finding_count: int
  nodes: List[GraphNode]
  edges: List[GraphEdge]


# -----------------------------------------------------------------------------
# Health Check Schema
# -----------------------------------------------------------------------------
class HealthResponse(BaseModel):
  """System diagnostic and database connectivity status."""

  status: str
  database: str
  total_studies: int
  total_findings: int
  timestamp: datetime