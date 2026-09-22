// frontend/js/cameraManager.js
import * as THREE from 'three';
import * as TWEEN from '@tweenjs/tween.js';

export class CameraManager {
  constructor(camera, controls) {
    this.camera = camera;
    this.controls = controls;
    this.defaultCamPos = new THREE.Vector3(0.0, 0.8, 5.2);
    this.defaultTarget = new THREE.Vector3(0, 0, 0);
  }

  /**
   * Smoothly animates the camera to focus on a finding or cluster target.
   */
  flyTo(targetPos, offset = new THREE.Vector3(0, 0.4, 1.4), duration = 1000) {
    const startCamPos = this.camera.position.clone();
    const endCamPos = targetPos.clone().add(offset);
    const startTarget = this.controls.target.clone();
    const endTarget = targetPos.clone();

    // Disable controls damping during active tween to avoid jitter
    this.controls.enabled = false;

    new TWEEN.Tween({ t: 0 })
      .to({ t: 1 }, duration)
      .easing(TWEEN.Easing.Cubic.Out)
      .onUpdate(({ t }) => {
        this.camera.position.lerpVectors(startCamPos, endCamPos, t);
        this.controls.target.lerpVectors(startTarget, endTarget, t);
      })
      .onComplete(() => {
        this.controls.target.copy(endTarget);
        this.controls.enabled = true;
      })
      .start();
  }

  /**
   * Resets camera back to global overview.
   */
  reset(duration = 1000) {
    const startCamPos = this.camera.position.clone();
    const startTarget = this.controls.target.clone();

    this.controls.enabled = false;

    new TWEEN.Tween({ t: 0 })
      .to({ t: 1 }, duration)
      .easing(TWEEN.Easing.Cubic.Out)
      .onUpdate(({ t }) => {
        this.camera.position.lerpVectors(startCamPos, this.defaultCamPos, t);
        this.controls.target.lerpVectors(startTarget, this.defaultTarget, t);
      })
      .onComplete(() => {
        this.controls.target.copy(this.defaultTarget);
        this.controls.enabled = true;
      })
      .start();
  }
}