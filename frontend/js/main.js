// frontend/js/main.js
import * as THREE from 'three';
import * as TWEEN from '@tweenjs/tween.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { createAnatomicalHulls } from './anatomicalHull.js';
import { createFindingsMeshGroup, CLUSTER_COLORS } from './particles.js';
import { CameraManager } from './cameraManager.js';

// DOM Mounts
const container = document.getElementById('viewport-container');
const loader = document.getElementById('loader');
const fpsDisplay = document.getElementById('metric-fps');
const activeFindingsDisplay = document.getElementById('metric-findings');
const hoverTooltip = document.getElementById('hover-tooltip');
const drawer = document.getElementById('inspection-drawer');

// Stop pointer/touch gestures on UI elements from reaching OrbitControls or Raycaster
const uiPanels = [
  '#cockpit-header',
  '#cluster-legend',
  '#viewport-controls',
  '#inspection-drawer',
  '#filter-toolbar'
];

uiPanels.forEach((selector) => {
  const el = document.querySelector(selector);
  if (el) {
    ['pointerdown', 'mousedown', 'touchstart', 'touchend', 'touchmove', 'wheel', 'click', 'dblclick'].forEach((event) => {
      el.addEventListener(event, (e) => e.stopPropagation(), { passive: false });
    });
  }
});

// 1. Scene & Camera
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070b14);
scene.fog = new THREE.FogExp2(0x070b14, 0.06);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0.0, 0.8, 5.2);

// 2. Renderer & Bloom
const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
container.appendChild(renderer.domElement);

const renderPass = new RenderPass(scene, camera);
const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  0.65, 0.3, 0.75
);
const composer = new EffectComposer(renderer);
composer.addPass(renderPass);
composer.addPass(bloomPass);

// 3. OrbitControls & Camera Manager
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.maxDistance = 12;
controls.minDistance = 0.8;
controls.target.set(0, 0, 0);

const cameraManager = new CameraManager(camera, controls);

// 4. Lighting Rig
scene.add(new THREE.AmbientLight(0xffffff, 0.25));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
keyLight.position.set(6, 8, 7);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0x38bdf8, 0.6);
fillLight.position.set(-6, -2, 4);
scene.add(fillLight);
const rimLight = new THREE.DirectionalLight(0x818cf8, 1.0);
rimLight.position.set(0, 5, -8);
scene.add(rimLight);

const grid = new THREE.GridHelper(10, 20, 0x1e293b, 0x0c1322);
grid.position.y = -2.2;
scene.add(grid);

// 5. Anatomical Hulls
const anatomicalHulls = createAnatomicalHulls();
scene.add(anatomicalHulls);

// 6. Data Ingestion
let findingsMeshes = [];
let currentMode = 'anat';
let hoveredMesh = null;
let selectedMesh = null;

createFindingsMeshGroup()
  .then(({ group, findingMeshes, total }) => {
    scene.add(group);
    findingsMeshes = findingMeshes;
    activeFindingsDisplay.textContent = total.toLocaleString();
    loader.classList.add('hidden');
  })
  .catch((err) => {
    console.error(err);
    loader.innerHTML = `<p style="color:#f43f5e;">Failed to connect to FastAPI on :8000.</p>`;
  });

// 7. Raycaster & Pointer Tracking
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

// 7. Raycaster & Pointer Tracking Guard
window.addEventListener('pointermove', (event) => {
  // If pointer is hovering over any UI container, don't cast into 3D scene
  if (event.target.closest('#cockpit-header, #cluster-legend, #viewport-controls, #inspection-drawer, #hover-tooltip')) {
    if (hoveredMesh && hoveredMesh !== selectedMesh) {
      hoveredMesh.scale.setScalar(hoveredMesh.userData.originalScale);
      hoveredMesh = null;
    }
    hoverTooltip.classList.add('hidden');
    container.style.cursor = 'default';
    return;
  }

  mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
  mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

  hoverTooltip.style.left = `${event.clientX}px`;
  hoverTooltip.style.top = `${event.clientY}px`;

  raycaster.setFromCamera(mouse, camera);

  const activeMeshes = findingsMeshes.filter(m => !m.userData.isFilteredOut);
  const intersects = raycaster.intersectObjects(activeMeshes);

  if (intersects.length > 0) {
    const mesh = intersects[0].object;
    if (hoveredMesh !== mesh) {
      if (hoveredMesh && hoveredMesh !== selectedMesh) {
        hoveredMesh.scale.setScalar(hoveredMesh.userData.originalScale);
      }
      hoveredMesh = mesh;
      hoveredMesh.scale.setScalar(mesh.userData.originalScale * 1.35);

      document.getElementById('tt-id').textContent = mesh.userData.finding_id;
      document.getElementById('tt-cluster').textContent = `Cluster ${mesh.userData.cluster_id}`;
      document.getElementById('tt-diameter').textContent = `${mesh.userData.diameter_mm.toFixed(1)} mm`;
      document.getElementById('tt-anomaly').textContent = mesh.userData.anomaly_score.toFixed(3);
      hoverTooltip.classList.remove('hidden');
      container.style.cursor = 'pointer';
    }
  } else {
    if (hoveredMesh && hoveredMesh !== selectedMesh) {
      hoveredMesh.scale.setScalar(hoveredMesh.userData.originalScale);
    }
    hoveredMesh = null;
    hoverTooltip.classList.add('hidden');
    container.style.cursor = 'default';
  }
});

