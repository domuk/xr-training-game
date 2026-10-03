// Service rules for the 2U server: which parts and controls can be used, in
// what order. Pure logic (no three.js) so it can be tested with plain Node.
//
// Data comes from the model's glTF extras (see the README's model metadata table):
//   parts    = `asset_*` nodes   (pull path, requires, order_out/order_in, tips)
//   controls = moving parts + fasteners (motion, axis, limits, seq, optional)

export type Vec3 = [number, number, number];
export type Motion = 'hinge' | 'press' | 'slide' | 'screw';
export type AxisName = 'X' | 'Y' | 'Z';

export interface PartInfo {
  name: string;
  parent: string | null;
  requires: string[];
  pull: Vec3[];
  orderOut: number[];
  orderIn: number[];
  tip?: string;
  check?: string;
  warn?: string;
  note?: string;
}

export interface ControlInfo {
  name: string;
  asset: string | null;
  motion: Motion;
  axis: AxisName;
  limits: [number, number];
  requires: string[];
  seq?: number;
  optional: boolean;
  captive: boolean;
  rise: number;
  tip?: string;
  note?: string;
}

export interface Result {
  ok: boolean;
  reason?: string;
}

/** Parts the trainee can take out in v0.1 (README: Features). */
const V01_PARTS =
  /^asset_(lid|caddy_\d+|drive_\d+|fan_\d+|dimm_\d+|hs_\d+|cpu_\d+|nic|accel|shroud|board)$/;

/** Controls that belong to the v0.1 parts. */
const V01_CONTROLS =
  /^(lid_tab_[LR]|lid_screw|caddy_\d+_(button|handle|screw_\d+)|dimm_slot_\d+_clip[FR]|hs_\d+_screw_\d+|socket_\d+_(lever|plate)|nic_screw|accel_screw|board_screw_\d+)$/;

/** Everything else sits under the lid, so the lid must come off first. */
const OUTSIDE_LID = /^(asset_)?(lid|caddy|drive|psu|cord|blank|ctrl|io)(_|$)/;

/** Controls the training skips for now (user: fans just pull out). */
const SKIPPED_REQUIRES = /^fan_\d+_release_tab$/;

/**
 * Cables and cords are hidden for now (to be coded properly later), so
 * nothing waits on them.
 */
export const CABLES =
  /^(asset_cable_sata|asset_cord_\d+|fixed_cables|atx_plug_\d+|pwr_\d+_plug|fan_\d+_(cable|plug))$/;

/**
 * The motherboard: DIMMs, CPUs and heatsinks aren't attached to it in the
 * model, so they must come out before it does.
 */
const BOARD_EXTRA = /^asset_(dimm|cpu)_\d+$/;

/** DIMM ejectors open/close as a pair (one click unlocks the DIMM). */
const DIMM_CLIP = /^(dimm_slot_\d+)_clip([FR])$/;

/** Drive screws sit inside the bay: only reachable with the caddy out. */
const CADDY_SCREW = /^caddy_(\d+)_screw_\d+$/;

export function isV01Part(name: string): boolean {
  return V01_PARTS.test(name);
}

export function isV01Control(name: string): boolean {
  return V01_CONTROLS.test(name);
}

export function needsLidOff(name: string): boolean {
  return !OUTSIDE_LID.test(name);
}

export function splitList(value: unknown): string[] {
  if (typeof value !== 'string') return [];
  return value
    .split(',')
    .map((s) => s.trim())
    .filter((s) => s.length > 0);
}

export function parseOrder(value: unknown): number[] {
  return splitList(value)
    .map((s) => Number(s))
    .filter((n) => Number.isFinite(n));
}

