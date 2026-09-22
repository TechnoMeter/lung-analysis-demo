# src/database/models.py
"""SQLAlchemy ORM models defining Study and Finding entities."""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from src.database.connection import Base


class Study(Base):
  """Parent entity representing a distinct DICOM CT acquisition session."""

  __tablename__ = "studies"

  seriesuid = Column(String(128), primary_key=True, index=True)
  finding_count = Column(Integer, nullable=False, default=0)
  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  # 1:N relationship with cascade deletion
  findings = relationship(
    "Finding", back_populates="study", cascade="all, delete-orphan"
  )

  def __repr__(self) -> str:
    return (
      f"<Study(seriesuid='{self.seriesuid}', findings={self.finding_count})>"
    )


class Finding(Base):
  """Child entity representing an enriched pulmonary nodule observation."""

  __tablename__ = "findings"

  # Surrogate Primary Key
  finding_id = Column(String(16), primary_key=True, index=True)

  # Foreign Key to Study
  seriesuid = Column(
    String(128),
    ForeignKey("studies.seriesuid", ondelete="CASCADE"),
    nullable=False,
    index=True,
  )

  # Physical Continuous Coordinates (mm)
  coord_x = Column(Float, nullable=False)
  coord_y = Column(Float, nullable=False)
  coord_z = Column(Float, nullable=False)

  # Clinical Morphology
  diameter_mm = Column(Float, nullable=False)
  volume_mm3 = Column(Float, nullable=False)

  # Unsupervised Latent Metrics
  cluster_id = Column(Integer, nullable=False, index=True)
  anomaly_score = Column(Float, nullable=False, index=True)

  # 3D PCA WebGL Coordinates
  pca_x = Column(Float, nullable=False)
  pca_y = Column(Float, nullable=False)
  pca_z = Column(Float, nullable=False)

  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  # Relationship back to Parent Study
  study = relationship("Study", back_populates="findings")

  def __repr__(self) -> str:
    return (
      f"<Finding(id='{self.finding_id}', cluster={self.cluster_id}, d={self.diameter_mm}mm)>"
    )