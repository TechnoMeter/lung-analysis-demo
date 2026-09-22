// frontend/js/particles.js
import * as THREE from 'three';

export const CLUSTER_COLORS = {
  0: 0x38bdf8, // Right Lung: Sky Blue
  1: 0xf43f5e, // High-Volume Masses: Vivid Rose
  2: 0x818cf8, // Left Lung: Indigo
  3: 0xfbbf24  // Couch Shifts: Amber
};

function getVolumetricRadius(volumeMm3) {
  const cubeRoot = Math.cbrt(volumeMm3);
  return Math.max(0.045, Math.min(0.28, cubeRoot * 0.010));
}

export async function createFindingsMeshGroup(apiUrl = '/api/v1/findings?limit=1200') {
  const response = await fetch(apiUrl);
  if (!response.ok) throw new Error(`FastAPI responded with status: ${response.status}`);
  const data = await response.json();
  const findings = data.findings;

  const group = new THREE.Group();
  group.name = 'findings-group';

  const baseGeometry = new THREE.SphereGeometry(1, 24, 18);

  const findingMeshes = [];

  const MEDIAN_X = 0.0;
  const MEDIAN_Y = 10.0;
  const MEDIAN_Z = -195.0;

  for (const f of findings) {
    const radius = getVolumetricRadius(f.volume_mm3);
    const isOutlier = f.anomaly_score >= 0.50;

    // Unique material per mesh so each sphere can be dimmed/highlighted independently
    const material = new THREE.MeshStandardMaterial({
      color: isOutlier ? 0xff1744 : CLUSTER_COLORS[f.cluster_id],
      roughness: isOutlier ? 0.2 : 0.35,
      metalness: isOutlier ? 0.3 : 0.15,
      emissive: isOutlier ? 0x990022 : (f.cluster_id === 1 ? 0x5a0b1b : 0x000000),
      emissiveIntensity: isOutlier ? 0.45 : (f.cluster_id === 1 ? 0.25 : 0.0),
      transparent: true,
      opacity: 1.0
    });

    const mesh = new THREE.Mesh(baseGeometry, material);
    mesh.scale.set(radius, radius, radius);

    // Anatomical CT space
    const anatX = ((f.coord_x - MEDIAN_X) / 160.0) * 1.5;
    const anatY = ((f.coord_z - MEDIAN_Z) / 220.0) * 1.3;
    const anatZ = ((f.coord_y - MEDIAN_Y) / 160.0) * 1.4;

    // PCA latent space
    const pcaX = f.pca_x;
    const pcaY = f.pca_y;
    const pcaZ = f.pca_z;

    mesh.position.set(anatX, anatY, anatZ);

    mesh.userData = {
      finding_id: f.finding_id,
      seriesuid: f.seriesuid,
      diameter_mm: f.diameter_mm,
      volume_mm3: f.volume_mm3,
      cluster_id: f.cluster_id,
      anomaly_score: f.anomaly_score,
      coord_x: f.coord_x,
      coord_y: f.coord_y,
      coord_z: f.coord_z,
      anatPos: new THREE.Vector3(anatX, anatY, anatZ),
      pcaPos: new THREE.Vector3(pcaX, pcaY, pcaZ),
      targetPos: new THREE.Vector3(anatX, anatY, anatZ),
      originalScale: radius,
      baseMaterial: material
    };

    group.add(mesh);
    findingMeshes.push(mesh);
  }

  return { group, findingMeshes, total: findings.length };
}