// 8. Finding Click Selection & Drawer Trigger
window.addEventListener('click', () => {
  if (hoveredMesh) {
    selectFinding(hoveredMesh);
  }
});

function selectFinding(mesh) {
  selectedMesh = mesh;
  const data = mesh.userData;

  // Fly camera to focus on finding
  cameraManager.flyTo(mesh.position, new THREE.Vector3(0, 0.2, 0.8), 900);

  // Populate Slide-Out Drawer
  document.getElementById('dr-finding-id').textContent = data.finding_id;
  document.getElementById('dr-anomaly-score').textContent = data.anomaly_score.toFixed(3);
  document.getElementById('dr-progress-fill').style.width = `${Math.round(data.anomaly_score * 100)}%`;
  document.getElementById('dr-diameter').textContent = `${data.diameter_mm.toFixed(1)} mm`;
  document.getElementById('dr-volume').textContent = `${data.volume_mm3.toLocaleString(undefined, { maximumFractionDigits: 1 })} mm³`;
// Populate full 3-axis continuous scanner coordinates (mm)
  const formatCoord = (val) => (val >= 0 ? `+${val.toFixed(1)}` : val.toFixed(1));
  document.getElementById('dr-coords-xyz').textContent = 
    `${formatCoord(data.coord_x)}, ${formatCoord(data.coord_y)}, ${formatCoord(data.coord_z)} mm`;
  document.getElementById('dr-seriesuid').textContent = data.seriesuid;

  // Cluster label metadata
  const clusterNames = {
    0: 'Right Lung Typical',
    1: 'High-Volume Lesions',
    2: 'Left Lung Typical',
    3: 'Axial Couch Outliers'
  };
  document.getElementById('dr-cluster-label').textContent = `Cluster ${data.cluster_id} (${clusterNames[data.cluster_id]})`;

  // Status Card styling
  const statusCard = document.getElementById('dr-status-card');
  const statusTitle = document.getElementById('dr-status-title');
  const statusSub = document.getElementById('dr-status-sub');
  const thresholdTag = document.getElementById('dr-threshold-tag');

if (data.anomaly_score >= 0.40) {
    statusCard.className = 'status-card';
    statusTitle.textContent = 'High-Priority Geometric Outlier';
    statusSub.textContent = `Centroid deviation score: ${data.anomaly_score.toFixed(3)} (Top Outlier Tier)`;
  } else {
    statusCard.className = 'status-card typical';
    statusTitle.textContent = 'Typical Cohort Lesion';
    statusSub.textContent = `Centroid deviation score: ${data.anomaly_score.toFixed(3)} (Standard Baseline)`;
  }

  thresholdTag.textContent = data.diameter_mm >= 8.0 ? '≥8mm Fleischner High' : '<8mm Fleischner Low';
  thresholdTag.style.color = data.diameter_mm >= 8.0 ? '#f43f5e' : '#38bdf8';

  drawer.classList.remove('hidden');
}

// Drawer Close Handler
document.getElementById('btn-close-drawer').addEventListener('click', () => {
  drawer.classList.add('hidden');
  if (selectedMesh) {
    selectedMesh.scale.setScalar(selectedMesh.userData.originalScale);
    selectedMesh = null;
  }
});

// 9. Cohort Filter Toolbar Implementation
const filterButtons = document.querySelectorAll('.filter-btn');

filterButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    filterButtons.forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');

    const filter = btn.dataset.filter;
    applyFilter(filter);
  });
});