/** Plain-language name for any part or control id. */
export function label(name: string): string {
  const n = (s: string) => String(Number(s));
  let m: RegExpMatchArray | null;
  if (name === 'asset_lid') return 'Lid';
  if ((m = name.match(/^asset_caddy_(\d+)$/))) return `Drive caddy ${n(m[1])}`;
  if ((m = name.match(/^asset_drive_(\d+)$/))) return `Drive ${n(m[1])}`;
  if ((m = name.match(/^asset_fan_(\d+)$/))) return `Fan ${n(m[1])}`;
  if ((m = name.match(/^asset_dimm_(\d+)$/))) return `DIMM ${n(m[1])}`;
  if ((m = name.match(/^asset_hs_(\d+)$/))) return `Heatsink ${n(m[1])}`;
  if ((m = name.match(/^asset_cpu_(\d+)$/))) return `CPU ${n(m[1])}`;
  if ((m = name.match(/^asset_psu_(\d+)$/))) return `PSU ${n(m[1])}`;
  if ((m = name.match(/^asset_cord_(\d+)$/))) return `Power cord ${n(m[1])}`;
  if ((m = name.match(/^asset_blank_(\d+)$/))) return `Blank bracket ${n(m[1])}`;
  if (name === 'asset_nic') return 'Network card';
  if (name === 'asset_accel') return 'Accelerator card';
  if (name === 'asset_shroud') return 'Air shroud';
  if (name === 'asset_backplane') return 'Backplane';
  if (name === 'asset_board') return 'Motherboard';
  if (name === 'asset_battery') return 'CMOS battery';
  if (name === 'asset_cable_sata') return 'SATA cable';
  if (name === 'lid_tab_L') return 'Left lid tab';
  if (name === 'lid_tab_R') return 'Right lid tab';
  if (name === 'lid_screw') return 'Lid screw';
  if ((m = name.match(/^caddy_(\d+)_button$/))) return `Caddy ${n(m[1])} button`;
  if ((m = name.match(/^caddy_(\d+)_handle$/))) return `Caddy ${n(m[1])} handle`;
  if ((m = name.match(/^caddy_(\d+)_screw_(\d+)$/)))
    return `Caddy ${n(m[1])} screw ${m[2]}`;
  if ((m = name.match(/^fan_(\d+)_release_tab$/)))
    return `Fan ${n(m[1])} release tab`;
  if ((m = name.match(/^dimm_slot_(\d+)_clip([FR])$/)))
    return `DIMM ${n(m[1])} ${m[2] === 'F' ? 'front' : 'rear'} ejector`;
  if ((m = name.match(/^hs_(\d+)_screw_(\d+)$/)))
    return `Heatsink ${n(m[1])} screw ${m[2]}`;
  if ((m = name.match(/^socket_(\d+)_lever$/))) return `Socket ${n(m[1])} lever`;
  if ((m = name.match(/^socket_(\d+)_plate$/)))
    return `Socket ${n(m[1])} load plate`;
  if (name === 'nic_screw') return 'Network card screw';
  if (name === 'accel_screw') return 'Accelerator card screw';
  if ((m = name.match(/^board_screw_(\d+)$/))) return `Motherboard screw ${m[1]}`;
  return name.replace(/^asset_/, '').replace(/_/g, ' ');
}

export class ServiceRules {
  readonly parts = new Map<string, PartInfo>();
  readonly controls = new Map<string, ControlInfo>();
  private fitted = new Map<string, boolean>();
  private operated = new Map<string, boolean>();

  constructor(parts: PartInfo[], controls: ControlInfo[]) {
    for (const p of parts) {
      this.parts.set(p.name, {
        ...p,
        requires: p.requires.filter((t) => !SKIPPED_REQUIRES.test(t) && !CABLES.test(t)),
      });
    }
    const board = this.parts.get('asset_board');
    if (board != null) {
      const extra = parts.map((p) => p.name).filter((n) => BOARD_EXTRA.test(n));
      board.requires = [...board.requires, ...extra.sort()];
    }
    for (const c of controls) this.controls.set(c.name, c);
    this.reset();
  }

  reset(): void {
    for (const name of this.parts.keys()) this.fitted.set(name, true);
    for (const name of this.controls.keys()) this.operated.set(name, false);
  }

  isFitted(part: string): boolean {
    return this.fitted.get(part) ?? true;
  }

  isOperated(control: string): boolean {
    return this.operated.get(control) ?? false;
  }

  lidOff(): boolean {
    return this.parts.has('asset_lid') && !this.isFitted('asset_lid');
  }

  /** Is a `requires` token done? Assets must be out; controls operated. */
  tokenDone(token: string): boolean {
    if (this.parts.has(token)) return !this.isFitted(token);
    const c = this.controls.get(token);
    if (c == null) return true; // unknown token never blocks
    if (c.optional) return true;
    return this.isOperated(token);
  }

