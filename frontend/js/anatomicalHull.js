// frontend/js/anatomicalHull.js
import * as THREE from 'three';

export function createAnatomicalHulls() {
  const hullGroup = new THREE.Group();
  hullGroup.name = 'anatomical-hulls';

  const lobeGeometry = new THREE.SphereGeometry(1.4, 32, 24);

  // Soft material that does not compete with the findings
  const hullMaterial = new THREE.MeshPhysicalMaterial({
    color: 0x38bdf8,
    transparent: true,
    opacity: 0.05,
    roughness: 0.1,
    transmission: 0.9,
    depthWrite: false,
    wireframe: false
  });

  // Very delicate wireframe overlay
  const subtleWireMaterial = new THREE.MeshBasicMaterial({
    color: 0x38bdf8,
    wireframe: true,
    transparent: true,
    opacity: 0.04
  });

  // 1. Right Lung Pleural Cavity (Centered around Y = 0)
  const rightLobe = new THREE.Mesh(lobeGeometry, hullMaterial);
  rightLobe.scale.set(0.95, 1.85, 0.9);
  rightLobe.position.set(-1.05, 0.05, 0.0);
  rightLobe.rotation.z = 0.05;

  const rightWire = new THREE.Mesh(lobeGeometry, subtleWireMaterial);
  rightWire.scale.copy(rightLobe.scale);
  rightWire.position.copy(rightLobe.position);
  rightWire.rotation.copy(rightLobe.rotation);

  // 2. Left Lung Pleural Cavity (Centered around Y = 0)
  const leftLobe = new THREE.Mesh(lobeGeometry, hullMaterial);
  leftLobe.scale.set(0.90, 1.80, 0.85);
  leftLobe.position.set(1.05, 0.05, 0.0);
  leftLobe.rotation.z = -0.05;

  const leftWire = new THREE.Mesh(lobeGeometry, subtleWireMaterial);
  leftWire.scale.copy(leftLobe.scale);
  leftWire.position.copy(leftLobe.position);
  leftWire.rotation.copy(leftLobe.rotation);

  hullGroup.add(rightLobe, rightWire, leftLobe, leftWire);
  return hullGroup;
}