function applyFilter(filter) {
  let activeCount = 0;
  let targetCentroid = new THREE.Vector3(0, 0, 0);

  findingsMeshes.forEach((mesh) => {
    const data = mesh.userData;
    let match = false;

    if (filter === 'all') {
      match = true;
    } else if (filter === 'cluster-0' && data.cluster_id === 0) {
      match = true;
    } else if (filter === 'cluster-1' && data.cluster_id === 1) {
      match = true;
    } else if (filter === 'cluster-2' && data.cluster_id === 2) {
      match = true;
    } else if (filter === 'cluster-3' && data.cluster_id === 3) {
      match = true;
    } else if (filter === 'outliers' && data.anomaly_score >= 0.40) {
      match = true;
    }

    if (match) {
      mesh.material.opacity = 1.0;
      mesh.scale.setScalar(data.originalScale);
      mesh.userData.isFilteredOut = false; // Active for raycasting
      targetCentroid.add(mesh.position);
      activeCount++;
    } else {
      mesh.material.opacity = 0.06;
      mesh.scale.setScalar(data.originalScale * 0.7);
      mesh.userData.isFilteredOut = true;  // Ignore in raycasting
    }
  });

  activeFindingsDisplay.textContent = activeCount.toLocaleString();

// If a specific cluster or outlier subset was selected, fly camera to its centroid
  if (filter !== 'all' && activeCount > 0) {
    targetCentroid.divideScalar(activeCount);

    // If filtering outliers, bias Y upward slightly to focus on thoracic masses rather than floor table offsets
    if (filter === 'outliers') {
      targetCentroid.y += 0.30;
      cameraManager.flyTo(targetCentroid, new THREE.Vector3(0, 0.1, 2.2), 1000);
    } else {
      cameraManager.flyTo(targetCentroid, new THREE.Vector3(0, 0.2, 2.0), 1000);
    }
  } else if (filter === 'all') {
    cameraManager.reset(900);
  }
}

// 10. Cluster Legend Click Zoom
document.querySelectorAll('.legend-item').forEach((item) => {
  item.addEventListener('click', () => {
    const cId = parseInt(item.dataset.cluster, 10);
    const filterBtn = document.querySelector(`.filter-btn[data-filter="cluster-${cId}"]`);
    if (filterBtn) filterBtn.click();
  });
});

// 11. Coordinate Projection Toggle
const btnModeAnat = document.getElementById('btn-mode-anat');
const btnModePca = document.getElementById('btn-mode-pca');

function setCoordinateMode(mode) {
  currentMode = mode;
  btnModeAnat.classList.toggle('active', mode === 'anat');
  btnModePca.classList.toggle('active', mode === 'pca');

  findingsMeshes.forEach((mesh) => {
    mesh.userData.targetPos = mode === 'anat' ? mesh.userData.anatPos : mesh.userData.pcaPos;
  });

  anatomicalHulls.visible = (mode === 'anat');
}

btnModeAnat.addEventListener('click', () => setCoordinateMode('anat'));
btnModePca.addEventListener('click', () => setCoordinateMode('pca'));

// Toolbar Handlers
document.getElementById('btn-reset-cam').addEventListener('click', () => {
  cameraManager.reset(800);
});

const toggleHullsBtn = document.getElementById('btn-toggle-hulls');
toggleHullsBtn.addEventListener('click', () => {
  anatomicalHulls.visible = !anatomicalHulls.visible;
  toggleHullsBtn.classList.toggle('active', anatomicalHulls.visible);
});

let bloomActive = true;
const toggleGlowBtn = document.getElementById('btn-toggle-glow');
toggleGlowBtn.addEventListener('click', () => {
  bloomActive = !bloomActive;
  bloomPass.enabled = bloomActive;
  toggleGlowBtn.classList.toggle('active', bloomActive);
});

// Resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
});

// 12. 60 FPS Render Loop with TWEEN Updates
let lastTime = performance.now();
let frames = 0;

function animate(time) {
  requestAnimationFrame(animate);

  TWEEN.update();
  controls.update();

  // Smooth lerp when toggling coordinate modes
  for (let i = 0; i < findingsMeshes.length; i++) {
    const mesh = findingsMeshes[i];
    if (mesh.userData.targetPos) {
      mesh.position.lerp(mesh.userData.targetPos, 0.08);
    }
  }

  composer.render();

  frames++;
  if (time >= lastTime + 1000) {
    fpsDisplay.textContent = Math.round((frames * 1000) / (time - lastTime));
    frames = 0;
    lastTime = time;
  }
}

requestAnimationFrame(animate);