  private firstMissing(tokens: string[]): string | undefined {
    return tokens.find((t) => !this.tokenDone(t));
  }

  private missingText(token: string): string {
    if (this.parts.has(token)) return `Remove the ${label(token)} first.`;
    return `${label(token)} first.`;
  }

  canRemove(part: string): Result {
    const info = this.parts.get(part);
    if (info == null) return { ok: false, reason: 'Unknown part.' };
    if (!isV01Part(part)) {
      return { ok: false, reason: `${label(part)}: not in this training yet.` };
    }
    if (!this.isFitted(part)) return { ok: true };
    if (needsLidOff(part) && !this.lidOff()) {
      return { ok: false, reason: 'Take the lid off first.' };
    }
    if (info.parent != null && this.isFitted(info.parent)) {
      return { ok: false, reason: `Pull the ${label(info.parent)} out first.` };
    }
    const missing = this.firstMissing(info.requires);
    if (missing != null) return { ok: false, reason: this.missingText(missing) };
    return { ok: true };
  }

  /** Can a removed part go back into its slot? */
  canRefit(part: string, requires?: string[]): Result {
    const info = this.parts.get(part);
    if (info == null) return { ok: false, reason: 'Unknown part.' };
    if (needsLidOff(part) && !this.lidOff()) {
      return { ok: false, reason: 'Take the lid off first.' };
    }
    // Reverse order: a part whose removal needed this one out goes back first
    // (the motherboard before its DIMMs, CPUs, cards and shroud).
    for (const other of this.parts.values()) {
      if (other.name !== part && other.requires.includes(part) && !this.isFitted(other.name)) {
        return { ok: false, reason: `Fit the ${label(other.name)} first.` };
      }
    }
    if (info.parent != null && this.isFitted(info.parent)) {
      return { ok: false, reason: `Pull the ${label(info.parent)} out first.` };
    }
    for (const child of this.childrenOf(part)) {
      if (!this.isFitted(child)) {
        return { ok: false, reason: `Put the ${label(child)} back in first.` };
      }
    }
    for (const token of requires ?? info.requires) {
      if (this.parts.has(token)) {
        if (this.isFitted(token)) {
          return { ok: false, reason: `Remove the ${label(token)} first.` };
        }
        continue;
      }
      const c = this.controls.get(token);
      if (c == null) continue;
      if ((c.motion === 'hinge' || c.motion === 'slide') && !this.isOperated(token)) {
        return { ok: false, reason: `Open the ${label(token)} first.` };
      }
    }
    return { ok: true };
  }

  childrenOf(part: string): string[] {
    const out: string[] = [];
    for (const p of this.parts.values()) if (p.parent === part) out.push(p.name);
    return out;
  }

  /** A part moved to another slot: its prerequisites change (CPU sockets). */
  setPartRequires(part: string, requires: string[]): void {
    const info = this.parts.get(part);
    if (info != null) info.requires = requires;
  }

  /** A control's prerequisites changed (socket lever ↔ heatsink in that socket). */
  setControlRequires(control: string, requires: string[]): void {
    const info = this.controls.get(control);
    if (info != null) info.requires = requires;
  }

  /** Debug: set a part's state without checking the rules. */
  forceFitted(part: string, fitted: boolean): void {
    this.fitted.set(part, fitted);
  }

  /** Debug: set a control's state without checking the rules. */
  forceOperated(control: string, operated: boolean): void {
    this.operated.set(control, operated);
  }

  /** Part has left its slot. */
  markRemoved(part: string): void {
    this.fitted.set(part, false);
  }

  /**
   * Part is back in its slot. Momentary controls (tabs, buttons) and DIMM
   * ejectors spring back as it seats; returns the controls that reset.
   */
  markFitted(part: string): string[] {
    this.fitted.set(part, true);
    const info = this.parts.get(part);
    const reset: string[] = [];
    if (info == null) return reset;
    for (const token of info.requires) {
      const c = this.controls.get(token);
      if (c == null || !this.isOperated(token)) continue;
      const autoClose =
        c.motion === 'press' || /^dimm_slot_\d+_clip[FR]$/.test(token);
      if (autoClose) {
        this.operated.set(token, false);
        reset.push(token);
      }
    }
    return reset;
  }

