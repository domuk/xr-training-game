// Drives the 2U server model from the data baked into its glTF extras:
// - tabs, buttons, ejectors, levers and screws respond to a laser click/poke
// - v0.1 parts are always laser-grabbable (point + hold trigger / pinch);
//   a grab the rules don't allow yet is dropped straight away with a reason
// - a fitted part only slides along its real `pull` path until it is out
// - released near its slot, a part slides back in along the same path
// Rules live in rules.ts; words in text.ts.
//
// Grab handles are added once and never removed: IWSDK 1.0.1 keeps a grab
// handle alive after its grab component is removed, so toggling them breaks
// input.
import {
  Box3,
  BoxGeometry,
  createSystem,
  DistanceGrabbable,
  Grabbed,
  GrabSystem,
  InputComponent,
  LocomotionEnvironment,
  type Material,
  Matrix4,
  Mesh,
  MeshBasicMaterial,
  MovementMode,
  PlaneGeometry,
  PokeInteractable,
  Quaternion,
  RayInteractable,
  Raycaster,
  SlideSystem,
  SphereGeometry,
  TeleportSystem,
  TurnSystem,
  Vector3,
  VisibilityState,
  type Entity,
  type Object3D,
  type UIKitMLAsset,
  Color,
  LocomotionSystem,
} from '@iwsdk/core';
import { ServiceControl, ServicePart } from './components.js';
import {
  type AxisName,
  CABLES,
  type ControlInfo,
  isV01Control,
  isV01Part,
  label,
  parseOrder,
  type PartInfo,
  ServiceRules,
  splitList,
  type Vec3,
} from './rules.js';
import { LabRoom, type RackSlot } from './lab.js';
import { LabTablet } from './tablet.js';
import { MOVE_TEXT, READY_TEXT, SCREW_TIP, START_TEXT, TIPS, TOOL_TEXT } from './text.js';

const SNAP_DISTANCE = 0.08; // m — how close a free part must be to its slot
const SMOOTHING = 18; // 1/s: higher = snappier, lower = steadier
const REACH_HAND = 0.04; // m: pinch this close to a part to grab it
const REACH_CONTROLLER = 0.06; // m: grip this close to a part to grab it
const PRESSED_COLOR = 0x22c55e; // green: tab/button/screw operated
const ZOOM_SPEED = 0.8; // m/s: right stick pushes a held server away / back
const TOOL_REACH = 0.04; // m: screwdriver tip to screw for the buttons
const TOOL_TOUCH = 0.015; // m: hand-held screwdriver toggles on touch
const TOOL_COOLDOWN = 2; // s: between screwdriver turns
const TOOL_GRIP_AT = 0.2; // fraction along the screwdriver (from the handle end) held in the palm
const TOOL_SMOOTHING = 35; // 1/s: screwdriver in hand (wrist is steady, so less lag)
const TOOL_JUMP_POS = 0.12; // m in one frame: hand tracking glitch, hold still
const TOOL_JUMP_ANGLE = 1.0; // rad in one frame: same, for rotation
const START_RACK_SLOT = 'slot_rack_3_u21'; // where the server starts (rack 3, U21-22, ~1 m up)
const RACK_REACH = 0.3; // m: let go this close to a rack slot to rack the server
const RACK_ANGLE = 35; // degrees: how square to the rack the server must be
const RACKED_TEXT =
  'The server is in the rack. Pull it out with both hands on its sides (drives can be swapped in place).';
const ROOM_STAND = 0.95;
const ROOM_HALF = 4.0; // m: loose parts stay within the 8.4 m room (minus wall thickness) // m: where the user stands, south of the island table slot
const MENU_DOUBLE = 0.45; // s: two A presses within this = quick menu
const MENU_HOLD = 2; // s: right-hand pinch held this long (nothing grabbed) = quick menu
const CURSOR_MAX = 1.6; // laser dot scale cap (IWSDK grows it with distance)
const PATH_END = 0.995;
const SHORT_PATH = 0.03; // m: pull paths shorter than this (drive in caddy)…
const BREAK_FREE = 0.03; // m: …come free when pulled this far in any direction

/** Parts that can go back into any free slot of the same kind. */
const SLOT_GROUPS: { group: string; match: RegExp }[] = [
  { group: 'caddy', match: /^asset_caddy_\d+$/ },
  { group: 'fan', match: /^asset_fan_\d+$/ },
  { group: 'card', match: /^asset_(nic|accel)$/ },
  { group: 'cpu', match: /^asset_cpu_\d+$/ },
  { group: 'hs', match: /^asset_hs_\d+$/ },
];

/** Exploded-view buttons → which parts they move. */
const EXPLODE_GROUPS: Record<string, RegExp> = {
  lid: /^asset_lid$/,
  drives: /^asset_caddy_\d+$/,
  fans: /^asset_fan_\d+$/,
  dimms: /^asset_dimm_\d+$/,
  heatsinks: /^asset_hs_\d+$/,
  cpus: /^asset_cpu_\d+$/,
  cards: /^asset_(nic|accel)$/,
}; // fraction of a path segment that counts as "out"

/** Blender (Z-up) vector → glTF/three (Y-up): (x, y, z) → (x, z, -y). */
function toGl(v: Vec3): Vector3 {
  return new Vector3(v[0], v[2], -v[1]);
}

type PointerEventLike = { stopPropagation?: () => void };

/** three's typed event map doesn't list pointer events; IWSDK dispatches them. */
function listen(
  obj: Object3D,
  type: 'pointerdown' | 'pointerenter',
  fn: (event: PointerEventLike) => void,
): void {
  (obj as unknown as {
    addEventListener: (t: string, f: (e: PointerEventLike) => void) => void;
  }).addEventListener(type, fn);
}

function axisVector(axis: AxisName): Vector3 {
  if (axis === 'X') return new Vector3(1, 0, 0);
  if (axis === 'Y') return new Vector3(0, 0, -1);
  return new Vector3(0, 1, 0);
}

type PartMode = 'fitted' | 'seated' | 'free' | 'gone';

interface PartRuntime {
  info: PartInfo;
  entity: Entity;
  object: Object3D;
  restPos: Vector3;
  restQuat: Quaternion;
  /** Path points in parent space: rest, rest+pull1, rest+pull1+pull2 … */
  path: Vector3[];
  mode: PartMode;
  stage: number;
  busy: boolean;
  /** Grab refused by the rules: ignore its release. */
  denied: boolean;
  /** Swappable parts: slot group, current slot and original slot. */
  group?: string;
  slot?: number;
  homeSlot?: number;
}

interface ControlRuntime {
  info: ControlInfo;
  entity: Entity;
  object: Object3D;
  restPos: Vector3;
  restQuat: Quaternion;
  axis: Vector3;
  riseDir: Vector3;
  /** 0 = rest (closed / tight), 1 = operated (open / undone). */
  amount: number;
}

/** A part (or the server) held by a hand pinch / controller grip up close. */
interface NearGrab {
  part?: PartRuntime;
  server?: boolean;
  tablet?: boolean;
  tool?: boolean;
  /** Held object's world matrix relative to the hand. */
  offset: Matrix4;
  /** Screwdriver in a tracked hand: follow the wrist (palm), not the fingertip. */
  wrist?: boolean;
  /** Last accepted wrist pose (glitch frames are skipped). */
  lastPos?: Vector3;
  lastQuat?: Quaternion;
  /** Frames skipped in a row (a real fast move is accepted after a few). */
  skipped?: number;
}

/** Laser drag of the server (move mode) or the tablet (by a side grip). */
interface ServerDrag {
  target: 'server' | 'tablet' | 'tool';
  hand: 'left' | 'right';
  /** Tablet only: its world matrix relative to the laser (moves AND turns with it). */
  rigid?: Matrix4;
  distance: number;
  offset: Vector3;
}

interface Tween {
  update: (t: number) => void;
  duration: number;
  elapsed: number;
  done?: () => void;
}

