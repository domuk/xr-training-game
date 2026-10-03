// Run: npm test  (Node strips the TypeScript types itself)
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import {
  type ControlInfo,
  type PartInfo,
  parseOrder,
  ServiceRules,
  splitList,
} from '../src/service/rules.ts';

const manifest = JSON.parse(
  readFileSync(new URL('../public/gltf/server/server_manifest.json', import.meta.url), 'utf8'),
);

function load(): ServiceRules {
  const parts: PartInfo[] = Object.entries<any>(manifest.assets).map(([name, a]) => ({
    name,
    parent: a.parent_asset ?? null,
    requires: splitList(a.requires),
    pull: a.pull ?? [],
    orderOut: parseOrder(a.order_out),
    orderIn: parseOrder(a.order_in),
    tip: a.tip,
  }));
  const controls: ControlInfo[] = [
    ...Object.entries<any>(manifest.moving),
    ...Object.entries<any>(manifest.fasteners),
  ].map(([name, c]) => ({
    name,
    asset: c.asset ?? null,
    motion: c.motion,
    axis: c.axis,
    limits: c.limits,
    requires: splitList(c.requires),
    seq: c.seq,
    optional: !!c.optional,
    captive: !!c.captive,
    rise: c.rise ?? 0,
  }));
  return new ServiceRules(parts, controls);
}

test('lid: tabs first, screw optional, then everything inside unlocks', () => {
  const r = load();
  assert.equal(r.canRemove('asset_fan_01').reason, 'Take the lid off first.');
  assert.equal(r.canRemove('asset_lid').ok, false);
  assert.ok(r.toggle('lid_tab_L').ok);
  assert.equal(r.canRemove('asset_lid').ok, false);
  assert.ok(r.toggle('lid_tab_R').ok);
  assert.ok(r.canRemove('asset_lid').ok, 'lid screw is optional');
  r.markRemoved('asset_lid');
  assert.ok(r.canRemove('asset_fan_01').ok, 'fan just pulls out (no release tab)');
});

test('lid refit springs the tabs back', () => {
  const r = load();
  r.toggle('lid_tab_L');
  r.toggle('lid_tab_R');
  r.markRemoved('asset_lid');
  assert.ok(r.canRefit('asset_lid').ok);
  assert.deepEqual(r.markFitted('asset_lid').sort(), ['lid_tab_L', 'lid_tab_R']);
  assert.equal(r.isOperated('lid_tab_L'), false);
});

test('caddy needs button + handle; drive needs caddy out + 4 screws', () => {
  const r = load();
  assert.equal(r.canRemove('asset_caddy_01').ok, false);
  assert.equal(r.canRemove('asset_drive_01').ok, false);
  assert.equal(r.canToggle('caddy_01_screw_1').ok, false, 'screw hidden in bay');
  r.toggle('caddy_01_button');
  r.toggle('caddy_01_handle');
  assert.ok(r.canRemove('asset_caddy_01').ok);
  r.markRemoved('asset_caddy_01');
  for (const k of [1, 2, 3, 4]) assert.ok(r.toggle(`caddy_01_screw_${k}`).ok);
  assert.ok(r.canRemove('asset_drive_01').ok);
  r.markRemoved('asset_drive_01');
  assert.equal(r.canRefit('asset_caddy_01').ok, false, 'drive must go back first');
  r.markFitted('asset_drive_01');
  assert.ok(r.canRefit('asset_caddy_01').ok);
});

test('heatsink screws: out 4-3-2-1, in 1-2-3-4', () => {
  const r = load();
  r.markRemoved('asset_lid');
  const wrong = r.toggle('hs_1_screw_1');
  assert.equal(wrong.ok, false);
  assert.match(wrong.reason ?? '', /Loosen screw 4 next/);
  for (const k of [4, 3, 2, 1]) assert.ok(r.toggle(`hs_1_screw_${k}`).ok, `out ${k}`);
  assert.ok(r.canRemove('asset_hs_1').ok);
  assert.match(r.toggle('hs_1_screw_4').reason ?? '', /Tighten screw 1 next/);
  for (const k of [1, 2, 3, 4]) assert.ok(r.toggle(`hs_1_screw_${k}`).ok, `in ${k}`);
});

test('CPU: heatsink off, lever then plate; close plate before lever', () => {
  const r = load();
  r.markRemoved('asset_lid');
  assert.match(r.toggle('socket_1_lever').reason ?? '', /Heatsink 1/);
  for (const k of [4, 3, 2, 1]) r.toggle(`hs_1_screw_${k}`);
  r.markRemoved('asset_hs_1');
  assert.equal(r.toggle('socket_1_plate').ok, false, 'lever first');
  assert.ok(r.toggle('socket_1_lever').ok);
  assert.ok(r.toggle('socket_1_plate').ok);
  assert.ok(r.canRemove('asset_cpu_1').ok);
  r.markRemoved('asset_cpu_1');
  assert.ok(r.canRefit('asset_cpu_1').ok);
  r.markFitted('asset_cpu_1');
  assert.match(r.toggle('socket_1_lever').reason ?? '', /load plate/);
  assert.ok(r.toggle('socket_1_plate').ok);
  assert.ok(r.toggle('socket_1_lever').ok);
});

