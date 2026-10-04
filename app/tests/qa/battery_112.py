"""1.1.2 bug battery (emulator). Run with the dev server up:
    python tests/qa/battery_112.py
Each check prints PASS / FAIL; screenshots for the visual ones are listed at the end.
"""
import math
import sys
import time

import iwsdk as q
from run_qa import ui_click, laser_click, check, RESULTS, add, dist, fmt

SHOTS = []
HOME = {}


def shot(label):
    r = q.cli('browser', 'screenshot')
    path = r.get('screenshotPath') or (r.get('data') or {}).get('screenshotPath')
    SHOTS.append((label, path))


def grip(value, device='controller-right'):
    q.cli('xr', 'set-gamepad-state', data={'device': device, 'buttons': [{'index': 1, 'value': value}]})
    q.wait(0.4)


def walk_to(device, target, steps=6, duration=0.25):
    start = q.ctrl_pos(device)
    for i in range(1, steps + 1):
        t = i / steps
        p = {k: start[k] + (target[k] - start[k]) * t for k in 'xyz'}
        q.move_ctrl(p, duration, device)


def lab_click(name, offset=(0, 0, 0), distance=0.5):
    q.aim(add(q.world_pos(name), *offset), distance=distance)
    q.click()


def setup():
    q.cli('browser', 'reload')
    q.cli('runtime', 'wait')
    time.sleep(4)
    q.enter_xr()
    time.sleep(4)
    q.load_uuids()
    HOME.update(q.ctrl_pos())
    ui_click('tablet', 'btn-start-lab')
    time.sleep(1)


def server_side_point(server, yaw_deg=90):
    # Server front faces east (+X) when racked; its right side (local +X) faces north (-Z).
    # Local (x=0.27, y=0.044, z=-0.35) -> world offset (z, y, -x) for yaw 90.
    return add(server, -0.35, 0.044, -0.27)


def t_rack_out_and_float():
    s0 = q.world_pos('server_root')
    hand = server_side_point(s0)
    q.set_ctrl(hand)
    grip(1)
    walk_to('controller-right', add(hand, 0.45, 0, 0))
    s1 = q.world_pos('server_root')
    check('#1 server slides out of the rack (east)', s1['x'] - s0['x'] > 0.3, f'{fmt(s0)} -> {fmt(s1)}')
    check('#13 out along the rails (no sideways drift)', abs(s1['z'] - s0['z']) < 0.02 and abs(s1['y'] - s0['y']) < 0.02, fmt(s1))
    walk_to('controller-right', add(hand, 0.95, 0, 0))
    walk_to('controller-right', add(hand, 0.95, 0, 0.3))
    s2 = q.world_pos('server_root')
    check('#2/#12 one hand carries it once out (moved south)', s2['z'] - s1['z'] > 0.15, f'{fmt(s1)} -> {fmt(s2)}')
    grip(0)
    q.wait(1.0)
    s3 = q.world_pos('server_root')
    check('#4 released server floats (no fall)', dist(s2, s3) < 0.02, f'{fmt(s2)} -> {fmt(s3)}')
    return s0, s3


def t_parts_accessible():
    laser_click('lid_tab_L', up=0.25, back=0.3)
    laser_click('lid_tab_R', up=0.25, back=0.3)
    check('#7 server parts work once out of the rack (lid tabs)', q.operated('lid_tab_L') and q.operated('lid_tab_R'))


def t_collision():
    q.set_ctrl(dict(HOME))  # click the tablet from in front
    q.wait(0.3)
    ui_click('tablet', 'dbg-lid')
    q.wait(0.6)
    fan = q.world_pos('asset_fan_01')
    fan = add(fan, -0.04, 0, 0)  # onto the fan body (its origin is at the drive-bay side)
    q.set_ctrl(add(fan, 0, 0.02, 0))
    grip(1)
    q.move_ctrl(add(fan, 0, 0.3, 0), 0.8)
    q.move_ctrl(add(fan, 0, 0.3, 0.6), 0.8)
    fans = ['asset_fan_01', 'asset_fan_02', 'asset_fan_03']
    grabbed = next((f for f in fans if q.part_state(f) == 'free'), 'asset_fan_01')
    out = q.world_pos(grabbed)
    server = q.world_pos('server_root')
    # Push it back at mid height towards the server's front (far from its own slot).
    front = add(server, 0.05, 0.05, 0)
    walk_to('controller-right', front, steps=8)
    end = q.world_pos(grabbed)
    grip(0)
    check('#5 a fan was pulled out (free)', q.part_state(grabbed) == 'free', grabbed + ' ' + q.part_state(grabbed))
    check('#5 free fan stopped outside the server (did not reach its front)', dist(end, front) > 0.08, f'{fmt(out)} -> {fmt(end)} (front {fmt(front)})')
    q.wait(1.0)
    after = q.world_pos(grabbed)
    check('#4 released fan floats', dist(end, after) < 0.02, f'{fmt(end)} -> {fmt(after)}')