  /** Try to operate (open/undo) or close (refit) a control. */
  canToggle(control: string): Result {
    const c = this.controls.get(control);
    if (c == null) return { ok: false, reason: 'Unknown control.' };
    if (!isV01Control(control)) {
      return { ok: false, reason: `${label(control)}: not in this training yet.` };
    }
    if (needsLidOff(control) && !this.lidOff()) {
      return { ok: false, reason: 'Take the lid off first.' };
    }
    const caddy = control.match(CADDY_SCREW);
    if (caddy != null) {
      const part = `asset_caddy_${caddy[1]}`;
      if (this.isFitted(part)) {
        return { ok: false, reason: `Pull the ${label(part)} out first.` };
      }
    }
    // A screw only turns while the part it holds is in place.
    if (c.motion === 'screw') {
      const held = this.heldBy(control);
      if (held != null && !this.isFitted(held)) {
        return { ok: false, reason: `Fit the ${label(held)} first.` };
      }
    }
    const opening = !this.isOperated(control);
    // Tabs and buttons stay pressed until their part is refitted (a second
    // click must not undo them).
    if (!opening && c.motion === 'press') {
      return { ok: false, reason: `${label(control)} is pressed. It releases when the part is refitted.` };
    }
    if (opening) {
      const missing = this.firstMissing(c.requires);
      if (missing != null) return { ok: false, reason: this.missingText(missing) };
    } else {
      for (const other of this.controls.values()) {
        if (other.requires.includes(control) && this.isOperated(other.name)) {
          return { ok: false, reason: `Close the ${label(other.name)} first.` };
        }
      }
    }
    const order = this.sequenceCheck(c, opening);
    if (!order.ok) return order;
    return { ok: true };
  }

  toggle(control: string): Result & { operated?: boolean } {
    const check = this.canToggle(control);
    if (!check.ok) return check;
    const next = !this.isOperated(control);
    this.operated.set(control, next);
    const pair = this.partnerOf(control);
    if (pair != null) this.operated.set(pair, next);
    return { ok: true, operated: next };
  }

  /** The part whose removal needs this control (the part a screw holds). */
  heldBy(control: string): string | undefined {
    for (const p of this.parts.values()) if (p.requires.includes(control)) return p.name;
    return undefined;
  }

  /** The other ejector of a DIMM slot (they move together). */
  partnerOf(control: string): string | null {
    const m = control.match(DIMM_CLIP);
    if (m == null) return null;
    const other = `${m[1]}_clip${m[2] === 'F' ? 'R' : 'F'}`;
    return this.controls.has(other) ? other : null;
  }

  /** Numbered fasteners (heatsinks) follow order_out / order_in. */
  private sequenceCheck(c: ControlInfo, opening: boolean): Result {
    if (c.seq == null || c.asset == null) return { ok: true };
    const part = this.parts.get(c.asset);
    if (part == null) return { ok: true };
    const order = opening ? part.orderOut : part.orderIn;
    if (order.length === 0) return { ok: true };
    const bySeq = new Map<number, ControlInfo>();
    for (const other of this.controls.values()) {
      if (other.asset === c.asset && other.seq != null) bySeq.set(other.seq, other);
    }
    const expected = order.find((seq) => {
      const other = bySeq.get(seq);
      if (other == null) return false;
      return opening ? !this.isOperated(other.name) : this.isOperated(other.name);
    });
    if (expected != null && expected !== c.seq) {
      const verb = opening ? 'Loosen' : 'Tighten';
      return {
        ok: false,
        reason: `Wrong order. ${verb} screw ${expected} next (order ${order.join('-')}).`,
      };
    }
    return { ok: true };
  }

  /** Short "what next" hint for a part. */
  nextStep(part: string): string {
    const info = this.parts.get(part);
    if (info == null) return '';
    if (!this.isFitted(part)) {
      const refit = this.canRefit(part);
      return refit.ok
        ? 'Bring it back to its slot to refit.'
        : (refit.reason ?? '');
    }
    const remove = this.canRemove(part);
    if (remove.ok) return 'Ready: grab it and pull it out.';
    return remove.reason ?? '';
  }
}