test('DIMM: one click opens both ejectors; refit closes them', () => {
  const r = load();
  r.markRemoved('asset_lid');
  assert.equal(r.canRemove('asset_dimm_01').ok, false);
  r.toggle('dimm_slot_01_clipF');
  assert.ok(r.isOperated('dimm_slot_01_clipR'), 'partner ejector opens too');
  assert.ok(r.canRemove('asset_dimm_01').ok);
  r.markRemoved('asset_dimm_01');
  assert.deepEqual(r.markFitted('asset_dimm_01').length, 2);
});

test('pressed tabs stay pressed until refit', () => {
  const r = load();
  assert.ok(r.toggle('lid_tab_L').ok);
  assert.equal(r.toggle('lid_tab_L').ok, false, 'second click does not undo it');
  assert.ok(r.isOperated('lid_tab_L'));
});

test('parts outside v0.1 are locked with a message', () => {
  const r = load();
  r.markRemoved('asset_lid');
  assert.match(r.canRemove('asset_psu_1').reason ?? '', /not in this training yet/);
  assert.match(r.canRemove('asset_backplane').reason ?? '', /not in this training yet/);
});

test('every v0.1 part can be removed by following the rules', () => {
  const r = load();
  // Open everything that is allowed, repeatedly, until nothing changes.
  const v01 = [...r.parts.keys()].filter((p) => r.canRemove(p).reason?.includes('not in') !== true);
  let changed = true;
  while (changed) {
    changed = false;
    for (const c of r.controls.keys()) {
      if (!r.isOperated(c) && r.canToggle(c).ok) {
        r.toggle(c);
        changed = true;
      }
    }
    for (const p of v01) {
      if (r.isFitted(p) && r.canRemove(p).ok) {
        r.markRemoved(p);
        changed = true;
      }
    }
  }
  const stuck = v01.filter((p) => r.isFitted(p));
  assert.deepEqual(stuck, []);
});

/** Lid off, ready for work inside. */
function opened(): ServiceRules {
  const r = load();
  r.toggle('lid_tab_L');
  r.toggle('lid_tab_R');
  r.markRemoved('asset_lid');
  return r;
}

function undoHeatsink(r: ServiceRules, k: number): void {
  for (const s of [4, 3, 2, 1]) assert.ok(r.toggle(`hs_${k}_screw_${s}`).ok);
  r.markRemoved(`asset_hs_${k}`);
}

test('CPU: heatsink off, then lever up, then plate up', () => {
  const r = opened();
  assert.equal(r.canRemove('asset_cpu_1').ok, false);
  assert.equal(r.toggle('socket_1_lever').ok, false, 'heatsink still on');
  undoHeatsink(r, 1);
  assert.equal(r.toggle('socket_1_plate').ok, false, 'lever first');
  assert.equal(r.canRemove('asset_cpu_1').ok, false);
  assert.ok(r.toggle('socket_1_lever').ok);
  assert.equal(r.canRemove('asset_cpu_1').ok, false, 'plate still down');
  assert.ok(r.toggle('socket_1_plate').ok);
  assert.ok(r.canRemove('asset_cpu_1').ok);
  r.markRemoved('asset_cpu_1');
  // Putting back: socket must be open; heatsink screws can't turn while it's out.
  assert.equal(r.toggle('hs_1_screw_1').ok, false);
  assert.equal(r.canRefit('asset_cpu_1').ok, true);
  assert.equal(r.toggle('socket_1_lever').ok, false, 'plate closes before the lever');
});

test('motherboard: screws, cards, shroud, DIMMs and CPUs first; cables ignored', () => {
  const r = opened();
  const req = r.parts.get('asset_board')!.requires;
  assert.ok(!req.some((t) => /cable|plug/.test(t)), 'cables are skipped');
  for (const t of req) {
    if (r.parts.has(t)) {
      if (/^asset_hs|^asset_cpu/.test(t)) continue;
      r.forceFitted(t, false);
    } else r.forceOperated(t, true);
  }
  assert.match(r.canRemove('asset_board').reason ?? '', /CPU/);
  r.forceFitted('asset_cpu_1', false);
  r.forceFitted('asset_cpu_2', false);
  assert.ok(r.canRemove('asset_board').ok);
  r.markRemoved('asset_board');
  assert.equal(r.canRefit('asset_dimm_01').reason, 'Fit the Motherboard first.');
  assert.equal(r.toggle('board_screw_1').reason, 'Fit the Motherboard first.');
});

test('board screws need the lid off and turn with the board in', () => {
  const r = load();
  assert.equal(r.toggle('board_screw_1').reason, 'Take the lid off first.');
  const o = opened();
  assert.ok(o.toggle('board_screw_1').ok);
});
