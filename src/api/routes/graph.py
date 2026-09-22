# src/api/routes/graph.py
"""Relational graph transformation delivering node-edge networks for vis.js."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.api.schemas import GraphEdge, GraphNode, GraphResponse
from src.database.connection import get_db
from src.database.models import Finding, Study

router = APIRouter(prefix="/api/v1/graph", tags=["Knowledge Graph"])


@router.get(
    "",
    response_model=GraphResponse,
    summary="Generate vis.js Relational Graph Payload",
)
def get_study_graph(
    seriesuid: Optional[str] = Query(
        None,
        description="Target CT study UID. Defaults to study with highest finding count.",
    ),
    db: Session = Depends(get_db),
):
  """Builds a 2D knowledge graph structure: Study -> Findings -> Clusters and Metrics.

  Output schema matches the vis.js DataSet format directly.
  """
  # Fallback to the study with the most findings for demonstration if unspecified
  if not seriesuid:
    target_study = (
        db.query(Study).order_by(Study.finding_count.desc()).first()
    )
    if not target_study:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="No studies found in database.",
      )
    seriesuid = target_study.seriesuid
  else:
    target_study = (
        db.query(Study).filter(Study.seriesuid == seriesuid).first()
    )
    if not target_study:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Study '{seriesuid}' not found.",
      )

  findings = db.query(Finding).filter(Finding.seriesuid == seriesuid).all()

  nodes = []
  edges = []

  # 1. Root Parent Study Node
  nodes.append(
      GraphNode(
          id=seriesuid,
          label=f"CT Study\n({len(findings)} findings)",
          group="study",
          title=f"Series UID: {seriesuid}<br>Findings: {len(findings)}",
      )
  )

  # Track unique cluster nodes to avoid duplicates
  cluster_nodes_added = set()

  for f in findings:
    # 2. Child Finding Node
    f_node_id = f.finding_id
    nodes.append(
        GraphNode(
            id=f_node_id,
            label=f"{f.finding_id}\n{f.diameter_mm:.1f} mm",
            group="finding",
            value=f.diameter_mm,
            title=(
                f"<b>{f.finding_id}</b><br>Volume: {f.volume_mm3:.1f}"
                f" mm³<br>Anomaly Score: {f.anomaly_score:.3f}"
            ),
        )
    )

    # Edge: Study -> Finding
    edges.append(
        GraphEdge(
            **{
                "from": seriesuid,
                "to": f_node_id,
                "label": "contains",
            }
        )
    )

    # 3. Cluster Group Node
    c_node_id = f"cluster_{f.cluster_id}"
    if c_node_id not in cluster_nodes_added:
      nodes.append(
          GraphNode(
              id=c_node_id,
              label=f"Cluster {f.cluster_id}",
              group="cluster",
              title=f"K-Means Cluster {f.cluster_id}",
          )
      )
      cluster_nodes_added.add(c_node_id)

    # Edge: Finding -> Cluster
    edges.append(
        GraphEdge(
            **{
                "from": f_node_id,
                "to": c_node_id,
                "label": "assigned_to",
            }
        )
    )

    # 4. Outlier Flag Node (if high anomaly)
    if f.anomaly_score >= 0.20:
      anomaly_node_id = f"outlier_{f.finding_id}"
      nodes.append(
          GraphNode(
              id=anomaly_node_id,
              label=f"Outlier\n({f.anomaly_score:.2f})",
              group="metric",
              title=(
                  f"Centroid Distance Score: {f.anomaly_score:.4f} (High"
                  " Priority)"
              ),
          )
      )
      edges.append(
          GraphEdge(
              **{
                  "from": f_node_id,
                  "to": anomaly_node_id,
                  "label": "surfaced_as",
              }
          )
      )

  return GraphResponse(
      seriesuid=seriesuid,
      finding_count=len(findings),
      nodes=nodes,
      edges=edges,
  )