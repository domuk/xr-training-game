// The training lab room: its doors and drawers open / close on a click
// (laser or finger), and a prop screwdriver sits in tool-cabinet drawer 1.
// Data comes from the lab model's glTF extras + lab_manifest.json
// (axis_world is in Blender axes: (x, y, z) -> three (x, z, -y)).
import {
  Box3,
  Matrix4,
  Mesh,
  type Object3D,
  Quaternion,
  Vector3,
  type World,
} from '@iwsdk/core';

/** Moving parts the user can open / close in v1 (the lift comes later). */
const OPENABLE = /^(door_leaf_[WE]|rack_1_door_(front|rear_[LR])|lab_cabinet_(door_[LR]|drawer_\d+))$/;
const TWEEN_TIME = 0.4; // s

interface Mover {
  obj: Object3D;
  motion: 'hinge' | 'slide';
  /** Axis in the parent's space (unit). */
  axis: Vector3;
  limit: number; // degrees (hinge) or metres (slide)
  restPos: Vector3;
  restQuat: Quaternion;
  amount: number; // 0 closed .. 1 open
  target: number;
}

type ManifestNode = {
  role?: string;
  motion?: string;
  limits?: number[];
  axis_world?: number[];
  requires?: string;
  pull_world?: number[][];
};

/** A 2U server position in a rack. */
export interface RackSlot {
  name: string;
  obj: Object3D;
  /** The two 1U blanking panels that must be out first. */
  blanks: string[];
}

const BLANK = /^asset_rack_\d+_blank_u\d+$/;
const RACK_SLOT = /^slot_rack_\d+_u\d+$/;

export class LabRoom {
  private movers = new Map<string, Mover>();
  root?: Object3D;
  /** Prop screwdriver kept in drawer 1 (follows the drawer until picked up). */
  prop?: Object3D;
  private propInDrawer = true;
  private propOffset = new Matrix4();
  /** Rack server slots, and blanking panels that have been pulled out. */
  slots: RackSlot[] = [];
  blanksOut = new Set<string>();
  private blankRest = new Map<string, { obj: Object3D; pos: Vector3; parent: Object3D | null }>();
  /** Called when a blank has been pulled out (the app drops it to the floor). */
  onBlankOut?: (obj: Object3D) => void;

  private openable: RegExp;

  /** `openable`: which moving parts open on a click (default: the lab's). */
  constructor(private world: World, opts: { openable?: RegExp } = {}) {
    this.openable = opts.openable ?? OPENABLE;
  }

  /** Once the lab model and its manifest are loaded. */
  async init(root: Object3D, manifestUrl: string, toolModel?: Object3D): Promise<void> {
    this.root = root;
    let nodes: Record<string, ManifestNode> = {};
    try {
      nodes = (await (await fetch(manifestUrl)).json()).nodes ?? {};
    } catch {
      /* no manifest: nothing opens */
    }
    root.updateMatrixWorld(true);
    for (const [name, n] of Object.entries(nodes)) {
      if (!this.openable.test(name) || n.role !== 'moving') continue;
      if (n.motion !== 'hinge' && n.motion !== 'slide' && n.motion !== 'press') continue;
      const obj = root.getObjectByName(name);
      const a = n.axis_world;
      if (obj == null || a == null || obj.parent == null) continue;
      const world = new Vector3(a[0], a[2], -a[1]).normalize();
      const parentQ = obj.parent.getWorldQuaternion(new Quaternion()).invert();
      const limits = n.limits ?? [0, 0];
      const limit = Math.abs(limits[1]) >= Math.abs(limits[0]) ? limits[1] : limits[0];
      this.movers.set(name, {
        obj,
        motion: n.motion === 'hinge' ? 'hinge' : 'slide', // a press moves like a short slide
        axis: world.applyQuaternion(parentQ).normalize(),
        limit,
        restPos: obj.position.clone(),
        restQuat: obj.quaternion.clone(),
        amount: 0,
        target: 0,
      });
      (obj as unknown as {
        addEventListener: (t: string, f: (e: { stopPropagation?: () => void }) => void) => void;
      }).addEventListener('pointerdown', (e) => {
        e.stopPropagation?.();
        // The lab's double door leads to the data hall.
        if (/^door_leaf_[WE]$/.test(name) && this.onDoor != null) this.onDoor();
        else this.toggle(name);
      });
    }
    for (const [name, n] of Object.entries(nodes)) {
      const obj = root.getObjectByName(name);
      if (obj == null) continue;
      if (RACK_SLOT.test(name)) {
        this.slots.push({ name, obj, blanks: (n.requires ?? '').split(',').map((t) => t.trim()).filter(Boolean) });
      } else if (BLANK.test(name) && n.pull_world?.[0] != null) {
        // Tool-less blank: a click / poke pulls it 40 mm out, then it drops.
        const pw = n.pull_world[0];
        const out = new Vector3(pw[0], pw[2], -pw[1]);
        this.blankRest.set(name, { obj, pos: obj.position.clone(), parent: obj.parent });
        (obj as unknown as {
          addEventListener: (t: string, f: (e: { stopPropagation?: () => void }) => void) => void;
        }).addEventListener('pointerdown', (e) => {
          e.stopPropagation?.();
          this.pullBlank(name, out);
        });
      }
    }
    if (toolModel != null) this.addProp(toolModel);
  }

