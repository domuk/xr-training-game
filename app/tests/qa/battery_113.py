"""Quick checks for the post-1.2.0 bug fixes (emulator). Run with the dev server up."""
import math
import sys
import time

import iwsdk as q
from run_qa import ui_click, ui_text, check, RESULTS, add, dist, fmt
import battery_112 as b


def stick(device, x=0.0, y=0.0):
    q.cli('xr', 'set-gamepad-state', data={'device': device, 'axes': [{'index': 0, 'value': x}, {'index': 1, 'value': y}]})


def yaw_of(name):
    t = q.transform(name)
    qx, qy, qz, qw = (t.get('globalQuaternion') or [0, 0, 0, 1])[:4] if isinstance(t.get('globalQuaternion'), list) else (
        t['globalQuaternion']['x'], t['globalQuaternion']['y'], t['globalQuaternion']['z'], t['globalQuaternion']['w'])
    # forward (+Z) rotated, projected on XZ
    fx = 2 * (qx * qz + qw * qy)
    fz = 1 - 2 * (qx * qx + qy * qy)
    return math.degrees(math.atan2(fx, fz))


def t_swap():
    title0 = ui_text('tablet', 'info-title')
    b.grip(1, 'controller-left'); b.grip(0, 'controller-left')
    q.wait(1.0)
    single = ui_text('tablet', 'info-title')
    b.grip(1, 'controller-left'); b.grip(0, 'controller-left')
    b.grip(1, 'controller-left'); b.grip(0, 'controller-left')
    q.wait(0.6)
    double = ui_text('tablet', 'info-title')
    check('#6/#7 single grip does not swap', single != 'Left hand', f'{title0} -> {single}')
    check('#6/#7 double grip swaps to hand', double == 'Left hand', double)


def t_table_and_spin():
    ui_click('tablet', 'srv-here')
    q.wait(0.8)
    s0 = q.world_pos('server_root')
    hand = add(s0, 0.27, 0.044, -0.35)  # right side, middle (server facing you)
    q.set_ctrl(hand)
    b.grip(1)
    y0 = yaw_of('server_root')
    stick('controller-right', x=1.0)
    q.wait(1.2)
    stick('controller-right', 0, 0)
    y1 = yaw_of('server_root')
    check('#9 right stick spins the held server', abs(((y1 - y0) + 180) % 360 - 180) > 20, f'{y0:.0f} -> {y1:.0f} deg')
    b.walk_to('controller-right', add(q.ctrl_pos(), 0, -0.5, 0))
    s1 = q.world_pos('server_root')
    b.grip(0)
    check('#5 server stops on the table top (not inside)', s1['y'] > 0.97, f'{fmt(s0)} -> {fmt(s1)}')


def t_hall():
    d0 = q.world_pos('door_leaf_W')
    q.aim(add(d0, 0.45, 1.0, 0), distance=0.8)
    q.click()
    q.wait(6)
    q.load_uuids()
    t0 = q.transform('hot_aisle_1_door_S_W')
    lab_door = q.world_pos('door_leaf_W')  # lab door (hidden) relative to you
    origin = {'x': -0.2 - lab_door['x'], 'y': 0, 'z': 4.17 - lab_door['z']}
    world = {'x': -5.97 - 0.25, 'y': 1.0, 'z': 2.478}
    rel = {k: world[k] - origin[k] for k in 'xyz'}
    q.aim(rel, distance=0.8)
    q.click()
    q.wait(1.2)
    t1 = q.transform('hot_aisle_1_door_S_W')
    p0, p1 = t0.get('localPosition'), t1.get('localPosition')
    check('#1 hall: a hot-aisle door slides on a click', p0 != p1, f'{p0} -> {p1}')


def main():
    b.setup()
    for name, fn in [('swap', t_swap), ('table + spin', t_table_and_spin), ('hall', t_hall)]:
        print(f'--- {name}')
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            check(f'{name} ran', False, repr(e)[:200])
    failed = [r for r in RESULTS if not r[1]]
    print(f'\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