def t_rack_in(slot_pos):
    s = q.world_pos('server_root')
    # Re-grab by the side, bring it back in front of the slot, push it in.
    hand = server_side_point(s)
    q.set_ctrl(hand)
    grip(1)
    target_front = add(slot_pos, 0.5, 0, 0)
    # Keep the hand at the same spot on the server's side while moving it.
    off = {k: hand[k] - s[k] for k in 'xyz'}
    walk_to('controller-right', add(target_front, off['x'], off['y'], off['z']), steps=8)
    walk_to('controller-right', add(slot_pos, off['x'] + 0.05, off['y'], off['z']), steps=6)
    grip(0)
    q.wait(1.2)
    end = q.world_pos('server_root')
    check('#13 server slides back into the rack slot', dist(end, slot_pos) < 0.05, f'{fmt(end)} vs slot {fmt(slot_pos)}')


def t_cabinet():
    d0 = q.world_pos('lab_cabinet_drawer_1')
    lab_click('lab_cabinet_drawer_1', (0, 0.08, 0))
    q.wait(0.8)
    d1 = q.world_pos('lab_cabinet_drawer_1')
    check('#6 drawer stays shut while the doors are shut', dist(d0, d1) < 0.01, f'{fmt(d0)} -> {fmt(d1)}')
    lab_click('lab_cabinet_door_L', (0, 0.9, -0.25))
    lab_click('lab_cabinet_door_R', (0, 0.9, 0.25))
    q.wait(0.8)
    lab_click('lab_cabinet_drawer_1', (0, 0.08, 0))
    q.wait(0.8)
    d2 = q.world_pos('lab_cabinet_drawer_1')
    check('#6 drawer opens once both doors are open', dist(d0, d2) > 0.2, f'{fmt(d0)} -> {fmt(d2)}')


def t_prop():
    p0 = q.world_pos('prop_screwdriver')
    q.aim(p0, distance=0.6)
    q.trigger(1)
    ctrl = q.ctrl_pos()
    q.move_ctrl(add(ctrl, 0, 0.3, 0.2), 0.8)
    p1 = q.world_pos('prop_screwdriver')
    q.trigger(0)
    q.wait(1.0)
    p2 = q.world_pos('prop_screwdriver')
    check('#19 drawer screwdriver moves with the laser', dist(p0, p1) > 0.1, f'{fmt(p0)} -> {fmt(p1)}')
    check('#19 released screwdriver floats (no fall)', dist(p1, p2) < 0.02, f'{fmt(p1)} -> {fmt(p2)}')


def t_tablet_server_buttons():
    q.set_ctrl(dict(HOME))  # click from in front, like a player
    q.wait(0.3)
    s0 = q.world_pos('server_root')
    ui_click('tablet', 'srv-up')
    q.wait(0.5)
    s1 = q.world_pos('server_root')
    check('#11 Server page: Up moves the server', s1['y'] - s0['y'] > 0.03, f'{fmt(s0)} -> {fmt(s1)}')
    ui_click('tablet', 'srv-here')
    q.wait(0.5)
    s2 = q.world_pos('server_root')
    check('#11 Server page: Bring here moves the server', dist(s1, s2) > 0.1, f'{fmt(s1)} -> {fmt(s2)}')


def t_visuals():
    # Long laser at the far wall, dot on the tablet: screenshots for review.
    q.aim({'x': 0, 'y': 1.5, 'z': -4}, distance=0.4)
    shot('#15 laser towards the far wall')
    tab = q.world_pos('tablet_body')
    q.aim(tab, distance=0.4)
    shot('#17 laser dot + hover on the tablet')


TESTS = [
    ('rack out + float', t_rack_out_and_float),
]


def main():
    setup()
    slot = q.world_pos('server_root')
    for name, fn in [
        ('cabinet', t_cabinet),
        ('prop', t_prop),
        ('rack out', t_rack_out_and_float),
        ('parts', t_parts_accessible),
        ('collision', t_collision),
        ('rack in', lambda: t_rack_in(slot)),
        ('tablet server buttons', t_tablet_server_buttons),
        ('visuals', t_visuals),
    ]:
        print(f'--- {name}')
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            check(f'{name} ran', False, repr(e)[:160])
    failed = [r for r in RESULTS if not r[1]]
    print(f'\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed')
    for label, path in SHOTS:
        print(f'SHOT {label}: {path}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