export class ServiceSystem extends createSystem({
  grabbedParts: { required: [ServicePart, Grabbed] },
}) {
  private rules?: ServiceRules;
  private serverEntity?: Entity;
  private parts = new Map<string, PartRuntime>();
  private controls = new Map<string, ControlRuntime>();
  private entities = new Map<Object3D, Entity>();
  private tweens: Tween[] = [];
  private tablet = new LabTablet(this.world);
  private tool?: Object3D;
  private toolTip?: Object3D;
  private toolShown?: string;
  private toolTouched = new Set<string>();
  /** Screwdriver pose relative to the left grip (palm). */
  private toolOffset?: Matrix4;
  /** Last accepted left-grip pose for the screwdriver (glitch skipping). */
  private toolHold: { lastPos?: Vector3; lastQuat?: Quaternion; skipped?: number } = {};
  /** Time (s) the screwdriver last turned a screw (cooldown). */
  private toolLastTurn = -Infinity;
  /** Where the training happens: the lab room (default), passthrough AR or a black void. */
  private setting: 'room' | 'ar' | 'black' = 'room';
  /** Reset view: move the player (and tablet) only, leave the server where it is. */
  private viewOnly = false;
  private lab?: Object3D;
  private labRoom = new LabRoom(this.world);
  private labState: 'waiting' | 'loading' | 'ready' = 'waiting';
  private propEntity?: Entity;
  private propHeld = false;
  /** Rack slot the server is in (only the drives are reachable then). */
  private serverSlot?: RackSlot;
  /** Hands gripping the server's sides; both = carrying. */
  private sideHold = new Set<'left' | 'right'>();
  private carry?: { offset: Vector3; yawOffset: number };
  /** Server bounds in its own space (lifting grips are its left / right sides). */
  private serverBox?: Box3;
  /** Quick menu (double-press A / pinch-and-hold right hand). */
  private menu?: Object3D & UIKitMLAsset;
  private menuScale = 0.07;
  private menuOpen = false;
  private lastAPress = -Infinity;
  private pinchSince = -1;
  private pinchUsed = false;
  /** Laser dots (IWSDK cursor meshes), size-capped each frame. */
  private cursors: Mesh[] = [];
  private cursorSearch = 0;
  /** Sockets whose load plate stays open until their CPU is taken out and refitted. */
  private plateNeedsCycle = new Set<number>();
  private tabletReady = false;
  private started = false;
  /** safety (tablet locked) -> training; 'place' = Move server mode. */
  private phase: 'safety' | 'place' | 'training' = 'safety';
  private exploded = false;
  private nearGrabs = new Map<'left' | 'right', NearGrab>();
  private serverDrag?: ServerDrag;
  private smooth = new Map<string, Vector3>();
  /** Laser-held parts: extra distance pushed out with the right stick. */
  private zoom = new Map<string, number>();
  /** Laser-held free parts: where they were last shown (kept on release). */
  private lastHeld = new Map<string, Vector3>();
  /** Held parts currently showing the green "will snap in" glow. */
  private snapCued = new Set<PartRuntime>();
  private pokeOn = false;
  private raycaster = new Raycaster();
  private passDirty = true;
  private hitGeometry = new SphereGeometry(0.009, 8, 6);
  private hitMaterial = new MeshBasicMaterial({ visible: false });
  private removedSet = false;
  private controlsOpen = false;
  private movement = true;
  private placePending = false;
  private slotMarkers: Object3D[] = [];
  /** Slot poses per group (parent space), from the parts' original places. */
  private slots = new Map<string, { pos: Vector3; quat: Quaternion }[]>();
  private tintCache = new Map<Material, Map<number, Material>>();
  private tmp = new Vector3();
  private tmp2 = new Vector3();

  init(): void {
    this.queries.grabbedParts.subscribe('qualify', (e) => this.onGrabStart(e));
    this.queries.grabbedParts.subscribe('disqualify', (e) => this.onGrabEnd(e));
    // Place the server and panels around the user on entering XR.
    this.cleanupFuncs.push(
      this.world.visibilityState.subscribe((state) => {
        if (state !== VisibilityState.NonImmersive) this.placePending = true;
      }),
    );
    this.createFloor();
  }

  update(delta: number): void {
    if (this.rules == null && !this.tryInit()) return;
    if (!this.tabletReady) this.tryInitTablet();
    if (this.tool == null) this.tryInitTool();
    if (this.placePending) this.tryPlaceAll();
    this.tablet.updateHud(this.player.head, delta);
    this.updateTweens(delta);
    this.updateInputMode();
    this.updateNearGrabs(delta);
    this.updateServerDrag(delta);
    this.updateLab(delta);
    this.updateLeftTool(delta);
    this.updateTool();
    this.updateMenu();
    this.capCursors();
    if (this.passDirty) {
      this.passDirty = false;
      this.updatePassThrough();
    }
    for (const entity of this.queries.grabbedParts.entities) {
      const part = this.partOf(entity);
      if (part == null) continue;
      if (part.denied) {
        // Refused grab: hold it in place until the release lands.
        part.object.position.copy(part.restPos);
        part.object.quaternion.copy(part.restQuat);
        continue;
      }
      if (part.mode === 'free') this.zoomHeld(entity, part, delta);
      this.smoothHeld(part, delta);
      if (part.mode === 'seated') this.followPath(part);
      if (part.mode === 'free') {
        const last = this.lastHeld.get(part.info.name);
        if (last != null) last.copy(part.object.position);
        else this.lastHeld.set(part.info.name, part.object.position.clone());
      }
    }
    this.updateSnapCue();
    if (this.serverDrag == null) {
      const zooming = [...this.queries.grabbedParts.entities].some(
        (e) => this.partOf(e)?.mode === 'free',
      );
      this.setStickTurning(!zooming);
    }
  }

  /**
   * Quick menu: double-press A (right controller), or pinch and hold the
   * right hand for MENU_HOLD seconds with nothing grabbed.
   */
  private updateMenu(): void {
    if (this.menu == null) this.tryInitMenu();
    const menu = this.menu;
    if (menu == null) return;
    const pad = this.input.xr.gamepads.right;
    if (pad == null) return;
    const now = performance.now() / 1000;
    if (this.input.xr.isPrimary('hand', 'right')) {
      const grabbing =
        this.nearGrabs.has('right') ||
        [...this.queries.grabbedParts.entities].some(
          (e) => this.world.getSystem(GrabSystem)?.getHolderHand(e) === 'right',
        );
      if (pad.getSelecting() && !grabbing) {
        if (this.pinchSince < 0) this.pinchSince = now;
        if (!this.pinchUsed && now - this.pinchSince >= MENU_HOLD) {
          this.pinchUsed = true;
          this.showMenu(!this.menuOpen);
        }
      } else {
        this.pinchSince = -1;
        this.pinchUsed = false;
      }
      return;
    }
    if (pad.getButtonDownByIdx(4)) {
      // 4 = A on the right controller.
      if (now - this.lastAPress < MENU_DOUBLE) {
        this.lastAPress = -Infinity;
        this.showMenu(!this.menuOpen);
      } else {
        this.lastAPress = now;
      }
    }
  }

  private tryInitMenu(): void {
    const menu = this.world.getSceneObject<UIKitMLAsset>('menu');
    const reset = menu?.getElementById('menu-reset-view');
    const close = menu?.getElementById('menu-close');
    if (menu == null || reset == null || close == null) return;
    this.menu = menu as Object3D & UIKitMLAsset;
    this.menuScale = this.menu.scale.x;
    reset.addEventListener('click', () => {
      this.showMenu(false);
      this.recallAll();
    });
    close.addEventListener('click', () => this.showMenu(false));
    for (const setting of ['room', 'ar', 'black'] as const) {
      menu.getElementById(`menu-${setting}`)?.addEventListener('click', () => {
        this.showMenu(false);
        this.setSetting(setting);
      });
    }
    this.showMenu(false);
  }

  /** Open the menu in front of the user, or hide it (tiny + no pointer hits). */
  private showMenu(open: boolean): void {
    const menu = this.menu;
    if (menu == null) return;
    this.menuOpen = open;
    (menu as Object3D & { pointerEvents?: string }).pointerEvents = open ? undefined : 'none';
    if (!open) {
      menu.scale.setScalar(1e-5);
      return;
    }
    menu.scale.setScalar(this.menuScale);
    const view = this.headView();
    if (view == null) return;
    const pos = view.headPos.clone().addScaledVector(view.forward, 0.45);
    pos.y = view.headPos.y - 0.12;
    this.facePanel(menu, pos, view.headPos, -10);
  }

  /** The laser dot grows with distance: keep it small (it flashed huge). */
  private capCursors(): void {
    if (this.cursors.length === 0) {
      if (++this.cursorSearch % 60 !== 1) return;
      this.player.traverse((o) => {
        const m = o as Mesh;
        if (m.isMesh && m.renderOrder === Infinity && m.geometry?.type === 'CircleGeometry') {
          this.cursors.push(m);
        }
      });
    }
    for (const c of this.cursors) if (c.scale.x > CURSOR_MAX) c.scale.setScalar(CURSOR_MAX);
  }

  /** Server, tablet and screwdriver back in front of the user (after teleporting). */
  private recallAll(): void {
    if (this.serverDrag != null || this.nearGrabs.size > 0) return; // something held
    this.placePending = true;
    this.viewOnly = true;
    this.say(
      'Reset view',
      this.setting === 'room'
        ? 'You are back at the island table.'
        : 'The server and tablet are back in front of you.',
      '',
    );
  }

  /** Green glow on a held part while letting go would snap it into a slot. */
  private updateSnapCue(): void {
    const held = new Set<PartRuntime>();
    for (const e of this.queries.grabbedParts.entities) {
      const p = this.partOf(e);
      if (p != null && p.mode === 'free' && !p.denied) held.add(p);
    }
    for (const g of this.nearGrabs.values()) {
      if (g.part != null && g.part.mode === 'free') held.add(g.part);
    }
    for (const part of held) {
      const ready = this.wouldSnap(part);
      if (ready && !this.snapCued.has(part)) {
        this.snapCued.add(part);
        this.tint(part.object, PRESSED_COLOR);
      } else if (!ready && this.snapCued.has(part)) {
        this.clearSnapCue(part);
      }
    }
    for (const part of [...this.snapCued]) if (!held.has(part)) this.clearSnapCue(part);
  }

  private clearSnapCue(part: PartRuntime): void {
    this.snapCued.delete(part);
    this.tint(part.object, null);
    this.passDirty = true; // put back screw / clip glows under the part
  }

  /** Would releasing this held part now snap it home? */
  private wouldSnap(part: PartRuntime): boolean {
    if (part.group != null) {
      const slot = this.snapSlot(part);
      if (slot < 0 || this.occupant(part.group, slot, part) != null) return false;
      if (part.group === 'hs') {
        return this.occupant('cpu', slot)?.mode === 'fitted' && this.socketBlock(slot, false) == null;
      }
      if (part.group === 'cpu') {
        return (
          this.occupant('hs', slot) == null &&
          (this.rules?.canRefit(part.info.name, this.socketControls(slot)).ok ?? false)
        );
      }
      return this.rules?.canRefit(part.info.name).ok ?? false;
    }
    return (
      this.pathDistance(part.path, part.object.position).dist <= SNAP_DISTANCE &&
      (this.rules?.canRefit(part.info.name).ok ?? false)
    );
  }

  /** Right stick up/down pushes a laser-held (free) part away / back. */
  private zoomHeld(entity: Entity, part: PartRuntime, delta: number): void {
    const hand = this.world.getSystem(GrabSystem)?.getHolderHand(entity);
    if (hand == null) return;
    let zoom = this.zoom.get(part.info.name) ?? 0;
    const stick = this.input.xr.gamepads.right?.getAxesValues(InputComponent.Thumbstick);
    if (stick != null && Math.abs(stick.y) > 0.2) {
      zoom = Math.min(3, Math.max(-1.5, zoom - stick.y * ZOOM_SPEED * delta));
      this.zoom.set(part.info.name, zoom);
    }
    if (zoom === 0) return;
    const ray = this.player.raySpaces[hand];
    const dir = new Vector3(0, 0, -1).applyQuaternion(ray.getWorldQuaternion(new Quaternion()));
    const world = part.object.getWorldPosition(new Vector3()).addScaledVector(dir, zoom);
    part.object.parent?.worldToLocal(world);
    part.object.position.copy(world);
  }

  /** Damp tracking jitter on a held part (laser or hand). */
  private smoothHeld(part: PartRuntime, delta: number): void {
    const prev = this.smooth.get(part.info.name);
    if (prev == null) {
      this.smooth.set(part.info.name, part.object.position.clone());
      return;
    }
    prev.lerp(part.object.position, 1 - Math.exp(-delta * SMOOTHING));
    part.object.position.copy(prev);
  }

  /** Invisible floor so teleport / thumbstick movement has ground to land on. */
  private createFloor(): void {
    const floor = new Mesh(
      new PlaneGeometry(40, 40).rotateX(-Math.PI / 2),
      new MeshBasicMaterial({ visible: false }),
    );
    floor.name = 'debug_floor';
    // Teleport still lands on it, but the laser dot never does (it grew huge
    // on this far-reaching invisible plane and flashed).
    (floor as Object3D & { pointerEvents?: string }).pointerEvents = 'none';
    const entity = this.world.createTransformEntity(floor);
    entity.addComponent(LocomotionEnvironment, { type: 'static' });
  }

  // ---------------------------------------------------------------- setup

  private tryInit(): boolean {
    const serverEntity = this.world.getSceneEntity('server');
    const serverObject = serverEntity?.object3D;
    const root = serverObject?.getObjectByName('server_root');
    if (serverEntity == null || serverObject == null || root == null) return false;
    this.serverEntity = serverEntity;
    this.entities.set(serverObject, serverEntity);

    const partInfos: PartInfo[] = [];
    const controlInfos: ControlInfo[] = [];
    const found: { obj: Object3D; part?: PartInfo; control?: ControlInfo }[] = [];
    root.traverse((obj) => {
      const x = obj.userData as Record<string, unknown>;
      if (x.role === 'asset') {
        const info: PartInfo = {
          name: obj.name,
          parent: this.parentAssetName(obj),
          requires: splitList(x.requires),
          pull: Array.isArray(x.pull) ? (x.pull as Vec3[]) : [],
          orderOut: parseOrder(x.order_out),
          orderIn: parseOrder(x.order_in),
          tip: x.tip as string | undefined,
          check: x.check as string | undefined,
          warn: x.warn as string | undefined,
          note: x.note as string | undefined,
        };
        partInfos.push(info);
        found.push({ obj, part: info });
      } else if (x.role === 'moving' || x.role === 'fastener') {
        const info: ControlInfo = {
          name: obj.name,
          asset: this.parentAssetName(obj),
          motion: x.role === 'fastener' ? 'screw' : (x.motion as ControlInfo['motion']),
          axis: (x.axis as AxisName) ?? 'Z',
          limits: (x.limits as [number, number]) ?? [0, 0],
          requires: splitList(x.requires),
          seq: typeof x.seq === 'number' ? x.seq : undefined,
          optional: x.optional === true,
          captive: x.captive === true,
          rise: typeof x.rise === 'number' ? x.rise : 0,
          tip: x.tip as string | undefined,
          note: x.note as string | undefined,
        };
        controlInfos.push(info);
        found.push({ obj, control: info });
      }
    });
    // Create entities after the traversal (adding components mutates nothing
    // in the tree, but keep the walk side-effect free anyway).
    for (const f of found) {
      if (f.part != null) this.addPart(f.obj, f.part);
      if (f.control != null) this.addControl(f.obj, f.control);
    }
    serverObject.updateMatrixWorld(true);
    this.serverBox = new Box3().setFromObject(serverObject);
    const origin = serverObject.getWorldPosition(new Vector3());
    this.serverBox.min.sub(origin);
    this.serverBox.max.sub(origin);
    this.rules = new ServiceRules(partInfos, controlInfos);
    this.buildSlots();
    this.hideCables(root);
    // Placing: a laser press anywhere on the server drags it (place phase).
    serverEntity.addComponent(RayInteractable);
    listen(serverObject, 'pointerdown', (event) => this.onServerPointerDown(event));
    return true;
  }

  /** Each swappable part's original place becomes a slot of its group. */
  private buildSlots(): void {
    for (const { group, match } of SLOT_GROUPS) {
      const members = [...this.parts.values()]
        .filter((p) => match.test(p.info.name))
        .sort((a, b) => a.info.name.localeCompare(b.info.name, 'en', { numeric: true }));
      this.slots.set(
        group,
        members.map((p) => ({ pos: p.restPos.clone(), quat: p.restQuat.clone() })),
      );
      members.forEach((p, i) => {
        p.group = group;
        p.slot = i;
        p.homeSlot = i;
      });
    }
    this.refreshSockets();
  }

  /** Move a part's "home" to slot `index` of its group (pose + pull path). */
  private assignSlot(part: PartRuntime, index: number): void {
    const slot = part.group != null ? this.slots.get(part.group)?.[index] : undefined;
    if (slot == null) return;
    part.slot = index;
    part.restPos.copy(slot.pos);
    part.restQuat.copy(slot.quat);
    part.path = [part.restPos.clone()];
    for (const step of part.info.pull) {
      part.path.push(part.path[part.path.length - 1].clone().add(toGl(step)));
    }
    this.refreshSockets();
  }

  /** The fitted part of `group` sitting in slot `index`, if any. */
  private occupant(group: string, index: number, except?: PartRuntime): PartRuntime | undefined {
    for (const p of this.parts.values()) {
      if (p === except || p.group !== group || p.slot !== index) continue;
      if (p.mode === 'fitted' || p.mode === 'seated' || p.busy) return p;
    }
    return undefined;
  }

  /**
   * CPU sockets: a CPU needs the heatsink on ITS socket off, plus that
   * socket's lever and plate; a socket lever needs that socket's heatsink off.
   */
  private refreshSockets(): void {
    const rules = this.rules;
    if (rules == null) return;
    for (let k = 0; k < 2; k++) {
      const hs = this.occupant('hs', k);
      const hsReq = hs != null ? [hs.info.name] : [];
      rules.setControlRequires(`socket_${k + 1}_lever`, hsReq);
      for (const cpu of this.parts.values()) {
        if (cpu.group !== 'cpu' || cpu.slot !== k) continue;
        rules.setPartRequires(cpu.info.name, [
          ...hsReq,
          `socket_${k + 1}_lever`,
          `socket_${k + 1}_plate`,
        ]);
      }
    }
  }

  private socketControls(k: number): string[] {
    return [`socket_${k + 1}_lever`, `socket_${k + 1}_plate`];
  }

  /**
   * Socket `k` must be open (lever up, then plate up) for a CPU, and closed
   * again (plate down, then lever down) before its heatsink goes on.
   * Returns what's wrong, or undefined if it's ready.
   */
  private socketBlock(k: number, wantOpen: boolean): string | undefined {
    const rules = this.rules;
    if (rules == null) return 'Loading.';
    const [lever, plate] = this.socketControls(k);
    if (wantOpen) {
      if (!rules.isOperated(lever)) return `Open the ${label(lever)} first.`;
      if (!rules.isOperated(plate)) return `Open the ${label(plate)} first.`;
    } else {
      if (rules.isOperated(plate)) return `Close the ${label(plate)} first.`;
      if (rules.isOperated(lever)) return `Close the ${label(lever)} first.`;
    }
    return undefined;
  }

  /** Cables and cords are hidden for now (coded properly later). */
  private hideCables(root: Object3D): void {
    root.traverse((obj) => {
      if (!CABLES.test(obj.name)) return;
      obj.visible = false;
      obj.traverse((o) => {
        (o as Object3D & { pointerEvents?: string }).pointerEvents = 'none';
      });
    });
  }

  private parentAssetName(obj: Object3D): string | null {
    for (let p = obj.parent; p != null; p = p.parent) {
      if ((p.userData as Record<string, unknown>).role === 'asset') return p.name;
    }
    return null;
  }

  /** Make an entity for `obj`, creating entities for its ancestors first. */
  private ensureEntity(obj: Object3D): Entity {
    const existing = this.entities.get(obj);
    if (existing != null) return existing;
    if (obj.parent == null) throw new Error(`No server ancestor for ${obj.name}`);
    const parent = this.ensureEntity(obj.parent);
    const entity = this.world.createTransformEntity(obj, { parent });
    this.entities.set(obj, entity);
    return entity;
  }

  private addPart(obj: Object3D, info: PartInfo): void {
    const entity = this.ensureEntity(obj);
    entity.addComponent(ServicePart, { name: info.name, state: 'fitted' });
    if (isV01Part(info.name)) {
      // Laser grab (trigger / pinch), always on. Rules are checked on grab.
      entity.addComponent(DistanceGrabbable, {
        movementMode: MovementMode.MoveFromTarget,
        rotate: true,
        translate: true,
        scale: false,
      });
    } else {
      entity.addComponent(RayInteractable);
    }
    const restPos = obj.position.clone();
    const path = [restPos.clone()];
    for (const step of info.pull) {
      path.push(path[path.length - 1].clone().add(toGl(step)));
    }
    this.parts.set(info.name, {
      info,
      entity,
      object: obj,
      restPos,
      restQuat: obj.quaternion.clone(),
      path,
      mode: 'fitted',
      stage: 0,
      busy: false,
      denied: false,
    });
    listen(obj, 'pointerdown', (event) => {
      if (this.phase === 'place') return; // let it reach the server (move)
      // Stop here so a parent part (e.g. the caddy around a drive) doesn't
      // start a grab too. The part's own grab handle still gets the event.
      event.stopPropagation?.();
      if (!isV01Part(info.name)) this.showPart(info.name);
    });
  }

  private addControl(obj: Object3D, info: ControlInfo): void {
    const entity = this.ensureEntity(obj);
    entity.addComponent(ServiceControl, { name: info.name, operated: false });
    entity.addComponent(RayInteractable);
    // PokeInteractable is added only while hands are in use (updateInputMode):
    // touch outranks the laser within 15 cm, which killed the laser up close.
    if (isV01Control(info.name)) {
      // Bigger invisible target so fingers (and the laser) hit small tabs.
      const hit = new Mesh(this.hitGeometry, this.hitMaterial);
      hit.name = `${info.name}_hit`;
      obj.add(hit);
    }
    // Grab handles on the parent part deny some pointer types to the whole
    // subtree; keep tabs and screws clickable.
    (obj as Object3D & { pointerEventsType?: unknown }).pointerEventsType = 'all';
    const axis = axisVector(info.axis);
    const riseDir = axis.clone();
    if (obj.position.dot(axis) < 0) riseDir.negate();
    this.controls.set(info.name, {
      info,
      entity,
      object: obj,
      restPos: obj.position.clone(),
      restQuat: obj.quaternion.clone(),
      axis,
      riseDir,
      amount: 0,
    });
    listen(obj, 'pointerdown', (event) => {
      if (this.phase === 'place') return; // let it reach the server (move)
      // Don't let the click reach the parent part's grab handle.
      event.stopPropagation?.();
      this.onControl(info.name);
    });
    listen(obj, 'pointerenter', () => this.showControl(info.name));
  }

  private partOf(entity: Entity): PartRuntime | undefined {
    return this.parts.get(entity.getValue(ServicePart, 'name') as string);
  }

  private setMode(part: PartRuntime, mode: PartMode): void {
    part.mode = mode;
    part.entity.setValue(ServicePart, 'state', mode);
    // A hidden ("gone") part must not catch lasers meant for what's under it.
    (part.object as Object3D & { pointerEvents?: string }).pointerEvents =
      mode === 'gone' ? 'none' : undefined;
    part.object.visible = mode !== 'gone';
    this.passDirty = true;
    // Lid lifted off: its buttons spring back (unpressed, no glow).
    if (part.info.name === 'asset_lid' && (mode === 'free' || mode === 'gone')) {
      for (const tab of ['lid_tab_L', 'lid_tab_R']) {
        const c = this.controls.get(tab);
        if (c == null || !this.rules?.isOperated(tab)) continue;
        this.rules.forceOperated(tab, false);
        c.entity.setValue(ServiceControl, 'operated', false);
        this.animateControl(c, 0);
      }
    }
    if (part.group === 'hs' || part.group === 'cpu') this.refreshSockets();
  }

  private syncControl(name: string): void {
    const c = this.controls.get(name);
    if (c == null || this.rules == null) return;
    c.entity.setValue(ServiceControl, 'operated', this.rules.isOperated(name));
    this.passDirty = true;
  }

  // --------------------------------------------------------------- panel

  private tryInitTablet(): void {
    if (!this.tablet.tryInit()) return;
    this.tabletReady = true;
    const t = this.tablet;
    t.on('btn-start-lab', () => this.onStartLab());
    t.on('btn-reset', () => this.resetServer());
    t.on('btn-safety', () => t.show('safety'));
    t.on('btn-hud', () => t.toggleHud());
    t.on('btn-recall', () => this.recallAll());
    t.on('srv-move', () => this.toggleMoveServer());
    t.on('srv-here', () => this.placeServer());
    t.on('srv-rotate', () => this.dbgRotate());
    t.on('srv-up', () => this.dbgNudge(0, 0.05));
    t.on('srv-down', () => this.dbgNudge(0, -0.05));
    t.on('srv-closer', () => this.dbgNudge(-0.05, 0));
    t.on('srv-further', () => this.dbgNudge(0.05, 0));
    const dbg = (id: string, fn: () => void) =>
      t.on(id, () => {
        this.ensureStarted();
        fn();
      });
    dbg('dbg-lid', () => this.dbgLid());
    dbg('dbg-remove', () => this.dbgRemove());
    dbg('dbg-controls', () => this.dbgControls());
    for (const which of ['all', ...Object.keys(EXPLODE_GROUPS)]) {
      dbg(`exp-${which}`, () => this.explode(which));
    }
    dbg('dbg-slots', () => this.dbgSlots());
    dbg('dbg-teleport', () => this.dbgMovement());
    if (this.world.visibilityState.peek() !== VisibilityState.NonImmersive) {
      this.placePending = true;
    }
  }

  private say(title: string, body: string, status: string): void {
    this.tablet.say(title, body, status);
  }

  private tipText(tip?: string): string {
    return (tip != null && TIPS[tip]) || '';
  }

  private showPart(name: string, status?: string): void {
    const part = this.parts.get(name);
    if (part == null || this.rules == null) return;
    const info = part.info;
    const extra = [
      info.warn ? `Warning: ${info.warn}.` : '',
      info.check ? `Check: ${info.check}.` : '',
    ]
      .filter(Boolean)
      .join(' ');
    const line =
      status ?? (isV01Part(name) ? this.rules.nextStep(name) : 'Not in this training yet.');
    this.say(label(name), `${this.tipText(info.tip)} ${extra}`.trim(), line);
  }

  private showControl(name: string): void {
    const c = this.controls.get(name);
    if (c == null || this.rules == null || !this.started) return;
    const body = c.info.motion === 'screw' ? SCREW_TIP : this.tipText(c.info.tip);
    this.say(label(name), [body, c.info.note].filter(Boolean).join(' '), this.stateWord(c));
  }

  private stateWord(c: ControlRuntime): string {
    const open = this.rules?.isOperated(c.info.name) ?? false;
    if (c.info.motion === 'screw') return open ? 'Undone.' : 'Tight.';
    if (c.info.motion === 'press') return open ? 'Pressed.' : 'Not pressed.';
    return open ? 'Open.' : 'Closed.';
  }

  /** Start lab (bottom of the safety page): unlock the tablet and the server. */
  private onStartLab(): void {
    if (!this.started) {
      this.ensureStarted();
      this.say('Ready', READY_TEXT, '');
    }
    this.tablet.unlock();
  }

  private ensureStarted(): void {
    if (this.started) return;
    this.started = true;
    this.phase = 'training';
    this.serverDrag = undefined;
    this.tablet.unlock();
    this.passDirty = true;
  }

  /** Server tab: Move server on/off (laser drag / grab the server). */
  private toggleMoveServer(): void {
    if (!this.started) return;
    this.phase = this.phase === 'place' ? 'training' : 'place';
    this.serverDrag = undefined;
    const moving = this.phase === 'place';
    this.tablet.setText('srv-move-label', moving ? 'Done moving' : 'Move server');
    this.tablet.setText('srv-status', moving ? MOVE_TEXT : '');
    this.passDirty = true;
  }

  // ------------------------------------------------------------ controls

  private onControl(name: string, byTool = false): void {
    const c = this.controls.get(name);
    if (c == null || this.rules == null) return;
    if (!this.started) {
      this.say('Safety first', START_TEXT, '');
      return;
    }
    // Screws only turn with the screwdriver (not the laser or a finger).
    if (c.info.motion === 'screw' && !byTool) {
      this.say(label(name), SCREW_TIP, 'Use the screwdriver.');
      return;
    }
    const owner = c.info.asset ?? this.ownerOf(name);
    if (owner != null && this.parts.get(owner)?.mode === 'gone') return;
    if (this.serverSlot != null && !/^caddy_\d+_/.test(name)) {
      this.say(label(name), '', RACKED_TEXT);
      return;
    }
    const socket = name.match(/^socket_(\d+)_plate$/);
    const k = socket != null ? Number(socket[1]) - 1 : -1;
    if (k >= 0 && this.rules.isOperated(name) && this.plateNeedsCycle.has(k)) {
      this.say(label(name), this.tipText(c.info.tip), 'Take the CPU out and put it back first.');
      return;
    }
    const result = this.rules.toggle(name);
    if (k >= 0 && result.ok && result.operated) this.plateNeedsCycle.add(k);
    if (!result.ok) {
      this.say(label(name), this.tipText(c.info.tip), result.reason ?? '');
      return;
    }
    this.syncControl(name);
    this.animateControl(c, result.operated ? 1 : 0);
    const pair = this.rules.partnerOf(name);
    const pc = pair != null ? this.controls.get(pair) : undefined;
    if (pair != null && pc != null) {
      this.syncControl(pair);
      this.animateControl(pc, result.operated ? 1 : 0);
    }
    // Caddy release button: the handle springs open with it.
    const caddy = name.match(/^caddy_(\d+)_button$/);
    const handle = caddy != null ? this.controls.get(`caddy_${caddy[1]}_handle`) : undefined;
    if (result.operated && handle != null && !this.rules.isOperated(handle.info.name)) {
      if (this.rules.toggle(handle.info.name).ok) {
        this.syncControl(handle.info.name);
        this.animateControl(handle, 1);
      }
    }
    this.say(label(name), this.stateWord(c), owner ? this.rules.nextStep(owner) : '');
  }

  /** Part whose `requires` lists this control (e.g. fan release tab). */
  private ownerOf(control: string): string | null {
    for (const part of this.parts.values()) {
      if (part.info.requires.includes(control)) return part.info.name;
    }
    return null;
  }

  private animateControl(c: ControlRuntime, target: number): void {
    const from = c.amount;
    if (from === target) return;
    const duration = c.info.motion === 'screw' ? 0.9 : 0.25;
    this.tweens.push({
      duration,
      elapsed: 0,
      update: (t) => this.setControlAmount(c, from + (target - from) * t),
    });
  }

  private setControlAmount(c: ControlRuntime, amount: number): void {
    c.amount = amount;
    const [, limit] = c.info.limits;
    const obj = c.object;
    if (c.info.motion === 'hinge' || c.info.motion === 'screw') {
      const angle = (limit * amount * Math.PI) / 180;
      obj.quaternion.setFromAxisAngle(c.axis, angle).multiply(c.restQuat);
    }
    if (c.info.motion === 'press' || c.info.motion === 'slide') {
      obj.position.copy(c.restPos).addScaledVector(c.axis, limit * amount);
    } else if (c.info.motion === 'screw') {
      obj.position.copy(c.restPos).addScaledVector(c.riseDir, c.info.rise * amount);
    }
  }

  // --------------------------------------------------------------- parts

  /** Why a grab of this part isn't allowed right now (undefined = allowed). */
  private grabRefusal(part: PartRuntime): string | undefined {
    const rules = this.rules;
    if (rules == null) return 'Loading.';
    if (!this.started) return START_TEXT;
    if (part.mode === 'gone') return 'Removed (debug).';
    if (part.busy) return 'Wait for it to settle.';
    if (part.mode === 'free') return undefined;
    if (this.serverSlot != null && !/^asset_(caddy|drive)_\d+$/.test(part.info.name)) return RACKED_TEXT;
    const loose = rules.childrenOf(part.info.name).find((c) => !rules.isFitted(c));
    if (loose != null) return `Put the ${label(loose)} back in first.`;
    const remove = rules.canRemove(part.info.name);
    return remove.ok ? undefined : remove.reason;
  }

  private onGrabStart(entity: Entity): void {
    const part = this.partOf(entity);
    if (part == null) return;
    const holder = this.world.getSystem(GrabSystem)?.getHolderHand(entity);
    const refusal =
      holder === 'left' && this.toolOffset != null
        ? 'Your left hand is the screwdriver. Grab with the right.'
        : this.grabRefusal(part);
    if (refusal != null) {
      part.denied = true;
      this.world.getSystem(GrabSystem)?.forceRelease(entity);
      part.object.position.copy(part.restPos);
      part.object.quaternion.copy(part.restQuat);
      if (part.mode !== 'gone') this.showPart(part.info.name, refusal);
      return;
    }
    part.denied = false;
    if (part.mode === 'fitted') {
      this.setMode(part, 'seated');
      part.stage = 0;
    }
    this.showPart(part.info.name);
  }

  /** Keep a seated part on its pull path; free it at the end. */
  private followPath(part: PartRuntime): void {
    const obj = part.object;
    obj.quaternion.copy(part.restQuat);
    const last = part.path.length - 1;
    if (last < 1) {
      this.freePart(part);
      return;
    }
    // Snap to the closest point on the whole path (not just the current
    // segment), so pulling "up" on the lid also does its 15 mm slide back.
    const raw = this.tmp2.copy(obj.position);
    let bestDist = Infinity;
    let bestStage = 0;
    let bestT = 0;
    for (let i = 0; i < last; i++) {
      const a = part.path[i];
      const seg = this.tmp.copy(part.path[i + 1]).sub(a);
      const len2 = seg.lengthSq();
      const t = len2 > 0 ? Math.min(1, Math.max(0, raw.clone().sub(a).dot(seg) / len2)) : 1;
      const d = a.clone().addScaledVector(seg, t).distanceToSquared(raw);
      if (d < bestDist) {
        bestDist = d;
        bestStage = i;
        bestT = t;
      }
    }
    // Short paths (a drive in its caddy is 15 mm): pulling clearly away in
    // any direction breaks it free instead of fighting the tiny slide.
    let length = 0;
    for (let i = 0; i < last; i++) length += part.path[i].distanceTo(part.path[i + 1]);
    if (length < SHORT_PATH && Math.sqrt(bestDist) > BREAK_FREE) {
      this.freePart(part);
      return;
    }
    const a = part.path[bestStage];
    const seg = this.tmp.copy(part.path[bestStage + 1]).sub(a);
    obj.position.copy(a).addScaledVector(seg, bestT);
    part.stage = bestStage;
    if (bestStage === last - 1 && bestT >= PATH_END) this.freePart(part);
  }

  private freePart(part: PartRuntime): void {
    if (this.rules == null) return;
    this.setMode(part, 'free');
    this.rules.markRemoved(part.info.name);
    this.say(
      label(part.info.name),
      'Out. Move it anywhere; bring it back to its slot to refit.',
      part.info.warn ? `Warning: ${part.info.warn}.` : '',
    );
  }

  /**
   * Room: a released part that didn't go back in falls straight down onto
   * whatever is below it (table, floor, rack, cabinet, server) and stays
   * inside the room.
   */
  private dropPart(part: PartRuntime): void {
    if (part.mode !== 'free' || part.busy) return;
    this.dropObject(part.object, part);
  }

  /** Fall straight down onto the first surface below (room only). */
  private dropObject(obj: Object3D, part?: PartRuntime): void {
    if (this.setting !== 'room') return;
    obj.updateWorldMatrix(true, true);
    const box = new Box3().setFromObject(obj);
    const pos = obj.getWorldPosition(new Vector3());
    const bottom = pos.y - box.min.y;
    pos.x = Math.min(ROOM_HALF, Math.max(-ROOM_HALF, pos.x));
    pos.z = Math.min(ROOM_HALF, Math.max(-ROOM_HALF, pos.z));
    const targets: Object3D[] = [];
    if (this.lab != null) targets.push(this.lab);
    const server = this.serverEntity?.object3D;
    if (server != null) targets.push(server);
    this.raycaster.set(new Vector3(pos.x, box.min.y + 0.005, pos.z), new Vector3(0, -1, 0));
    let floorY = 0;
    for (const hit of this.raycaster.intersectObjects(targets, true)) {
      let mine = false;
      let shown = true;
      for (let o: Object3D | null = hit.object; o != null; o = o.parent) {
        if (o === obj) mine = true;
        if (!o.visible) shown = false;
      }
      const mat = (hit.object as Mesh).material as Material | undefined;
      if (mine || !shown || mat?.visible === false) continue;
      floorY = hit.point.y;
      break;
    }
    const end = new Vector3(pos.x, floorY + bottom, pos.z);
    const start = obj.getWorldPosition(new Vector3());
    const parent = obj.parent;
    if (parent == null) return;
    parent.updateWorldMatrix(true, false);
    const from = parent.worldToLocal(start.clone());
    const to = parent.worldToLocal(end.clone());
    const height = Math.max(0, start.y - end.y);
    if (part != null) part.busy = true;
    this.tweens.push({
      duration: Math.max(0.05, Math.sqrt((2 * height) / 9.81)),
      elapsed: 0,
      update: (t) => obj.position.copy(from).lerp(to, t * t),
      done: () => {
        if (part != null) part.busy = false;
      },
    });
  }

  private onGrabEnd(entity: Entity): void {
    const part = this.partOf(entity);
    if (part == null) return;
    // The grab handle drops the stick zoom / smoothing on release: keep the
    // part where the user last saw it.
    const last = this.lastHeld.get(part.info.name);
    if (last != null && part.mode === 'free' && !part.denied) part.object.position.copy(last);
    this.lastHeld.delete(part.info.name);
    this.releasePart(part);
    this.dropPart(part);
  }

  /** A held part was let go (laser or hand). */
  private releasePart(part: PartRuntime): void {
    this.smooth.delete(part.info.name);
    this.zoom.delete(part.info.name);
    if (this.rules == null) return;
    if (part.denied) {
      part.denied = false;
      part.object.position.copy(part.restPos);
      part.object.quaternion.copy(part.restQuat);
      return;
    }
    if (part.mode === 'seated') {
      // Let go before it was out: it slides back home.
      this.slideHome(part, false);
      return;
    }
    if (part.mode !== 'free') return;
    if (part.group != null) {
      const best = this.snapSlot(part);
      if (best < 0) return;
      if (this.occupant(part.group, best, part) != null) {
        this.say(label(part.info.name), "Can't refit here.", 'That slot already has a part in it.');
        return;
      }
      if (part.group === 'hs') {
        const cpu = this.occupant('cpu', best);
        if (cpu == null || cpu.mode !== 'fitted') {
          this.say(label(part.info.name), "Can't refit here.", 'Fit a CPU in that socket first.');
          return;
        }
        const block = this.socketBlock(best, false);
        if (block != null) {
          this.say(label(part.info.name), "Can't refit yet.", block);
          return;
        }
      }
      this.assignSlot(part, best);
    } else if (this.pathDistance(part.path, part.object.position).dist > SNAP_DISTANCE) {
      return;
    }
    const refit = this.rules.canRefit(part.info.name);
    if (!refit.ok) {
      this.say(label(part.info.name), "Can't refit yet.", refit.reason ?? '');
      return;
    }
    this.slideHome(part, true);
  }

  /**
   * Swappable part: the slot whose slide-in path (anywhere from fully out to
   * home) passes closest to the part, within SNAP_DISTANCE; -1 if none.
   */
  private snapSlot(part: PartRuntime): number {
    const slots = part.group != null ? (this.slots.get(part.group) ?? []) : [];
    const steps = part.path.slice(1).map((p, i) => p.clone().sub(part.path[i]));
    let best = -1;
    let bestDist = SNAP_DISTANCE;
    slots.forEach((slot, i) => {
      const path = [slot.pos.clone()];
      for (const step of steps) path.push(path[path.length - 1].clone().add(step));
      const d = this.pathDistance(path, part.object.position).dist;
      if (d < bestDist) {
        bestDist = d;
        best = i;
      }
    });
    return best;
  }

  /** Closest point on a polyline path: distance, segment index and point. */
  private pathDistance(path: Vector3[], p: Vector3): { dist: number; seg: number; point: Vector3 } {
    let best = { dist: Infinity, seg: 0, point: path[0].clone() };
    for (let i = 0; i < path.length - 1; i++) {
      const a = path[i];
      const ab = path[i + 1].clone().sub(a);
      const len2 = ab.lengthSq();
      const t = len2 > 0 ? Math.min(1, Math.max(0, p.clone().sub(a).dot(ab) / len2)) : 0;
      const point = a.clone().addScaledVector(ab, t);
      const dist = point.distanceTo(p);
      if (dist < best.dist) best = { dist, seg: i, point };
    }
    if (path.length === 1) best.dist = path[0].distanceTo(p);
    return best;
  }

  /** Line up on the slide-in path, then slide in along it to the slot. */
  private slideHome(part: PartRuntime, fromFree: boolean): void {
    part.busy = true;
    const obj = part.object;
    const startPos = obj.position.clone();
    const startQuat = obj.quaternion.clone();
    let points: Vector3[];
    if (fromFree) {
      // Join the path where the part is (a drive pushed nearly home doesn't
      // jump back out first), then follow it in.
      const near = this.pathDistance(part.path, startPos);
      points = [near.point, ...part.path.slice(0, near.seg + 1).reverse()];
    } else {
      points = part.path.slice(0, part.stage + 1).reverse();
    }
    const steps: { from: Vector3; to: Vector3; lineUp: boolean }[] = [];
    let prev = startPos;
    for (const p of points) {
      steps.push({ from: prev, to: p, lineUp: steps.length === 0 });
      prev = p;
    }
    const run = (i: number) => {
      if (i >= steps.length) {
        this.finishFit(part, fromFree);
        return;
      }
      const step = steps[i];
      const dist = step.from.distanceTo(step.to);
      this.tweens.push({
        duration: Math.max(0.12, Math.min(0.5, dist * 4)),
        elapsed: 0,
        update: (t) => {
          obj.position.copy(step.from).lerp(step.to, t);
          if (step.lineUp) obj.quaternion.copy(startQuat).slerp(part.restQuat, t);
        },
        done: () => run(i + 1),
      });
    };
    run(0);
  }

  private finishFit(part: PartRuntime, fromFree: boolean): void {
    if (this.rules == null) return;
    if (fromFree && part.group === 'cpu' && part.slot != null) this.plateNeedsCycle.delete(part.slot);
    part.object.position.copy(part.restPos);
    part.object.quaternion.copy(part.restQuat);
    this.setMode(part, 'fitted');
    part.stage = 0;
    part.busy = false;
    if (!fromFree) return;
    for (const name of this.rules.markFitted(part.info.name)) {
      const c = this.controls.get(name);
      if (c != null) this.animateControl(c, 0);
      this.syncControl(name);
    }
    const check = part.info.check ? `Check: ${part.info.check}.` : '';
    this.say(label(part.info.name), `Refitted. ${check}`.trim(), this.refitNext(part));
  }

  /** After refit: which of its controls still need closing/tightening. */
  private refitNext(part: PartRuntime): string {
    const rules = this.rules;
    if (rules == null) return '';
    const open = part.info.requires.filter(
      (t) => this.controls.has(t) && rules.isOperated(t),
    );
    if (open.length === 0) return 'Secured.';
    const verb = (t: string) =>
      this.controls.get(t)?.info.motion === 'screw' ? 'tighten' : 'close';
    return `Now ${open.map((t) => `${verb(t)} ${label(t)}`).join(', ')}.`;
  }

  // ------------------------------------------------------------- reset

  private resetServer(): void {
    if (this.rules == null) return;
    const grab = this.world.getSystem(GrabSystem);
    this.tweens = [];
    for (const part of this.parts.values()) {
      if (part.entity.hasComponent(Grabbed)) grab?.forceRelease(part.entity);
      if (part.homeSlot != null) this.assignSlot(part, part.homeSlot);
      part.object.position.copy(part.restPos);
      part.object.quaternion.copy(part.restQuat);
      part.object.visible = true;
      this.setMode(part, 'fitted');
      part.stage = 0;
      part.busy = false;
      part.denied = false;
    }
    this.rules.reset();
    this.labRoom.reset();
    this.plateNeedsCycle.clear();
    this.refreshSockets();
    const root = this.serverEntity?.object3D?.getObjectByName('server_root');
    if (root != null) this.hideCables(root);
    for (const c of this.controls.values()) {
      this.setControlAmount(c, 0);
      this.syncControl(c.info.name);
    }
    this.exploded = false;
    this.removedSet = false;
    this.controlsOpen = false;
    this.serverSlot = undefined;
    this.carry = undefined;
    this.sideHold.clear();
    this.placePending = true;
    this.setDebugLabels();
    this.debugSay('Reset: everything back in place.');
    this.say('Server reset', READY_TEXT, '');
  }

  // ------------------------------------------------- placement (XR start)

  /** On entering XR: server within reach and the tablet in front. */
  private tryPlaceAll(): void {
    const view = this.headView();
    if (view == null) return;
    this.placePending = false;
    this.applySetting();
    const viewOnly = this.viewOnly;
    this.viewOnly = false;
    if (this.setting === 'room') this.placeInRoom(!viewOnly);
    else {
      this.serverSlot = undefined;
      this.placeServer();
    }
    const screen = this.tablet.screen;
    const after = this.headView() ?? view;
    if (screen != null) {
      // In front, a little to the left and low (like holding it), so the
      // server stays visible.
      const pos = after.headPos
        .clone()
        .addScaledVector(after.forward, 0.25)
        .addScaledVector(after.right, -0.5);
      pos.y = after.headPos.y - 0.35;
      this.facePanel(screen, pos, after.headPos, -35);
    }
  }

  /** Head position + flat forward / right, or undefined before tracking. */
  private headView(): { headPos: Vector3; forward: Vector3; right: Vector3 } | undefined {
    const head = this.player.head;
    head.updateWorldMatrix(true, false);
    const headPos = new Vector3().setFromMatrixPosition(head.matrixWorld);
    if (headPos.y < 0.3) return undefined;
    const forward = new Vector3(0, 0, -1).applyQuaternion(
      head.getWorldQuaternion(new Quaternion()),
    );
    forward.y = 0;
    if (forward.lengthSq() < 1e-6) forward.set(0, 0, -1);
    forward.normalize();
    const right = new Vector3().crossVectors(forward, new Vector3(0, 1, 0)).normalize();
    return { headPos, forward, right };
  }

  /** Server at chest height, 0.45 m ahead, front facing the user. */
  /** Lab room: doors / drawers and the prop screwdriver in drawer 1. */
  private updateLab(delta: number): void {
    if (this.labState === 'waiting') {
      const lab = this.world.getSceneObject('lab');
      const labEntity = this.world.getSceneEntity('lab');
      if (lab == null || labEntity == null || this.tool == null) return;
      this.labState = 'loading';
      this.lab = lab;
      labEntity.addComponent(RayInteractable);
      this.labRoom
        .init(lab, `${import.meta.env.BASE_URL}gltf/lab/lab_manifest.json`, this.tool)
        .then(() => {
          const prop = this.labRoom.prop;
          if (prop != null) {
            this.propEntity = this.world.createTransformEntity(prop);
            this.propEntity.addComponent(DistanceGrabbable, {
              movementMode: MovementMode.MoveFromTarget,
              rotate: true,
              translate: true,
              scale: false,
            });
            this.labRoom.placeProp();
          }
          this.labRoom.onBlankOut = (obj) => this.dropObject(obj);
          this.labState = 'ready';
          this.applySetting();
          // Browser (flat) view: show the server on the island table.
          const server = this.serverEntity?.object3D;
          const table = lab.getObjectByName('slot_island_server');
          if (this.world.visibilityState.peek() === VisibilityState.NonImmersive && server != null && table != null) {
            this.setWorldPose(server, table.getWorldPosition(new Vector3()), 0, 0);
          }
        });
      return;
    }
    if (this.labState !== 'ready') return;
    this.labRoom.update(delta);
    // Prop screwdriver: picked up leaves the drawer; let go falls (room).
    const held = this.propEntity?.hasComponent(Grabbed) ?? false;
    const prop = this.labRoom.prop;
    if (held && !this.propHeld) this.labRoom.releaseProp();
    if (!held && this.propHeld && prop != null) this.dropObject(prop);
    this.propHeld = held;
  }

  /** Show / hide the lab and passthrough for the current setting. */
  private applySetting(): void {
    if (this.lab == null) this.lab = this.world.getSceneObject('lab') ?? undefined;
    const labEntity = this.world.getSceneEntity('lab');
    if (labEntity != null) {
      const solid = labEntity.hasComponent(LocomotionEnvironment);
      if (this.setting === 'room' && !solid) labEntity.addComponent(LocomotionEnvironment, { type: 'static' });
      if (this.setting !== 'room' && solid) labEntity.removeComponent(LocomotionEnvironment);
    }
    if (this.lab != null) {
      this.lab.visible = this.setting === 'room';
      (this.lab as Object3D & { pointerEvents?: string }).pointerEvents =
        this.setting === 'room' ? undefined : 'none';
    }
    const prop = this.labRoom.prop;
    if (prop != null) {
      prop.visible = this.setting === 'room';
      (prop as Object3D & { pointerEvents?: string }).pointerEvents =
        this.setting === 'room' ? undefined : 'none';
    }
    // An opaque background hides passthrough (room and black).
    this.world.scene.background = this.setting === 'ar' ? null : new Color(0x000000);
  }

  /** Menu: switch Room / AR / Black and put everything back in place. */
  private setSetting(setting: 'room' | 'ar' | 'black'): void {
    this.setting = setting;
    this.placePending = true;
  }

  /**
   * Room: the server sits on the island table and the user stands at its
   * south side, facing it (north). Moves the player, not the room.
   */
  private placeInRoom(moveServer = true): void {
    const server = this.serverEntity?.object3D;
    const slot = this.lab?.getObjectByName('slot_island_server');
    if (server == null || slot == null) {
      this.placeServer();
      return;
    }
    const slotPos = slot.getWorldPosition(new Vector3());
    if (moveServer) this.startServerInRack(server, slotPos);
    this.standAtTable(slotPos);
  }

  /** Session start: the server is racked in START_RACK_SLOT, its blanks out. */
  private startServerInRack(server: Object3D, tablePos: Vector3): void {
    // The session starts with the server racked: its two blanking panels are
    // out and it sits in the slot, front facing east (towards the table).
    const rack = this.labRoom.slots.find((r) => r.name === START_RACK_SLOT);
    if (rack != null) {
      this.labRoom.hideBlanks(rack);
      this.setWorldPose(server, rack.obj.getWorldPosition(new Vector3()), Math.PI / 2, 0);
      this.serverSlot = rack;
    } else {
      this.setWorldPose(server, tablePos.clone(), 0, 0);
    }
  }

  /** Move the player to stand south of the island table, facing it. */
  private standAtTable(slotPos: Vector3): void {
    // Turn the player so the head faces -Z (north), then move it to stand
    // ROOM_STAND m south of the table slot.
    const head = this.player.head;
    head.updateWorldMatrix(true, false);
    const headPos = new Vector3().setFromMatrixPosition(head.matrixWorld);
    const fwd = new Vector3(0, 0, -1).applyQuaternion(head.getWorldQuaternion(new Quaternion()));
    const yaw = Math.atan2(-fwd.x, -fwd.z); // 0 = facing -Z
    const turn = new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), -yaw);
    const p = this.player;
    p.position.sub(headPos).applyQuaternion(turn).add(headPos);
    p.quaternion.premultiply(turn);
    p.updateWorldMatrix(true, true);
    const now = new Vector3().setFromMatrixPosition(head.matrixWorld);
    const target = p.position.clone();
    target.x += slotPos.x - now.x;
    target.z += slotPos.z + ROOM_STAND - now.z;
    // Locomotion owns the player position: move it through the system.
    const loco = this.world.getSystem(LocomotionSystem);
    if (loco != null) loco.setPlayerPosition(target);
    else p.position.copy(target);
    p.updateWorldMatrix(true, true);
  }

  private placeServer(): void {
    const view = this.headView();
    const server = this.serverEntity?.object3D;
    if (view == null || server == null) return;
    const pos = view.headPos.clone().addScaledVector(view.forward, 0.45);
    pos.y = view.headPos.y - 0.55;
    this.setWorldPose(server, pos, Math.atan2(-view.forward.x, -view.forward.z), 0);
  }

  private facePanel(obj: Object3D, pos: Vector3, headPos: Vector3, pitchDeg: number): void {
    const yaw = Math.atan2(headPos.x - pos.x, headPos.z - pos.z);
    this.setWorldPose(obj, pos, yaw, pitchDeg);
  }

  /** Set world position + yaw (and pitch) for an object. */
  private setWorldPose(obj: Object3D, pos: Vector3, yaw: number, pitchDeg: number): void {
    const q = new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), yaw);
    if (pitchDeg !== 0) {
      q.multiply(
        new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), (pitchDeg * Math.PI) / 180),
      );
    }
    const parent = obj.parent;
    if (parent != null) {
      parent.updateWorldMatrix(true, false);
      parent.worldToLocal(pos);
      q.premultiply(parent.getWorldQuaternion(new Quaternion()).invert());
    }
    obj.position.copy(pos);
    obj.quaternion.copy(q);
  }

  // ---------------------------------------------------------- debug panel

  private debugSay(text: string): void {
    this.tablet.setText('dbg-status', text);
  }

  private setDebugLabel(id: string, text: string): void {
    this.tablet.setText(`${id}-label`, text);
  }

  private setDebugLabels(): void {
    const lid = this.parts.get('asset_lid');
    this.setDebugLabel('dbg-lid', lid?.mode === 'gone' ? 'Lid back' : 'Lid off');
    this.setDebugLabel('dbg-remove', this.removedSet ? 'Refit all' : 'Remove one of each');
    this.setDebugLabel('dbg-controls', this.controlsOpen ? 'Close all controls' : 'Open all controls');
    this.tablet.setText('exp-all-label', this.exploded ? 'Assemble all' : 'Explode all');
    this.setDebugLabel('dbg-slots', this.slotMarkers.some((m) => m.visible) ? 'Hide slots' : 'Show slots');
    this.setDebugLabel('dbg-teleport', this.movement ? 'Movement: on' : 'Movement: off');
  }

  private setControl(name: string, operated: boolean): void {
    const c = this.controls.get(name);
    if (c == null || this.rules == null) return;
    this.rules.forceOperated(name, operated);
    this.syncControl(name);
    this.animateControl(c, operated ? 1 : 0);
  }

  /** Open a part's own tabs/screws (debug). */
  private openRequires(part: PartRuntime): void {
    for (const token of part.info.requires) {
      if (this.controls.has(token)) this.setControl(token, true);
    }
  }

  /** Take a part out (rules skipped) and tween it to `local` (parent space). */
  private forceOut(part: PartRuntime, local: Vector3): void {
    if (this.rules == null) return;
    this.openRequires(part);
    this.rules.forceFitted(part.info.name, false);
    this.setMode(part, 'free');
    part.object.quaternion.copy(part.restQuat);
    const from = part.object.position.clone();
    this.tweens.push({
      duration: 0.4,
      elapsed: 0,
      update: (t) => part.object.position.copy(from).lerp(local, t),
    });
  }

  /** Put a part straight back in its slot (rules skipped). */
  private forceIn(part: PartRuntime): void {
    if (this.rules == null) return;
    part.object.position.copy(part.restPos);
    part.object.quaternion.copy(part.restQuat);
    part.object.visible = true;
    this.setMode(part, 'fitted');
    part.stage = 0;
    for (const name of this.rules.markFitted(part.info.name)) {
      const c = this.controls.get(name);
      if (c != null) this.animateControl(c, 0);
      this.syncControl(name);
    }
  }

  /** Debug lid: removed completely (hidden) until Lid back / Reset. */
  private dbgLid(): void {
    const lid = this.parts.get('asset_lid');
    if (lid == null || this.rules == null) return;
    if (lid.mode === 'gone') {
      this.forceIn(lid);
      this.debugSay('Lid back on.');
    } else {
      this.world.getSystem(GrabSystem)?.forceRelease(lid.entity);
      this.openRequires(lid);
      this.rules.forceFitted('asset_lid', false);
      this.setMode(lid, 'gone');
      lid.object.visible = false;
      this.debugSay('Lid removed.');
    }
    this.setDebugLabels();
  }

  private dbgRemove(): void {
    if (this.removedSet) {
      this.resetServer();
      return;
    }
    const names = [
      'asset_caddy_01',
      'asset_fan_01',
      'asset_dimm_01',
      'asset_hs_1',
      'asset_cpu_1',
      'asset_nic',
      'asset_accel',
    ];
    const lid = this.parts.get('asset_lid');
    if (lid != null && lid.mode !== 'gone') this.dbgLid();
    let slot = 0;
    for (const name of names) {
      const part = this.parts.get(name);
      if (part == null || part.mode !== 'fitted') continue;
      // A "mat" to the right of the server, in server space.
      const col = slot % 3;
      const row = Math.floor(slot / 3);
      slot++;
      this.forceOut(part, new Vector3(0.36 + col * 0.16, 0, -0.08 - row * 0.2));
    }
    const drive = this.parts.get('asset_drive_01');
    if (drive != null && drive.mode === 'fitted') {
      this.forceOut(drive, drive.restPos.clone().add(new Vector3(0.1, 0, 0)));
    }
    this.removedSet = true;
    this.debugSay('One of each part removed (right of the server).');
    this.setDebugLabels();
  }

  private dbgControls(): void {
    this.controlsOpen = !this.controlsOpen;
    for (const name of this.controls.keys()) {
      if (isV01Control(name)) this.setControl(name, this.controlsOpen);
    }
    this.debugSay(this.controlsOpen ? 'All controls opened.' : 'All controls closed.');
    this.setDebugLabels();
  }

  /**
   * Exploded view: every fitted v0.1 part flies well out along its pull
   * direction and counts as removed, so it can be grabbed and refitted.
   */
  /** Explode tab: all, or one kind of part. A second press assembles them. */
  private explode(which: string): void {
    if (this.rules == null) return;
    const match = which === 'all' ? undefined : EXPLODE_GROUPS[which];
    const chosen = [...this.parts.values()].filter(
      (p) => isV01Part(p.info.name) && p.mode !== 'gone' && (match == null || match.test(p.info.name)),
    );
    // Explode if any of them is still in place; otherwise put them back.
    const out = chosen.some((p) => p.mode === 'fitted');
    for (const part of chosen) {
      if (out) {
        if (part.mode !== 'fitted') continue;
        const end = part.path[part.path.length - 1];
        const pull = end.clone().sub(part.restPos);
        const dir = pull.lengthSq() > 0 ? pull.clone().normalize() : new Vector3(0, 1, 0);
        const distance = pull.length() * 4 + 0.15;
        const target = part.restPos.clone().addScaledVector(dir, distance);
        if (part.info.name === 'asset_lid') target.y += 0.35;
        this.forceOut(part, target);
      } else if (part.mode === 'free') {
        this.forceIn(part);
      }
    }
    if (which === 'all') this.exploded = out;
    this.tablet.setText('exp-all-label', this.exploded ? 'Assemble all' : 'Explode all');
    this.tablet.setText(
      'exp-status',
      out ? 'Exploded: grab any part; release near a slot to refit.' : 'Assembled.',
    );
  }

  private dbgSlots(): void {
    if (this.slotMarkers.length === 0) this.createSlotMarkers();
    const show = !this.slotMarkers.some((m) => m.visible);
    for (const m of this.slotMarkers) m.visible = show;
    this.debugSay(show ? 'Green dots = where each part snaps back.' : 'Slots hidden.');
    this.setDebugLabels();
  }

  private createSlotMarkers(): void {
    const geometry = new SphereGeometry(0.008, 12, 8);
    const material = new MeshBasicMaterial({
      color: 0x22ff66,
      depthTest: false,
      transparent: true,
      opacity: 0.85,
    });
    for (const part of this.parts.values()) {
      if (!isV01Part(part.info.name) || part.object.parent == null) continue;
      const marker = new Mesh(geometry, material);
      marker.renderOrder = 999;
      marker.position.copy(part.restPos);
      marker.visible = false;
      part.object.parent.add(marker);
      this.slotMarkers.push(marker);
    }
  }

  private dbgMovement(): void {
    this.movement = !this.movement;
    const systems = [
      this.world.getSystem(TeleportSystem),
      this.world.getSystem(SlideSystem),
      this.world.getSystem(TurnSystem),
    ];
    for (const instance of systems) {
      if (instance == null) continue;
      if (this.movement) instance.play();
      else instance.stop();
    }
    this.debugSay(
      this.movement
        ? 'Movement on: left stick walks, right stick teleports / turns.'
        : 'Movement off.',
    );
    this.setDebugLabels();
  }

  /** Right-stick teleport/turn off while it's zooming a held server. */
  private setStickTurning(on: boolean): void {
    const enable = on && this.movement;
    for (const instance of [this.world.getSystem(TeleportSystem), this.world.getSystem(TurnSystem)]) {
      if (instance == null) continue;
      if (enable && instance.isPaused) instance.play();
      else if (!enable && !instance.isPaused) instance.stop();
    }
  }

  /** Move the server: `along` = away from the user (m), `up` = height (m). */
  private dbgNudge(along: number, up: number): void {
    const server = this.serverEntity?.object3D;
    if (server == null) return;
    const head = this.player.head;
    head.updateWorldMatrix(true, false);
    const headPos = new Vector3().setFromMatrixPosition(head.matrixWorld);
    const serverPos = server.getWorldPosition(new Vector3());
    const away = serverPos.clone().sub(headPos);
    away.y = 0;
    if (away.lengthSq() < 1e-6) away.set(0, 0, -1);
    away.normalize();
    serverPos.addScaledVector(away, along);
    serverPos.y += up;
    if (server.parent != null) server.parent.worldToLocal(serverPos);
    server.position.copy(serverPos);
    this.debugSay(`Server moved (height ${server.getWorldPosition(new Vector3()).y.toFixed(2)} m).`);
  }

  /** Turn the server 90° around its middle (to see the back). */
  private dbgRotate(): void {
    const server = this.serverEntity?.object3D;
    if (server == null) return;
    const center = new Vector3(0, 0.045, -0.32); // middle of the 2U body
    server.updateMatrixWorld(true);
    const before = server.localToWorld(center.clone());
    server.quaternion.premultiply(
      new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), Math.PI / 2),
    );
    server.updateMatrixWorld(true);
    const after = server.localToWorld(center.clone());
    const shift = before.sub(after);
    if (server.parent != null) {
      shift.applyQuaternion(server.parent.getWorldQuaternion(new Quaternion()).invert());
    }
    server.position.add(shift);
    this.debugSay('Server rotated 90°.');
  }

  // ------------------------------------------------- hands / near grab

  /** Finger poke only while hands are tracked (keeps the laser up close). */
  private updateInputMode(): void {
    const hands =
      this.input.xr.isPrimary('hand', 'left') || this.input.xr.isPrimary('hand', 'right');
    if (hands === this.pokeOn) return;
    this.pokeOn = hands;
    // Tablet buttons: fingertip presses with hands (laser keeps working up
    // close with controllers).
    const labEntity = this.world.getSceneEntity('lab');
    if (labEntity != null) {
      if (hands) labEntity.addComponent(PokeInteractable);
      else if (labEntity.hasComponent(PokeInteractable)) labEntity.removeComponent(PokeInteractable);
    }
    const tablet = this.world.getSceneEntity('tablet');
    if (tablet != null) {
      if (hands) tablet.addComponent(PokeInteractable);
      else if (tablet.hasComponent(PokeInteractable)) tablet.removeComponent(PokeInteractable);
    }
    for (const c of this.controls.values()) {
      if (!isV01Control(c.info.name)) continue;
      if (hands) c.entity.addComponent(PokeInteractable);
      else if (c.entity.hasComponent(PokeInteractable)) c.entity.removeComponent(PokeInteractable);
    }
  }

  /** Pinch (hands) or grip (controllers) near a part to pull it; near the server to move it while placing. */
  private updateNearGrabs(delta: number): void {
    this.updateNearGrabsHands(delta);
    if (this.carry == null && this.sideHold.size === 2) this.beginCarry();
    if (this.carry != null) this.updateCarry(delta);
  }

  private updateNearGrabsHands(delta: number): void {
    for (const hand of ['left', 'right'] as const) {
      const isHand = this.input.xr.isPrimary('hand', hand);
      const pad = this.input.xr.gamepads[hand];
      if (pad == null) continue;
      const start = isHand ? pad.getSelectStart() : pad.getButtonDown(InputComponent.Squeeze);
      const end = isHand ? pad.getSelectEnd() : pad.getButtonUp(InputComponent.Squeeze);
      const held = this.nearGrabs.get(hand);
      const handMatrix = this.handMatrix(hand, isHand);
      if (held != null) {
        if (end) {
          this.nearGrabs.delete(hand);
          if (held.part != null) {
            this.releasePart(held.part);
            this.dropPart(held.part);
          }
        } else {
          this.moveNearGrab(held, held.wrist ? this.wristMatrix(hand) : handMatrix, delta);
        }
        continue;
      }
      // Server: both hands on its sides carry it (room).
      if (this.sideHold.has(hand)) {
        if (end) {
          this.sideHold.delete(hand);
          if (this.carry != null) this.endCarry();
        }
        continue;
      }
      if (start && this.setting === 'room' && this.onServerSide(new Vector3().setFromMatrixPosition(handMatrix))) {
        this.sideHold.add(hand);
        if (this.sideHold.size < 2) this.say('Server', 'Lift with both hands: one on each side.', '');
        continue;
      }
      // The left hand is the screwdriver: only the right hand grabs up close.
      if (start && hand === 'right') {
        this.tryNearGrab(hand, handMatrix, isHand ? REACH_HAND : REACH_CONTROLLER, isHand);
      }
    }
  }

  // ----------------------------------------------- server: two-hand carry

  /** Is this point on the left or right side of the server (a lifting grip)? */
  private onServerSide(p: Vector3): boolean {
    const server = this.serverEntity?.object3D;
    const box = this.serverBox;
    if (server == null || box == null) return false;
    server.updateWorldMatrix(true, false);
    const local = server.worldToLocal(p.clone());
    const half = (box.max.x - box.min.x) / 2;
    const cx = (box.max.x + box.min.x) / 2;
    const side = Math.abs(local.x - cx);
    return (
      side > half - 0.06 &&
      side < half + 0.12 &&
      local.y > box.min.y - 0.08 &&
      local.y < box.max.y + 0.1 &&
      local.z > box.min.z - 0.05 &&
      local.z < box.max.z - 0.06 // not the front (drive caddies sit there)
    );
  }

  /** Both hands' positions as a frame: midpoint, and yaw from left to right hand. */
  private carryFrame(): { mid: Vector3; yaw: number } {
    const isL = this.input.xr.isPrimary('hand', 'left');
    const isR = this.input.xr.isPrimary('hand', 'right');
    const l = new Vector3().setFromMatrixPosition(this.handMatrix('left', isL));
    const r = new Vector3().setFromMatrixPosition(this.handMatrix('right', isR));
    const mid = l.clone().add(r).multiplyScalar(0.5);
    const dir = r.sub(l);
    return { mid, yaw: Math.atan2(-dir.z, dir.x) };
  }

  /** Both hands on the sides: lift the server (out of a rack if racked). */
  private beginCarry(): void {
    const server = this.serverEntity?.object3D;
    if (server == null) return;
    const f = this.carryFrame();
    const pos = server.getWorldPosition(new Vector3());
    const fwd = new Vector3(0, 0, 1).applyQuaternion(server.getWorldQuaternion(new Quaternion()));
    const yaw = Math.atan2(fwd.x, fwd.z);
    const offset = pos.sub(f.mid).applyAxisAngle(new Vector3(0, 1, 0), -f.yaw);
    this.carry = { offset, yawOffset: yaw - f.yaw };
    if (this.serverSlot != null) {
      this.serverSlot = undefined;
      this.say('Server', 'Out of the rack. Carry it to the table (it only turns left / right).', '');
    }
  }

  /** Follow both hands: position + turn left / right only (never tips). */
  private updateCarry(delta: number): void {
    const server = this.serverEntity?.object3D;
    const carry = this.carry;
    if (server == null || carry == null) return;
    const f = this.carryFrame();
    const pos = carry.offset.clone().applyAxisAngle(new Vector3(0, 1, 0), f.yaw).add(f.mid);
    const cur = server.getWorldPosition(new Vector3());
    pos.copy(cur.lerp(pos, 1 - Math.exp(-delta * SMOOTHING)));
    this.setWorldPose(server, pos, f.yaw + carry.yawOffset, 0);
  }

  /** Let go: into a rack slot if lined up (blanks out), else down onto a surface. */
  private endCarry(): void {
    const server = this.serverEntity?.object3D;
    this.carry = undefined;
    if (server == null) return;
    const pos = server.getWorldPosition(new Vector3());
    const fwd = new Vector3(0, 0, 1).applyQuaternion(server.getWorldQuaternion(new Quaternion()));
    const facingEast = fwd.x > Math.cos((RACK_ANGLE * Math.PI) / 180);
    let best: RackSlot | undefined;
    let bestDist = RACK_REACH;
    for (const slot of this.labRoom.slots) {
      const d = slot.obj.getWorldPosition(new Vector3()).distanceTo(pos);
      if (d < bestDist) {
        bestDist = d;
        best = slot;
      }
    }
    if (best != null && facingEast) {
      const missing = best.blanks.filter((b) => !this.labRoom.blanksOut.has(b));
      if (missing.length === 0) {
        const slot = best;
        const target = slot.obj.getWorldPosition(new Vector3());
        const from = pos.clone();
        this.tweens.push({
          duration: 0.4,
          elapsed: 0,
          update: (t) => this.setWorldPose(server, from.clone().lerp(target, t), Math.PI / 2, 0),
        });
        this.serverSlot = slot;
        this.say('Server', 'Racked.', 'Pull it out with both hands on its sides.');
        return;
      }
      this.say('Server', 'Cannot rack it here yet.', 'Pull the two blanking panels out of this slot first.');
    }
    this.dropObject(server);
  }

  /** World matrix of the pinch point (index tip) or controller grip. */
  private handMatrix(hand: 'left' | 'right', isHand: boolean): Matrix4 {
    const space = isHand ? this.player.indexTipSpaces[hand] : this.player.gripSpaces[hand];
    space.updateWorldMatrix(true, false);
    return space.matrixWorld.clone();
  }

  /** World matrix of a tracked hand's grip (palm / wrist): steady in a fist. */
  private wristMatrix(hand: 'left' | 'right'): Matrix4 {
    const space = this.player.gripSpaces[hand];
    space.updateWorldMatrix(true, false);
    return space.matrixWorld.clone();
  }

  private tryNearGrab(
    hand: 'left' | 'right',
    handMatrix: Matrix4,
    reach: number,
    isHand = false,
  ): void {
    const point = new Vector3().setFromMatrixPosition(handMatrix);
    // The tablet, by its side handles only (like holding a real tablet);
    // the screen is for pressing buttons.
    const screen = this.tablet.screen;
    if (screen != null) {
      const box = new Box3();
      for (const grip of this.tablet.grips) {
        if (!box.setFromObject(grip).expandByScalar(reach).containsPoint(point)) continue;
        screen.updateWorldMatrix(true, false);
        const anchor = isHand ? this.wristMatrix(hand) : handMatrix;
        this.nearGrabs.set(hand, {
          tablet: true,
          wrist: isHand,
          offset: anchor.clone().invert().multiply(screen.matrixWorld),
        });
        return;
      }
    }
    // Move server mode: grab the whole server.
    if (this.phase === 'place') {
      const server = this.serverEntity?.object3D;
      if (server != null && new Box3().setFromObject(server).expandByScalar(reach).containsPoint(point)) {
        server.updateWorldMatrix(true, false);
        this.nearGrabs.set(hand, {
          server: true,
          offset: handMatrix.clone().invert().multiply(server.matrixWorld),
        });
      }
      return;
    }
    // Training: the closest grabbable part (smallest wins when nested).
    let best: PartRuntime | undefined;
    let bestScore = Infinity;
    const box = new Box3();
    const size = new Vector3();
    for (const part of this.parts.values()) {
      if (!isV01Part(part.info.name) || part.mode === 'gone' || part.busy) continue;
      if (part.entity.hasComponent(Grabbed)) continue;
      box.setFromObject(part.object);
      const d = box.distanceToPoint(point);
      if (d > reach) continue;
      // Outside: nearest box wins. Touching several (neighbours, nested):
      // nearest centre wins, then the smaller part.
      const volume = box.getSize(size).x * size.y * size.z;
      const centre = box.getCenter(new Vector3()).distanceTo(point);
      const score = d * 1000 + centre * 10 + volume;
      if (score < bestScore) {
        bestScore = score;
        best = part;
      }
    }
    if (best == null) return;
    const refusal = this.grabRefusal(best);
    if (refusal != null) {
      this.showPart(best.info.name, refusal);
      return;
    }
    if (best.mode === 'fitted') {
      this.setMode(best, 'seated');
      best.stage = 0;
    }
    best.denied = false;
    best.object.updateWorldMatrix(true, false);
    // Hands: follow the wrist (steady in a fist), not the pinching fingertip.
    const anchor = isHand ? this.wristMatrix(hand) : handMatrix;
    this.nearGrabs.set(hand, {
      part: best,
      wrist: isHand,
      offset: anchor.clone().invert().multiply(best.object.matrixWorld),
    });
    this.showPart(best.info.name);
  }

  private moveNearGrab(held: NearGrab, handMatrix: Matrix4, delta: number): void {
    const target = handMatrix.clone().multiply(held.offset);
    const pos = new Vector3();
    const quat = new Quaternion();
    target.decompose(pos, quat, new Vector3());
    if (held.wrist) {
      // Skip tracking glitches: a big jump in one frame = hold the last pose.
      if (held.lastPos != null && held.lastQuat != null) {
        const jump = pos.distanceTo(held.lastPos) > TOOL_JUMP_POS || quat.angleTo(held.lastQuat) > TOOL_JUMP_ANGLE;
        if (jump && (held.skipped ?? 0) < 8) {
          held.skipped = (held.skipped ?? 0) + 1;
          return;
        }
      }
      held.skipped = 0;
      held.lastPos = (held.lastPos ?? new Vector3()).copy(pos);
      held.lastQuat = (held.lastQuat ?? new Quaternion()).copy(quat);
    }
    if (held.tablet || held.tool) {
      const screen = held.tool ? this.tool : this.tablet.screen;
      if (screen == null) return;
      const parent = screen.parent;
      if (parent != null) {
        parent.updateWorldMatrix(true, false);
        parent.worldToLocal(pos);
        quat.premultiply(parent.getWorldQuaternion(new Quaternion()).invert());
      }
      const k = 1 - Math.exp(-delta * (held.wrist ? TOOL_SMOOTHING : SMOOTHING));
      screen.position.lerp(pos, k);
      screen.quaternion.slerp(quat, k);
      return;
    }
    if (held.server) {
      const server = this.serverEntity?.object3D;
      if (server == null) return;
      if (server.parent != null) server.parent.worldToLocal(pos);
      // Move only; keep it level and facing the same way.
      server.position.lerp(pos, 1 - Math.exp(-delta * SMOOTHING));
      return;
    }
    const part = held.part;
    if (part == null) return;
    const parent = part.object.parent;
    if (parent != null) {
      parent.updateWorldMatrix(true, false);
      parent.worldToLocal(pos);
      quat.premultiply(parent.getWorldQuaternion(new Quaternion()).invert());
    }
    part.object.position.copy(pos);
    if (part.mode === 'free') part.object.quaternion.copy(quat);
    this.smoothHeld(part, delta);
    if (part.mode === 'seated') this.followPath(part);
  }

  // ------------------------------------------------------------ screwdriver

  /**
   * Find the screwdriver once its model has loaded and work out how it sits
   * in the left hand: handle in the palm, shaft pointing forward.
   */
  private tryInitTool(): void {
    const tool = this.world.getSceneObject('screwdriver');
    const tip = tool?.getObjectByName('sd_tip');
    if (tool == null || tip == null) return; // model not loaded yet
    // Measure in the tool's own frame: reset its pose for a moment.
    const pos = tool.position.clone();
    const quat = tool.quaternion.clone();
    const scale = tool.scale.clone();
    const parent = tool.parent;
    parent?.remove(tool);
    tool.position.set(0, 0, 0);
    tool.quaternion.identity();
    tool.scale.set(1, 1, 1);
    tool.updateMatrixWorld(true);
    const box = new Box3().setFromObject(tool);
    const tipLocal = tip.getWorldPosition(new Vector3());
    parent?.add(tool);
    tool.position.copy(pos);
    tool.quaternion.copy(quat);
    tool.scale.copy(scale);
    tool.updateMatrixWorld(true);
    // Axis is local Y; the tip is at one end, the handle end at the other.
    const tipUp = tipLocal.y > (box.min.y + box.max.y) / 2;
    const tipEnd = tipUp ? box.max.y : box.min.y;
    const handleEnd = tipUp ? box.min.y : box.max.y;
    const gripY = handleEnd + (tipEnd - handleEnd) * TOOL_GRIP_AT;
    const along = new Vector3(0, tipUp ? 1 : -1, 0);
    const q = new Quaternion().setFromUnitVectors(along, new Vector3(0, 0, -1));
    const s = tool.getWorldScale(new Vector3());
    const grip = new Vector3((box.min.x + box.max.x) / 2, gripY, (box.min.z + box.max.z) / 2)
      .multiply(s)
      .applyQuaternion(q)
      .negate();
    this.toolOffset = new Matrix4().compose(grip, q, s);
    this.tool = tool;
    this.toolTip = tip;
  }

  /**
   * The left hand IS the screwdriver: each frame the tool follows the left
   * grip (palm) and the left hand / controller model is hidden. Tracking
   * glitches are skipped, with light smoothing.
   */
  private updateLeftTool(delta: number): void {
    const tool = this.tool;
    const offset = this.toolOffset;
    const inXR = this.world.visibilityState.peek() !== VisibilityState.NonImmersive;
    const left = this.input.xr.gamepads.left;
    const adapters = this.input.xr.visualAdapters;
    if (inXR) {
      const hand = adapters.hand.left.visual?.model;
      const pad = adapters.controller.left.visual?.model;
      if (hand != null) hand.visible = false;
      if (pad != null) pad.visible = false;
    }
    if (tool == null || offset == null || !inXR || left == null) return;
    const target = this.wristMatrix('left').multiply(offset);
    const pos = new Vector3();
    const quat = new Quaternion();
    target.decompose(pos, quat, new Vector3());
    const hold = this.toolHold;
    if (hold.lastPos != null && hold.lastQuat != null) {
      const jump = pos.distanceTo(hold.lastPos) > TOOL_JUMP_POS || quat.angleTo(hold.lastQuat) > TOOL_JUMP_ANGLE;
      if (jump && (hold.skipped ?? 0) < 8) {
        hold.skipped = (hold.skipped ?? 0) + 1;
        return;
      }
    }
    const first = hold.lastPos == null;
    hold.skipped = 0;
    hold.lastPos = (hold.lastPos ?? new Vector3()).copy(pos);
    hold.lastQuat = (hold.lastQuat ?? new Quaternion()).copy(quat);
    const parent = tool.parent;
    if (parent != null) {
      parent.updateWorldMatrix(true, false);
      parent.worldToLocal(pos);
      quat.premultiply(parent.getWorldQuaternion(new Quaternion()).invert());
    }
    const k = first ? 1 : 1 - Math.exp(-delta * TOOL_SMOOTHING);
    tool.position.lerp(pos, k);
    tool.quaternion.slerp(quat, k);
  }

  /** Which hand holds the screwdriver (laser or near grab), if any. */
  private toolHand(): 'left' | 'right' | undefined {
    const inXR = this.world.visibilityState.peek() !== VisibilityState.NonImmersive;
    return inXR && this.input.xr.gamepads.left != null && this.toolOffset != null ? 'left' : undefined;
  }

  /**
   * Held by a controller: that controller's lower button (X / A) unscrews and
   * upper button (Y / B) screws in the screw at the tip. Held by a hand:
   * touching a screw toggles it. Rules (lid off, heatsink order…) still apply.
   */
  private updateTool(): void {
    const hand = this.toolHand();
    if (hand == null || this.toolTip == null) {
      this.toolShown = undefined;
      this.toolTouched.clear();
      return;
    }
    const isHand = this.input.xr.isPrimary('hand', hand);
    const tip = this.toolTip.getWorldPosition(new Vector3());
    let nearest: ControlRuntime | undefined;
    let nearestDist = TOOL_REACH;
    for (const c of this.controls.values()) {
      if (c.info.motion !== 'screw' || !isV01Control(c.info.name)) continue;
      const d = c.object.getWorldPosition(this.tmp).distanceTo(tip);
      if (d < nearestDist) {
        nearestDist = d;
        nearest = c;
      }
    }
    const lower = hand === 'left' ? 'X' : 'A';
    const upper = hand === 'left' ? 'Y' : 'B';
    const help = isHand ? TOOL_TEXT.hand : TOOL_TEXT.controller(lower, upper);
    const shown = `${hand}:${isHand}:${nearest?.info.name ?? ''}`;
    if (shown !== this.toolShown) {
      this.toolShown = shown;
      const status = nearest != null ? `${label(nearest.info.name)}: ${this.stateWord(nearest)}` : 'No screw at the tip.';
      this.say('Screwdriver', help, status);
    }
    if (nearest == null) return;
    const name = nearest.info.name;
    const undone = this.rules?.isOperated(name) ?? false;
    const now = performance.now() / 1000;
    const turn = () => {
      if (now - this.toolLastTurn < TOOL_COOLDOWN) return;
      this.toolLastTurn = now;
      this.onControl(name, true);
      this.toolShown = undefined;
    };
    if (isHand) {
      // Touch toggles once; move away to touch again.
      for (const t of [...this.toolTouched]) {
        const c = this.controls.get(t);
        if (c == null || c.object.getWorldPosition(this.tmp).distanceTo(tip) > TOOL_TOUCH * 2) {
          this.toolTouched.delete(t);
        }
      }
      if (nearestDist <= TOOL_TOUCH && !this.toolTouched.has(name)) {
        this.toolTouched.add(name);
        turn();
      }
      return;
    }
    const pad = this.input.xr.gamepads[hand];
    // xr-standard: 4 = X / A (lower), 5 = Y / B (upper).
    if (pad?.getButtonDownByIdx(4) && !undone) turn();
    else if (pad?.getButtonDownByIdx(5) && undone) turn();
  }

  // ------------------------------------------- placing the server (laser)

  private onServerPointerDown(event: PointerEventLike): void {
    if (this.phase !== 'place') return;
    const server = this.serverEntity?.object3D;
    const point = (event as PointerEventLike & { point?: Vector3 }).point;
    if (server == null || point == null) return;
    const hand = (['right', 'left'] as const).find((h) =>
      this.input.xr.gamepads[h]?.getSelecting(),
    );
    if (hand == null) return;
    const origin = this.player.raySpaces[hand].getWorldPosition(new Vector3());
    this.serverDrag = {
      target: 'server',
      hand,
      distance: origin.distanceTo(point),
      offset: server.getWorldPosition(new Vector3()).sub(point),
    };
  }

  private updateServerDrag(delta: number): void {
    if (this.serverDrag == null) this.tryStartServerDrag();
    const drag = this.serverDrag;
    if (drag == null) return;
    const pad = this.input.xr.gamepads[drag.hand];
    const server =
      drag.target === 'tablet'
        ? this.tablet.screen
        : drag.target === 'tool'
          ? this.tool
          : this.serverEntity?.object3D;
    if (pad == null || server == null || !pad.getSelecting()) {
      this.serverDrag = undefined;
      this.setStickTurning(true);
      return;
    }
    if (drag.target === 'server') {
      // Right stick up = push the server away, down = bring it back.
      this.setStickTurning(false);
      const stick = this.input.xr.gamepads.right?.getAxesValues(InputComponent.Thumbstick);
      if (stick != null && Math.abs(stick.y) > 0.2) {
        drag.distance = Math.min(5, Math.max(0.2, drag.distance - stick.y * ZOOM_SPEED * delta));
      }
    }
    const ray = this.player.raySpaces[drag.hand];
    ray.updateWorldMatrix(true, false);
    if (drag.rigid != null) {
      // Tablet: held rigidly on the laser, so twisting the controller turns it.
      const pos = new Vector3();
      const quat = new Quaternion();
      ray.matrixWorld.clone().multiply(drag.rigid).decompose(pos, quat, new Vector3());
      const parent = server.parent;
      if (parent != null) {
        parent.updateWorldMatrix(true, false);
        parent.worldToLocal(pos);
        quat.premultiply(parent.getWorldQuaternion(new Quaternion()).invert());
      }
      server.position.lerp(pos, 0.5);
      server.quaternion.slerp(quat, 0.5);
      return;
    }
    const origin = new Vector3().setFromMatrixPosition(ray.matrixWorld);
    const dir = new Vector3(0, 0, -1).applyQuaternion(ray.getWorldQuaternion(new Quaternion()));
    const pos = origin.addScaledVector(dir, drag.distance).add(drag.offset);
    if (server.parent != null) server.parent.worldToLocal(pos);
    server.position.lerp(pos, 0.5);
  }

  /**
   * Trigger pressed while the laser points at the server (place phase).
   * Raycast directly: part grab handles swallow the pointer event.
   */
  private tryStartServerDrag(): void {
    const server = this.serverEntity?.object3D;
    const screen = this.tablet.screen;
    for (const hand of ['right', 'left'] as const) {
      if (!this.input.xr.gamepads[hand]?.getSelectStart()) continue;
      const ray = this.player.raySpaces[hand];
      ray.updateWorldMatrix(true, false);
      const origin = new Vector3().setFromMatrixPosition(ray.matrixWorld);
      const dir = new Vector3(0, 0, -1).applyQuaternion(ray.getWorldQuaternion(new Quaternion()));
      this.raycaster.set(origin, dir);
      // Tablet side grips first (any time).
      const gripHit = this.raycaster.intersectObjects(this.tablet.grips, false)[0];
      if (gripHit != null && screen != null) {
        screen.updateWorldMatrix(true, false);
        this.serverDrag = {
          target: 'tablet',
          hand,
          rigid: ray.matrixWorld.clone().invert().multiply(screen.matrixWorld),
          distance: gripHit.distance,
          offset: screen.getWorldPosition(new Vector3()).sub(gripHit.point),
        };
        return;
      }
      if (this.phase !== 'place' || server == null) continue;
      const hit = this.raycaster.intersectObject(server, true)[0];
      if (hit == null) continue;
      this.serverDrag = {
        target: 'server',
        hand,
        distance: hit.distance,
        offset: server.getWorldPosition(new Vector3()).sub(hit.point),
      };
      return;
    }
  }

  // --------------------------------------- open handles pass the laser on

  /**
   * When a fitted part may come out, its own press/hinge controls (caddy
   * button + handle, lid tabs) stop catching the laser, so holding on the
   * handle arm grabs the part behind it. They catch clicks again otherwise.
   */
  private updatePassThrough(): void {
    for (const c of this.controls.values()) {
      // Socket lever / plate belong to the board in the model, but they hold
      // the CPU: once open they let clicks through to it.
      const ownerName = /^socket_\d+_(lever|plate)$/.test(c.info.name)
        ? this.ownerOf(c.info.name)
        : c.info.asset;
      const owner = ownerName != null ? this.parts.get(ownerName) : undefined;
      const passes =
        owner != null &&
        this.started &&
        owner.mode === 'fitted' &&
        (c.info.motion === 'press' || c.info.motion === 'hinge') &&
        owner.info.requires.includes(c.info.name) &&
        this.grabRefusal(owner) == null;
      (c.object as Object3D & { pointerEvents?: string }).pointerEvents = passes
        ? 'none'
        : undefined;
      // Green glow only on lid buttons (pressed), screws (undone) and DIMM
      // ejectors (open).
      const glows =
        /^lid_tab_[LR]$/.test(c.info.name) ||
        /^dimm_slot_\d+_clip[FR]$/.test(c.info.name) ||
        (c.info.motion === 'screw' && isV01Control(c.info.name));
      const on = glows && (this.rules?.isOperated(c.info.name) ?? false);
      this.tint(c.object, on ? PRESSED_COLOR : null);
    }
  }

  /** Give a control's meshes a coloured glow, or put the originals back. */
  private tint(obj: Object3D, color: number | null): void {
    obj.traverse((child) => {
      const mesh = child as Mesh;
      if (!mesh.isMesh || mesh.name.endsWith('_hit')) return;
      const data = mesh.userData as { originalMaterial?: Material };
      if (data.originalMaterial == null) {
        if (color == null) return;
        data.originalMaterial = mesh.material as Material;
      }
      const original = data.originalMaterial;
      if (color == null) {
        mesh.material = original;
        return;
      }
      let byColor = this.tintCache.get(original);
      if (byColor == null) {
        byColor = new Map();
        this.tintCache.set(original, byColor);
      }
      let tinted = byColor.get(color);
      if (tinted == null) {
        tinted = original.clone();
        const m = tinted as Material & { emissive?: { setHex: (c: number) => void }; emissiveIntensity?: number; color?: { setHex: (c: number) => void } };
        if (m.emissive != null) {
          m.emissive.setHex(color);
          m.emissiveIntensity = 0.7;
        } else {
          m.color?.setHex(color);
        }
        byColor.set(color, tinted);
      }
      mesh.material = tinted;
    });
  }

  // -------------------------------------------------------------- tweens

  private updateTweens(delta: number): void {
    if (this.tweens.length === 0) return;
    const running = this.tweens;
    this.tweens = [];
    for (const tw of running) {
      tw.elapsed += delta;
      const t = Math.min(1, tw.elapsed / tw.duration);
      const eased = t * t * (3 - 2 * t);
      tw.update(eased);
      if (t >= 1) tw.done?.();
      else this.tweens.push(tw);
    }
  }
}
