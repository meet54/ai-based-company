/**
 * Three.js 3D virtual office — humanoid characters and themed rooms.
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const FLOOR_W = 24;
const FLOOR_D = 18;
const OFFICE_CENTER = new THREE.Vector3(12, 0, 9);

function hashColor(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = ((h << 5) - h) + name.charCodeAt(i) | 0;
  const hue = Math.abs(h) % 360;
  return new THREE.Color(`hsl(${hue}, 55%, 52%)`);
}

function pctToWorld(x, y) {
  return { x: (x / 100) * FLOOR_W, z: (y / 100) * FLOOR_D };
}

export class Office3DScene {
  constructor(mountEl) {
    this.mount = mountEl;
    this.characters = new Map();
    this.clock = new THREE.Clock();
    this._targetVec = new THREE.Vector3();

    const parent = mountEl.parentElement;
    const w = Math.max(mountEl.clientWidth, parent?.clientWidth || 0, 640);
    const h = Math.max(mountEl.clientHeight, parent?.clientHeight || 0, 420);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0a0e14);
    this.scene.fog = new THREE.Fog(0x0a0e14, 28, 55);

    const aspect = Math.max(w / h, 0.5);
    this.camera = new THREE.PerspectiveCamera(42, aspect, 0.1, 120);
    this.camera.position.set(12, 16, 22);
    this.camera.lookAt(OFFICE_CENTER);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(w, h);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    mountEl.appendChild(this.renderer.domElement);
    this.renderer.domElement.className = 'office-3d-canvas';

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.copy(OFFICE_CENTER);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.enablePan = true;
    this.controls.panSpeed = 0.7;
    this.controls.rotateSpeed = 0.55;
    this.controls.zoomSpeed = 1.1;
    this.controls.minDistance = 7;
    this.controls.maxDistance = 42;
    this.controls.maxPolarAngle = Math.PI / 2.15;
    this.controls.minPolarAngle = 0.2;
    this.controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.DOLLY,
      RIGHT: THREE.MOUSE.PAN,
    };
    this.controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };
    this.controls.update();

    this._defaultCamera = {
      position: this.camera.position.clone(),
      target: OFFICE_CENTER.clone(),
    };

    this.labelRenderer = new CSS2DRenderer();
    this.labelRenderer.setSize(w, h);
    this.labelRenderer.domElement.className = 'office-3d-labels';
    mountEl.appendChild(this.labelRenderer.domElement);

    this._lights();
    this._buildFloor();
    this._buildRooms();
    this._bindResize();
    this._bindCameraUI(mountEl);
    this._animate = this._animate.bind(this);
    this._onResize();
    requestAnimationFrame(this._animate);
    this.renderer.render(this.scene, this.camera);
    this.labelRenderer.render(this.scene, this.camera);
  }

  _lights() {
    this.scene.add(new THREE.AmbientLight(0x8aa4c8, 0.45));
    const sun = new THREE.DirectionalLight(0xffffff, 0.85);
    sun.position.set(10, 22, 8);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -20;
    sun.shadow.camera.right = 20;
    sun.shadow.camera.top = 20;
    sun.shadow.camera.bottom = -20;
    this.scene.add(sun);
    const fill = new THREE.PointLight(0x4fd1c5, 0.35, 40);
    fill.position.set(4, 8, 14);
    this.scene.add(fill);
  }

  _floorMat(color, emissive = 0x000000) {
    return new THREE.MeshStandardMaterial({
      color,
      emissive,
      roughness: 0.82,
      metalness: 0.08,
    });
  }

  _box(w, h, d, mat, x, y, z) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    m.castShadow = true;
    m.receiveShadow = true;
    this.scene.add(m);
    return m;
  }

  _buildFloor() {
    const base = new THREE.Mesh(
      new THREE.PlaneGeometry(FLOOR_W, FLOOR_D),
      this._floorMat(0x141c28),
    );
    base.rotation.x = -Math.PI / 2;
    base.position.set(FLOOR_W / 2, 0, FLOOR_D / 2);
    base.receiveShadow = true;
    this.scene.add(base);

    const grid = new THREE.GridHelper(FLOOR_W, 24, 0x2a3a52, 0x1a2436);
    grid.position.set(FLOOR_W / 2, 0.02, FLOOR_D / 2);
    this.scene.add(grid);
  }

  _roomWalls(x, z, w, d, wallColor, floorColor) {
    const mat = this._floorMat(wallColor);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(w, d), this._floorMat(floorColor));
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(x + w / 2, 0.03, z + d / 2);
    floor.receiveShadow = true;
    this.scene.add(floor);

    const h = 0.9;
    this._box(w, h, 0.08, mat, x + w / 2, h / 2, z);
    this._box(w, h, 0.08, mat, x + w / 2, h / 2, z + d);
    this._box(0.08, h, d, mat, x, h / 2, z + d / 2);
    if (x + w < FLOOR_W - 0.5) {
      this._box(0.08, h, d, mat, x + w, h / 2, z + d / 2);
    }
  }

  _roomLabel(text, x, z) {
    const el = document.createElement('div');
    el.className = 'office-3d-room-label';
    el.textContent = text;
    const label = new CSS2DObject(el);
    label.position.set(x, 1.8, z);
    this.scene.add(label);
  }

  _buildRooms() {
    // Dev floor (desks) — left
    this._roomWalls(0.3, 0.3, 13.2, 10.5, 0x243044, 0x1a2436);
    this._roomLabel('💻 Dev Floor', 6.5, 1.2);

    // Coffee break room — top right
    this._roomWalls(13.8, 0.3, 9.8, 7.5, 0x3d2e1e, 0x2a2018);
    this._roomLabel('☕ Coffee Break Room', 18.5, 1.2);
    this._coffeeProps(14.5, 2.5);
    this._coffeeProps(17.5, 4.5);
    this._coffeeProps(20.5, 2.8);

    // Phone / call room — bottom right
    this._roomWalls(13.8, 8.2, 9.8, 9.2, 0x1e2a3d, 0x151f2e);
    this._roomLabel('📞 Call Room', 18.5, 9.2);
    this._phoneBooth(15.2, 10);
    this._phoneBooth(17.8, 12.5);
    this._phoneBooth(20.5, 10.5);
    this._phoneBooth(18, 14.5);

    // Chill / games room — bottom left
    this._roomWalls(0.3, 8.2, 13.2, 9.2, 0x2a1e3d, 0x1e1528);
    this._roomLabel('🎮 Chill & Games Room', 6.5, 9.2);
    this._gameTable(4, 11);
    this._gameTable(8.5, 13);
    this._sofa(10, 10.5);
  }

  _coffeeProps(x, z) {
    this._box(0.9, 0.85, 0.5, this._floorMat(0x4a3728), x, 0.42, z);
    this._box(0.25, 0.5, 0.25, this._floorMat(0x8899aa), x + 0.35, 0.95, z);
  }

  _phoneBooth(x, z) {
    this._box(1.4, 1.6, 1.4, this._floorMat(0x2a3a55), x, 0.8, z);
    this._box(0.5, 0.08, 0.5, this._floorMat(0x334155), x, 0.5, z);
  }

  _gameTable(x, z) {
    this._box(2.2, 0.12, 1.2, this._floorMat(0x3d2a5c), x, 0.55, z);
    this._box(0.15, 0.5, 0.15, this._floorMat(0x2a3548), x - 0.8, 0.3, z - 0.4);
    this._box(0.15, 0.5, 0.15, this._floorMat(0x2a3548), x + 0.8, 0.3, z - 0.4);
  }

  _sofa(x, z) {
    this._box(2.4, 0.45, 0.9, this._floorMat(0x4a3060), x, 0.32, z);
  }

  buildDesks(desks) {
    if (this._desksBuilt) return;
    this._desksBuilt = true;
    desks.forEach((d) => {
      const p = pctToWorld(d.x, d.y);
      this._box(0.9, 0.06, 0.55, this._floorMat(0x3d4f6a), p.x, 0.55, p.z + 0.2);
      this._box(0.35, 0.35, 0.35, this._floorMat(0x1e293b), p.x, 0.28, p.z - 0.15);
    });
  }

  _createHumanoid(name) {
    const color = hashColor(name);
    const skin = new THREE.Color(0xf0c8a8);
    const group = new THREE.Group();

    const bodyMat = new THREE.MeshStandardMaterial({ color, roughness: 0.7 });
    const skinMat = new THREE.MeshStandardMaterial({ color: skin, roughness: 0.8 });
    const legMat = new THREE.MeshStandardMaterial({ color: 0x2a3548, roughness: 0.8 });

    const torso = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.24, 0.55, 10), bodyMat);
    torso.position.y = 0.95;
    torso.castShadow = true;

    const head = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 16), skinMat);
    head.position.y = 1.42;
    head.castShadow = true;

    const legGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.4, 8);
    const legL = new THREE.Mesh(legGeo, legMat);
    legL.position.set(-0.12, 0.38, 0);
    const legR = legL.clone();
    legR.position.x = 0.12;

    const armGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.3, 8);
    const armL = new THREE.Mesh(armGeo, skinMat);
    armL.position.set(-0.3, 1.02, 0);
    armL.rotation.z = 0.25;
    const armR = armL.clone();
    armR.position.x = 0.3;
    armR.rotation.z = -0.25;

    group.add(torso, head, legL, legR, armL, armR);
    group.userData.parts = { head, armL, armR };

    const labelEl = document.createElement('div');
    labelEl.className = 'office-3d-agent-label';
    labelEl.innerHTML = '<strong></strong><span class="act"></span><span class="hrs"></span>';
    const label = new CSS2DObject(labelEl);
    label.position.set(0, 1.85, 0);
    group.add(label);

    group.userData.labelEl = labelEl;
    return group;
  }

  upsertCharacter(id, member) {
    let entry = this.characters.get(id);
    if (!entry) {
      const mesh = this._createHumanoid(id);
      mesh.position.set(1, 0, 1);
      this.scene.add(mesh);
      entry = {
        mesh,
        target: new THREE.Vector3(1, 0, 1),
        state: 'idle',
        anim: 0,
      };
      this.characters.set(id, entry);
    }
    return entry;
  }

  moveCharacter(id, xPct, yPct, state) {
    const entry = this.characters.get(id);
    if (!entry) return;
    const world = pctToWorld(xPct, yPct);
    entry.target.set(world.x, 0, world.z);
    entry.state = state;
    entry.mesh.userData.labelEl.className = `office-3d-agent-label state-${state}`;
  }

  updateCharacter(id, member, progress, activity, hoursText) {
    const entry = this.characters.get(id);
    if (!entry) return;
    const el = entry.mesh.userData.labelEl;
    const first = (member.name || '').split(' ')[0];
    el.querySelector('strong').textContent = first;
    el.querySelector('.act').textContent = activity?.task || member.current_task || '';
    el.querySelector('.hrs').textContent = hoursText || '';
    const fill = progress?.pct ?? 0;
    el.style.setProperty('--prog', `${fill}%`);
  }

  setCharacterVisible(id, visible) {
    const entry = this.characters.get(id);
    if (entry) entry.mesh.visible = visible;
  }

  removeCharacter(id) {
    const entry = this.characters.get(id);
    if (!entry) return;
    this.scene.remove(entry.mesh);
    this.characters.delete(id);
  }

  _animateCharacter(entry, dt) {
    const { mesh, target, state } = entry;
    entry.anim += dt;
    mesh.position.lerp(target, Math.min(1, dt * 2.2));

    const parts = mesh.userData.parts;
    const bob = Math.sin(entry.anim * 3) * 0.02;
    mesh.position.y = bob;

    if (state === 'working') {
      parts.armL.rotation.x = Math.sin(entry.anim * 8) * 0.35;
      parts.armR.rotation.x = -Math.sin(entry.anim * 8) * 0.35;
      parts.head.rotation.x = 0.15;
    } else if (state === 'coffee') {
      parts.armR.rotation.x = -0.8;
      parts.armR.rotation.z = -0.4;
    } else if (state === 'phone') {
      parts.armR.rotation.x = -1.2;
      parts.head.rotation.z = 0.1;
    } else if (state === 'gaming') {
      parts.armL.rotation.x = -0.5;
      parts.armR.rotation.x = -0.5;
    } else if (state === 'talking') {
      parts.armR.rotation.z = -0.5;
      parts.head.rotation.y = Math.sin(entry.anim * 2) * 0.15;
    } else {
      parts.armL.rotation.x = 0;
      parts.armR.rotation.x = 0;
      parts.head.rotation.set(0, 0, 0);
    }
  }

  _bindCameraUI(mountEl) {
    const hint = document.createElement('div');
    hint.className = 'office-3d-camera-hint';
    hint.innerHTML = '🖱️ Drag to rotate · Scroll to zoom · Right-drag to pan';
    mountEl.appendChild(hint);

    const resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'office-3d-reset-camera';
    resetBtn.textContent = '↺ Reset view';
    resetBtn.addEventListener('click', () => this.resetCamera());
    mountEl.appendChild(resetBtn);
  }

  resetCamera() {
    this.camera.position.copy(this._defaultCamera.position);
    this.controls.target.copy(this._defaultCamera.target);
    this.controls.update();
  }

  _animate() {
    requestAnimationFrame(this._animate);
    const dt = this.clock.getDelta();
    this.controls.update();
    this.characters.forEach((entry) => this._animateCharacter(entry, dt));
    this.renderer.render(this.scene, this.camera);
    this.labelRenderer.render(this.scene, this.camera);
  }

  _onResize() {
    if (!this.mount) return;
    const parent = this.mount.parentElement;
    const w = Math.max(this.mount.clientWidth, parent?.clientWidth || 0, 640);
    const h = Math.max(this.mount.clientHeight, parent?.clientHeight || 0, 420);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.labelRenderer.setSize(w, h);
  }

  _bindResize() {
    this._onResize = this._onResize.bind(this);
    window.addEventListener('resize', this._onResize);
  }

  dispose() {
    window.removeEventListener('resize', this._onResize);
    this.controls?.dispose();
    this.characters.clear();
    this.renderer.dispose();
    this.mount.innerHTML = '';
  }
}
