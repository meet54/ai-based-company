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
    this._animatedProps = [];

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

    this._followId = null;
    this._followHints = {};
    this._raycaster = new THREE.Raycaster();
    this._pointer = new THREE.Vector2();
    this._povLooks = {
      console: new THREE.Vector3(10.5, 1.25, 9.7),
      chess: new THREE.Vector3(2.8, 0.72, 10.5),
      pool: new THREE.Vector3(4.5, 0.88, 15.2),
      pingpong: new THREE.Vector3(7.5, 0.88, 13.5),
      coffee: new THREE.Vector3(18.5, 1.05, 3.2),
    };

    this.controls.addEventListener('start', () => {
      if (this._justFocusedPov) return;
      if (this._followId) {
        this._followId = null;
        this._clearPovLabels();
        this.onPovExit?.();
      }
    });

    this.labelRenderer = new CSS2DRenderer();
    this.labelRenderer.setSize(w, h);
    this.labelRenderer.domElement.className = 'office-3d-labels';
    mountEl.appendChild(this.labelRenderer.domElement);

    this._lights();
    this._buildFloor();
    this._buildRooms();
    this._bindResize();
    this._bindCameraUI(mountEl);
    this._bindCharacterPicks();
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

  _mat(color, emissive = 0x000000, metalness = 0.08, roughness = 0.82) {
    return new THREE.MeshStandardMaterial({
      color,
      emissive,
      roughness,
      metalness,
    });
  }

  _floorMat(color, emissive = 0x000000) {
    return this._mat(color, emissive);
  }

  _group(...meshes) {
    const g = new THREE.Group();
    meshes.forEach((m) => g.add(m));
    g.traverse((c) => {
      if (c.isMesh) {
        c.castShadow = true;
        c.receiveShadow = true;
      }
    });
    this.scene.add(g);
    return g;
  }

  _mesh(geo, mat) {
    const m = new THREE.Mesh(geo, mat);
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
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

  _steamMaterial() {
    return new THREE.MeshStandardMaterial({
      color: 0xffffff,
      emissive: 0xdddddd,
      emissiveIntensity: 0.6,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
      roughness: 1,
      metalness: 0,
    });
  }

  _addSteam(x, z, baseY = 1.62) {
    const offsets = [
      { dx: 0, dz: 0, phase: x },
      { dx: 0.08, dz: -0.05, phase: x + 1.2 },
      { dx: -0.06, dz: 0.07, phase: x + 2.4 },
    ];
    const meshes = [];
    offsets.forEach((o) => {
      const steam = this._mesh(new THREE.SphereGeometry(0.055, 8, 8), this._steamMaterial());
      steam.position.set(x - 0.55 + o.dx, baseY, z + o.dz);
      this._animatedProps.push({
        mesh: steam,
        type: 'steam',
        baseX: x - 0.55 + o.dx,
        baseZ: z + o.dz,
        baseY,
        phase: o.phase,
        rise: 0,
      });
      meshes.push(steam);
    });
    return meshes;
  }

  _addGlowLight(x, y, z, color, intensity = 0.35) {
    const light = new THREE.PointLight(color, intensity, 2.8);
    light.position.set(x, y, z);
    this.scene.add(light);
    return light;
  }

  _buildRooms() {
    // Dev floor (desks) — left
    this._roomWalls(0.3, 0.3, 13.2, 10.5, 0x243044, 0x1a2436);
    this._roomLabel('💻 Dev Floor', 6.5, 1.2);

    // Coffee break room — top right
    this._roomWalls(13.8, 0.3, 9.8, 7.5, 0x3d2e1e, 0x2a2018);
    this._roomLabel('☕ Coffee Break Room', 18.5, 1.2);
    this._coffeeBar(15.2, 2.2);
    this._coffeeBar(19.8, 4.8);
    this._coffeeSeating(17, 6.2);

    // Phone / call room — bottom right
    this._roomWalls(13.8, 8.2, 9.8, 9.2, 0x1e2a3d, 0x151f2e);
    this._roomLabel('📞 Call Room', 18.5, 9.2);
    this._callBooth(15, 9.8);
    this._callBooth(18.2, 12.2);
    this._callBooth(21, 10.2);
    this._callBooth(17, 14.8);

    // Chill / games room — bottom left
    this._roomWalls(0.3, 8.2, 13.2, 9.2, 0x2a1e3d, 0x1e1528);
    this._roomLabel('🎮 Chill & Games Room', 6.5, 9.2);
    this._chessTable(2.8, 10.5);
    this._pingPongTable(7.5, 13.5);
    this._gamingStation(10.5, 9.8);
    this._poolTable(4.5, 15.2);
    this._sofa(11.5, 11.8);
  }

  _coffeeBar(x, z) {
    const wood = this._mat(0x5c4033);
    const steel = this._mat(0x9aa8b8, 0x000000, 0.55, 0.35);
    const dark = this._mat(0x2a1810);

    const counter = this._mesh(new THREE.BoxGeometry(2.4, 0.9, 0.7), wood);
    counter.position.set(x, 0.45, z);

    const machine = this._mesh(new THREE.BoxGeometry(0.55, 0.75, 0.45), steel);
    machine.position.set(x - 0.55, 1.05, z);

    const groupHead = this._mesh(new THREE.BoxGeometry(0.45, 0.2, 0.35), dark);
    groupHead.position.set(x - 0.55, 1.48, z);

    const cup1 = this._mesh(new THREE.CylinderGeometry(0.07, 0.06, 0.14, 10), this._mat(0xf5f5f5));
    cup1.position.set(x + 0.2, 0.97, z - 0.1);
    const cup2 = cup1.clone();
    cup2.position.set(x + 0.45, 0.97, z + 0.08);

    const steamMeshes = this._addSteam(x, z);

    const pot = this._mesh(new THREE.CylinderGeometry(0.12, 0.14, 0.2, 12), this._mat(0x1a1a1a, 0x331100, 0.4, 0.5));
    pot.position.set(x + 0.75, 1.0, z);

    this._group(counter, machine, groupHead, cup1, cup2, ...steamMeshes, pot);
  }

  _coffeeSeating(x, z) {
    const stool = this._mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.45, 12), this._mat(0x4a3728));
    stool.position.set(x, 0.22, z);
    const table = this._mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.06, 16), this._mat(0x3d2e1e));
    table.position.set(x, 0.48, z);
    this._group(stool, table);
  }

  _callBooth(x, z) {
    const frame = this._mat(0x1e293b);
    const glass = new THREE.MeshStandardMaterial({
      color: 0x88aacc,
      transparent: true,
      opacity: 0.35,
      roughness: 0.1,
      metalness: 0.2,
    });
    const w = 1.55;
    const h = 1.75;
    const d = 1.55;

    const floorPad = this._mesh(new THREE.BoxGeometry(w, 0.05, d), this._mat(0x243044));
    floorPad.position.set(x, 0.025, z);

    const back = this._mesh(new THREE.BoxGeometry(w, h, 0.06), frame);
    back.position.set(x, h / 2, z - d / 2 + 0.03);
    const left = this._mesh(new THREE.BoxGeometry(0.06, h, d), frame);
    left.position.set(x - w / 2 + 0.03, h / 2, z);
    const right = this._mesh(new THREE.BoxGeometry(0.06, h, d), frame);
    right.position.set(x + w / 2 - 0.03, h / 2, z);

    const glassPanel = this._mesh(new THREE.BoxGeometry(w - 0.2, h - 0.3, 0.04), glass);
    glassPanel.position.set(x, h / 2, z + d / 2 - 0.05);

    const desk = this._mesh(new THREE.BoxGeometry(0.7, 0.05, 0.45), this._mat(0x334155));
    desk.position.set(x, 0.72, z);
    const stool = this._mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.42, 10), this._mat(0x475569));
    stool.position.set(x, 0.21, z + 0.35);

    const phone = this._mesh(new THREE.BoxGeometry(0.12, 0.04, 0.2), this._mat(0x111827));
    phone.position.set(x + 0.15, 0.78, z - 0.05);

    const led = this._mesh(new THREE.SphereGeometry(0.06, 8, 8), this._mat(0x22c55e, 0x22cc55));
    led.position.set(x, h - 0.15, z + d / 2 - 0.02);
    const boothLight = this._addGlowLight(x, h - 0.2, z, 0x22ff66, 0.15);
    this._animatedProps.push({
      mesh: led,
      light: boothLight,
      type: 'callLed',
      phase: x * 2,
      x,
      z,
    });

    const sign = this._mesh(
      new THREE.BoxGeometry(0.5, 0.12, 0.02),
      this._mat(0x0f172a, 0x112233),
    );
    sign.position.set(x, h - 0.35, z - d / 2 + 0.08);
    this._animatedProps.push({ mesh: sign, type: 'callSign', phase: x, x, z });

    this._group(floorPad, back, left, right, glassPanel, desk, stool, phone, led, sign);
  }

  _chessTable(x, z) {
    const legMat = this._mat(0x3d2817);
    const top = this._mesh(new THREE.BoxGeometry(1.1, 0.08, 1.1), this._mat(0x1a1a1a));
    top.position.set(x, 0.58, z);
    const leg = (dx, dz) => {
      const l = this._mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.55, 8), legMat);
      l.position.set(x + dx, 0.28, z + dz);
      return l;
    };
    const pieces = [];
    const boardColors = [0xf0d9b5, 0xb58863];
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) {
        const sq = this._mesh(
          new THREE.BoxGeometry(0.12, 0.02, 0.12),
          this._mat(boardColors[(i + j) % 2]),
        );
        sq.position.set(x - 0.2 + i * 0.13, 0.63, z - 0.2 + j * 0.13);
        pieces.push(sq);
      }
    }
    const king = this._mesh(new THREE.CylinderGeometry(0.04, 0.05, 0.12, 8), this._mat(0xffffff));
    king.position.set(x, 0.7, z);
    const rook = this._mesh(new THREE.CylinderGeometry(0.035, 0.04, 0.1, 8), this._mat(0x222222));
    rook.position.set(x + 0.15, 0.69, z + 0.1);
    this._group(top, leg(-0.45, -0.45), leg(0.45, -0.45), leg(-0.45, 0.45), leg(0.45, 0.45), ...pieces, king, rook);
  }

  _pingPongTable(x, z) {
    const blue = this._mat(0x1d4ed8);
    const top = this._mesh(new THREE.BoxGeometry(2.4, 0.08, 1.3), blue);
    top.position.set(x, 0.62, z);
    const net = this._mesh(new THREE.BoxGeometry(0.04, 0.22, 1.32), this._mat(0xeeeeee));
    net.position.set(x, 0.78, z);
    const leg = (dx, dz) => {
      const l = this._mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.6, 8), this._mat(0x64748b));
      l.position.set(x + dx, 0.3, z + dz);
      return l;
    };
    const paddleL = this._mesh(new THREE.BoxGeometry(0.14, 0.02, 0.2), this._mat(0xff4444));
    paddleL.position.set(x - 0.5, 0.72, z + 0.35);
    const paddleR = this._mesh(new THREE.BoxGeometry(0.14, 0.02, 0.2), this._mat(0x4444ff));
    paddleR.position.set(x + 0.5, 0.72, z - 0.35);
    const ball = this._mesh(new THREE.SphereGeometry(0.05, 10, 10), this._mat(0xffffff));
    ball.position.set(x, 0.72, z);
    this._group(top, net, leg(-1, -0.5), leg(1, -0.5), leg(-1, 0.5), leg(1, 0.5), paddleL, paddleR, ball);
  }

  _gamingStation(x, z) {
    const tv = this._mesh(new THREE.BoxGeometry(1.6, 0.9, 0.08), this._mat(0x0a0a0a));
    tv.position.set(x, 1.35, z - 0.5);
    const screenMat = new THREE.MeshStandardMaterial({
      color: 0x1e3a8a,
      emissive: 0x3366ff,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.1,
    });
    const screen = this._mesh(new THREE.BoxGeometry(1.45, 0.82, 0.02), screenMat);
    screen.position.set(x, 1.35, z - 0.46);
    const tvLight = this._addGlowLight(x, 1.35, z - 0.3, 0x4488ff, 0.4);
    this._animatedProps.push({
      mesh: screen,
      light: tvLight,
      type: 'screen',
      phase: 0,
      x,
      z,
    });

    const stand = this._mesh(new THREE.BoxGeometry(0.4, 0.5, 0.35), this._mat(0x1f2937));
    stand.position.set(x, 0.25, z - 0.45);

    const ps5 = this._mesh(new THREE.BoxGeometry(0.35, 0.95, 0.22), this._mat(0xf8fafc));
    ps5.position.set(x - 0.55, 0.48, z + 0.15);
    ps5.rotation.y = 0.25;

    const controller1 = this._mesh(new THREE.BoxGeometry(0.22, 0.06, 0.14), this._mat(0x2563eb));
    controller1.position.set(x + 0.2, 0.55, z + 0.2);
    const controller2 = controller1.clone();
    controller2.material = this._mat(0xdc2626);
    controller2.position.set(x + 0.45, 0.55, z + 0.2);

    const couch = this._mesh(new THREE.BoxGeometry(1.8, 0.4, 0.7), this._mat(0x4c1d95));
    couch.position.set(x, 0.28, z + 0.85);

    this._group(tv, screen, stand, ps5, controller1, controller2, couch);
  }

  _poolTable(x, z) {
    const felt = this._mat(0x166534);
    const top = this._mesh(new THREE.BoxGeometry(2.0, 0.1, 1.0), felt);
    top.position.set(x, 0.62, z);
    const rail = this._mat(0x3d2817);
    const railN = this._mesh(new THREE.BoxGeometry(2.05, 0.14, 0.08), rail);
    railN.position.set(x, 0.68, z - 0.5);
    const railS = railN.clone();
    railS.position.z = z + 0.5;
    const cue = this._mesh(new THREE.CylinderGeometry(0.02, 0.025, 1.2, 8), this._mat(0x8b6914));
    cue.position.set(x + 0.9, 0.75, z + 0.3);
    cue.rotation.z = 0.4;
    this._group(top, railN, railS, cue);
  }

  _sofa(x, z) {
    const base = this._mesh(new THREE.BoxGeometry(2.4, 0.45, 0.9), this._mat(0x4a3060));
    base.position.set(x, 0.32, z);
    const back = this._mesh(new THREE.BoxGeometry(2.4, 0.5, 0.2), this._mat(0x3d2650));
    back.position.set(x, 0.62, z - 0.35);
    this._group(base, back);
  }

  buildDesks(desks) {
    if (this._desksBuilt) return;
    this._desksBuilt = true;
    desks.forEach((d) => {
      const p = pctToWorld(d.x, d.y);
      this._workDesk(p.x, p.z);
    });
  }

  _workDesk(x, z) {
    const deskMat = this._mat(0x3d4f6a);
    const metal = this._mat(0x64748b, 0x000000, 0.5, 0.4);

    const top = this._mesh(new THREE.BoxGeometry(1.0, 0.06, 0.6), deskMat);
    top.position.set(x, 0.55, z + 0.15);

    const leg = (dx, dz) => {
      const l = this._mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.52, 8), metal);
      l.position.set(x + dx, 0.28, z + dz);
      return l;
    };

    const chairSeat = this._mesh(new THREE.BoxGeometry(0.38, 0.06, 0.38), this._mat(0x1e293b));
    chairSeat.position.set(x, 0.38, z - 0.45);
    const chairBack = this._mesh(new THREE.BoxGeometry(0.38, 0.45, 0.06), this._mat(0x1e293b));
    chairBack.position.set(x, 0.58, z - 0.62);

    const laptopBase = this._mesh(new THREE.BoxGeometry(0.42, 0.03, 0.28), this._mat(0x94a3b8, 0x000000, 0.6, 0.3));
    laptopBase.position.set(x, 0.6, z + 0.12);

    const laptopScreenMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      emissive: 0x2266cc,
      emissiveIntensity: 0.45,
      roughness: 0.4,
      metalness: 0.05,
    });
    const laptopScreen = this._mesh(new THREE.BoxGeometry(0.42, 0.28, 0.02), laptopScreenMat);
    laptopScreen.position.set(x, 0.74, z - 0.02);
    laptopScreen.rotation.x = -0.35;
    const lapLight = this._addGlowLight(x, 0.78, z + 0.1, 0x3399ff, 0.22);
    this._animatedProps.push({
      mesh: laptopScreen,
      light: lapLight,
      type: 'laptop',
      phase: x,
      x,
      z,
    });

    const keyboard = this._mesh(new THREE.BoxGeometry(0.35, 0.01, 0.12), this._mat(0x334155));
    keyboard.position.set(x, 0.59, z + 0.22);

    const mug = this._mesh(new THREE.CylinderGeometry(0.05, 0.045, 0.1, 10), this._mat(0xf8fafc));
    mug.position.set(x + 0.35, 0.63, z + 0.2);

    this._group(
      top,
      leg(-0.42, -0.2),
      leg(0.42, -0.2),
      leg(-0.42, 0.35),
      leg(0.42, 0.35),
      chairSeat,
      chairBack,
      laptopBase,
      laptopScreen,
      keyboard,
      mug,
    );
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
    group.userData.characterId = name;

    const labelEl = document.createElement('div');
    labelEl.className = 'office-3d-agent-label';
    labelEl.innerHTML = '<strong></strong><span class="act"></span><span class="hrs"></span>';
    labelEl.addEventListener('click', (e) => {
      e.stopPropagation();
      this.focusOnCharacter(name);
      this.onMemberClick?.(name);
    });
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

  moveCharacter(id, xPct, yPct, state, hints = {}) {
    const entry = this.characters.get(id);
    if (!entry) return;
    const world = pctToWorld(xPct, yPct);
    entry.target.set(world.x, 0, world.z);
    entry.state = state;
    if (hints.gameKey) entry.gameKey = hints.gameKey;
    entry.mesh.userData.labelEl.className = `office-3d-agent-label state-${state}`;
  }

  _clearPovLabels() {
    this.characters.forEach((entry) => {
      entry.mesh.userData.labelEl?.classList.remove('is-pov');
    });
  }

  _computePov(entry) {
    const pos = entry.mesh.position;
    const eye = new THREE.Vector3(pos.x, 1.55, pos.z);
    const state = this._followHints.state || entry.state;
    const gameKey = this._followHints.gameKey || entry.gameKey;

    let target;
    if (state === 'gaming' && gameKey && this._povLooks[gameKey]) {
      target = this._povLooks[gameKey].clone();
    } else if (state === 'coffee') {
      target = this._povLooks.coffee.clone();
    } else if (state === 'phone') {
      target = eye.clone().add(new THREE.Vector3(0, 0.05, -1.3));
    } else if (state === 'working' || state === 'talking') {
      target = eye.clone().add(new THREE.Vector3(0, -0.15, -1.0));
    } else if (state === 'idle') {
      target = eye.clone().add(new THREE.Vector3(0, -0.1, -0.85));
    } else {
      target = eye.clone().add(new THREE.Vector3(0, 0, -1.4));
    }

    return { position: eye, target };
  }

  focusOnCharacter(id, hints = {}) {
    const entry = this.characters.get(id);
    if (!entry) return;
    this._justFocusedPov = true;
    clearTimeout(this._focusPovTimer);
    this._focusPovTimer = setTimeout(() => {
      this._justFocusedPov = false;
    }, 120);
    this._followId = id;
    this._followHints = { ...hints };
    this._clearPovLabels();
    entry.mesh.userData.labelEl?.classList.add('is-pov');
    this._updatePovBanner(id);
    const pov = this._computePov(entry);
    this.camera.position.copy(pov.position);
    this.controls.target.copy(pov.target);
    this.controls.update();
  }

  clearCharacterPov() {
    this._followId = null;
    this._followHints = {};
    this._clearPovLabels();
    this._updatePovBanner(null);
  }

  _updatePovBanner(id) {
    if (!this._povBanner) return;
    if (!id) {
      this._povBanner.style.display = 'none';
      return;
    }
    const first = id.split(' ')[0];
    this._povBanner.textContent = `👁 ${first}'s POV — drag scene to exit · ↺ reset view`;
    this._povBanner.style.display = 'block';
  }

  _bindCharacterPicks() {
    let pointerDown = null;
    const pickCharacter = (clientX, clientY) => {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this._pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
      this._pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
      this._raycaster.setFromCamera(this._pointer, this.camera);
      const meshes = [];
      this.characters.forEach((entry, charId) => {
        entry.mesh.traverse((child) => {
          if (child.isMesh) {
            child.userData.characterId = charId;
            meshes.push(child);
          }
        });
      });
      const hits = this._raycaster.intersectObjects(meshes, false);
      if (!hits.length) return;
      const id = hits[0].object.userData.characterId;
      if (!id) return;
      this.focusOnCharacter(id);
      this.onMemberClick?.(id);
    };

    const onPointerDown = (e) => {
      if (e.button !== 0) return;
      pointerDown = { x: e.clientX, y: e.clientY };
    };
    const onPointerUp = (e) => {
      if (!pointerDown || e.button !== 0) return;
      const dx = e.clientX - pointerDown.x;
      const dy = e.clientY - pointerDown.y;
      pointerDown = null;
      if (dx * dx + dy * dy > 64) return;
      pickCharacter(e.clientX, e.clientY);
    };

    this.renderer.domElement.addEventListener('pointerdown', onPointerDown);
    this.renderer.domElement.addEventListener('pointerup', onPointerUp);
    this._pointerDownHandler = onPointerDown;
    this._pointerUpHandler = onPointerUp;
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

  _nearbyCharacterBoost(x, z, states, radius = 2.8) {
    let boost = 0;
    this.characters.forEach((entry) => {
      if (states && !states.includes(entry.state)) return;
      const dx = entry.mesh.position.x - x;
      const dz = entry.mesh.position.z - z;
      const d = Math.sqrt(dx * dx + dz * dz);
      if (d < radius) boost = Math.max(boost, 1 - d / radius);
    });
    return boost;
  }

  _animateProps(dt) {
    const t = this.clock.elapsedTime;

    this._animatedProps.forEach((p) => {
      if (p.type === 'steam') {
        p.rise = (p.rise || 0) + dt * 0.22;
        const cycle = p.rise % 1;
        p.mesh.position.y = p.baseY + cycle * 0.45;
        p.mesh.position.x = p.baseX + Math.sin(t * 1.8 + p.phase) * 0.04;
        p.mesh.position.z = p.baseZ + Math.cos(t * 1.5 + p.phase) * 0.04;
        p.mesh.material.opacity = 0.5 * (1 - cycle);
        p.mesh.scale.setScalar(0.6 + cycle * 0.9);

        const coffeeBoost = this._nearbyCharacterBoost(p.baseX, p.baseZ, ['coffee'], 3.5);
        if (coffeeBoost > 0) {
          p.mesh.material.opacity = Math.min(0.65, p.mesh.material.opacity + coffeeBoost * 0.35);
          p.rise += dt * coffeeBoost * 0.35;
        }
      } else if (p.type === 'callLed') {
        const phoneBoost = this._nearbyCharacterBoost(p.x, p.z, ['phone'], 2.2);
        const pulse = 0.5 + 0.5 * Math.sin(t * 5 + p.phase);
        const active = phoneBoost > 0.2 || pulse > 0.65;
        const intensity = active ? 0.85 + phoneBoost * 0.15 : 0.15 + pulse * 0.25;

        p.mesh.material.emissive.setHex(active ? 0x33ff66 : 0x441111);
        p.mesh.material.emissiveIntensity = intensity;
        p.mesh.material.color.setHex(active ? 0x66ff99 : 0x663333);
        p.mesh.scale.setScalar(0.9 + intensity * 0.35);

        if (p.light) {
          p.light.intensity = active ? 0.35 + phoneBoost * 0.5 : 0.05 + pulse * 0.12;
          p.light.color.setHex(active ? 0x44ff77 : 0x225533);
        }
      } else if (p.type === 'callSign') {
        const phoneBoost = this._nearbyCharacterBoost(p.x, p.z, ['phone'], 2.2);
        const on = phoneBoost > 0.2;
        p.mesh.material.emissive.setHex(on ? 0x114422 : 0x000000);
        p.mesh.material.emissiveIntensity = on ? 0.4 + Math.sin(t * 8) * 0.15 : 0;
        p.mesh.material.color.setHex(on ? 0x1a3d2a : 0x0f172a);
      } else if (p.type === 'laptop') {
        const workBoost = this._nearbyCharacterBoost(p.x, p.z, ['working', 'idle'], 1.8);
        const flicker = 0.85 + Math.sin(t * 12 + p.phase) * 0.08 + Math.sin(t * 3.7) * 0.05;
        const intensity = (0.35 + workBoost * 0.65) * flicker;

        p.mesh.material.emissive.setRGB(0.1 * intensity, 0.25 * intensity, 0.85 * intensity);
        p.mesh.material.emissiveIntensity = intensity;

        if (p.light) {
          p.light.intensity = 0.08 + workBoost * 0.45;
        }
      } else if (p.type === 'screen') {
        const gameBoost = this._nearbyCharacterBoost(p.x, p.z, ['gaming'], 3.2);
        const flicker = 0.8 + Math.sin(t * 6 + p.phase) * 0.12;
        const intensity = (0.4 + gameBoost * 0.8) * flicker;

        p.mesh.material.emissive.setRGB(0.15 * intensity, 0.2 * intensity, 0.95 * intensity);
        p.mesh.material.emissiveIntensity = intensity;

        if (p.light) {
          p.light.intensity = 0.15 + gameBoost * 0.7;
        }
      }
    });
  }

  _bindCameraUI(mountEl) {
    const hint = document.createElement('div');
    hint.className = 'office-3d-camera-hint';
    hint.innerHTML = '🖱️ Drag to rotate · Scroll to zoom · Click member for POV';
    mountEl.appendChild(hint);

    const povBanner = document.createElement('div');
    povBanner.className = 'office-3d-pov-banner';
    povBanner.style.display = 'none';
    mountEl.appendChild(povBanner);
    this._povBanner = povBanner;

    const resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'office-3d-reset-camera';
    resetBtn.textContent = '↺ Reset view';
    resetBtn.addEventListener('click', () => this.resetCamera());
    mountEl.appendChild(resetBtn);
  }

  resetCamera() {
    this.clearCharacterPov();
    this.onPovExit?.();
    this.camera.position.copy(this._defaultCamera.position);
    this.controls.target.copy(this._defaultCamera.target);
    this.controls.update();
  }

  _animate() {
    requestAnimationFrame(this._animate);
    const dt = this.clock.getDelta();
    this.controls.update();
    this.characters.forEach((entry) => this._animateCharacter(entry, dt));

    if (this._followId) {
      const entry = this.characters.get(this._followId);
      if (entry) {
        const pov = this._computePov(entry);
        const blend = 1 - Math.pow(0.0008, dt);
        this.camera.position.lerp(pov.position, blend);
        this.controls.target.lerp(pov.target, blend);
        this.controls.update();
      }
    }

    this._animateProps(dt);
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
    if (this._pointerDownHandler) {
      this.renderer.domElement.removeEventListener('pointerdown', this._pointerDownHandler);
    }
    if (this._pointerUpHandler) {
      this.renderer.domElement.removeEventListener('pointerup', this._pointerUpHandler);
    }
    clearTimeout(this._focusPovTimer);
    this.controls?.dispose();
    this.characters.clear();
    this.renderer.dispose();
    this.mount.innerHTML = '';
  }
}