  /** Tool-less blank: slides 40 mm out of the rack, then the app drops it. */
  private pullBlank(name: string, outWorld: Vector3): void {
    const rest = this.blankRest.get(name);
    if (rest == null || this.blanksOut.has(name)) return;
    this.blanksOut.add(name);
    const obj = rest.obj;
    const parentQ = obj.parent?.getWorldQuaternion(new Quaternion()).invert() ?? new Quaternion();
    const step = outWorld.clone().applyQuaternion(parentQ);
    const from = obj.position.clone();
    let t = 0;
    this.blankTweens.push((dt) => {
      t = Math.min(1, t + dt / 0.3);
      obj.position.copy(from).addScaledVector(step, t);
      if (t >= 1) this.onBlankOut?.(obj);
      return t >= 1;
    });
  }

  /** Server put into a slot: its blanks count as out (hidden). */
  hideBlanks(slot: RackSlot): void {
    for (const b of slot.blanks) {
      const rest = this.blankRest.get(b);
      if (rest == null) continue;
      this.blanksOut.add(b);
      rest.obj.visible = false;
      (rest.obj as Object3D & { pointerEvents?: string }).pointerEvents = 'none';
    }
  }

  private blankTweens: ((dt: number) => boolean)[] = [];

  /** Called when the lab's double door is clicked (go to the data hall). */
  onDoor?: () => void;

  /** Called with a short message when a move isn't allowed. */
  onRefuse?: (title: string, text: string) => void;

  /** Is this object (or one of its parents) a door / drawer of the room? */
  isMover(obj: Object3D): boolean {
    for (let o: Object3D | null = obj; o != null; o = o.parent) {
      for (const m of this.movers.values()) if (m.obj === o) return true;
    }
    return false;
  }

  /** Doors / drawers move: not solid for collisions. */
  moverObjects(): Object3D[] {
    return [...this.movers.values()].map((m) => m.obj);
  }

  toggle(name: string): void {
    const m = this.movers.get(name);
    if (m == null) return;
    const opening = m.target <= 0.5;
    const open = (n: string) => (this.movers.get(n)?.target ?? 0) > 0.5;
    if (opening && /^lab_cabinet_drawer_\d+$/.test(name) && !(open('lab_cabinet_door_L') && open('lab_cabinet_door_R'))) {
      this.onRefuse?.('Tool cabinet', 'Open both cabinet doors first.');
      return;
    }
    if (!opening && /^lab_cabinet_door_[LR]$/.test(name)) {
      for (const n of this.movers.keys()) {
        if (/^lab_cabinet_drawer_\d+$/.test(n) && open(n)) {
          this.onRefuse?.('Tool cabinet', 'Close the drawers first.');
          return;
        }
      }
    }
    m.target = opening ? 1 : 0;
  }

  update(delta: number): void {
    const step = delta / TWEEN_TIME;
    for (const m of this.movers.values()) {
      if (m.amount === m.target) continue;
      m.amount = m.target > m.amount ? Math.min(m.target, m.amount + step) : Math.max(m.target, m.amount - step);
      const t = m.amount * m.amount * (3 - 2 * m.amount);
      if (m.motion === 'slide') {
        m.obj.position.copy(m.restPos).addScaledVector(m.axis, m.limit * t);
      } else {
        m.obj.quaternion
          .setFromAxisAngle(m.axis, (m.limit * t * Math.PI) / 180)
          .multiply(m.restQuat);
      }
    }
    this.followDrawer();
    this.blankTweens = this.blankTweens.filter((f) => !f(delta));
  }

  // ---------------------------------------------------------- prop screwdriver

  /** A copy of the screwdriver model lying in drawer 1. */
  private addProp(toolModel: Object3D): void {
    const drawer = this.movers.get('lab_cabinet_drawer_1')?.obj;
    if (drawer == null) return;
    const prop = toolModel.clone(true);
    prop.name = 'prop_screwdriver';
    prop.visible = true;
    prop.traverse((o) => {
      if ((o as Mesh).isMesh && o.name.endsWith('_zone')) o.visible = false;
    });
    // Lay it flat in the middle of the drawer, a little above the bottom.
    drawer.updateMatrixWorld(true);
    const box = new Box3().setFromObject(drawer);
    const centre = box.getCenter(new Vector3());
    const pose = new Matrix4().compose(
      new Vector3(centre.x, box.min.y + 0.03, centre.z),
      new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI / 2),
      toolModel.getWorldScale(new Vector3()),
    );
    this.propOffset.copy(drawer.matrixWorld).invert().multiply(pose);
    // The caller turns it into an entity (grabbable) and adds it to the scene.
    this.prop = prop;
  }

  /** Keep the prop in drawer 1 while it hasn't been picked up. */
  private followDrawer(): void {
    const drawer = this.movers.get('lab_cabinet_drawer_1')?.obj;
    if (!this.propInDrawer || this.prop == null || drawer == null) return;
    drawer.updateMatrixWorld(true);
    const m = drawer.matrixWorld.clone().multiply(this.propOffset);
    m.decompose(this.prop.position, this.prop.quaternion, this.prop.scale);
  }

  /** Prop added to the scene: put it in the drawer. */
  placeProp(): void {
    this.followDrawer();
  }

  /** Picked up: stop following the drawer. */
  releaseProp(): void {
    this.propInDrawer = false;
  }

  /** Put the room back (doors and drawers shut, prop in its drawer). */
  reset(): void {
    for (const m of this.movers.values()) {
      m.amount = 0;
      m.target = 0;
      m.obj.position.copy(m.restPos);
      m.obj.quaternion.copy(m.restQuat);
    }
    this.propInDrawer = true;
    this.followDrawer();
    for (const rest of this.blankRest.values()) {
      if (rest.parent != null && rest.obj.parent !== rest.parent) rest.parent.add(rest.obj);
      rest.obj.position.copy(rest.pos);
      rest.obj.visible = true;
      (rest.obj as Object3D & { pointerEvents?: string }).pointerEvents = undefined;
    }
    this.blanksOut.clear();
    this.blankTweens = [];
  }
}
