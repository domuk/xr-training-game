"""Realistic emulator QA: laser clicks + trigger-hold pulls with the right
controller, checked against app state and object positions.

Run from app/ with the dev server up:  python tests/qa/run_qa.py [test ...]
"""
import json
import math
import sys

import iwsdk as q

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = '') -> bool:
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}  {detail}")
    return ok


def dist(a: dict, b: dict) -> float:
    return math.sqrt(sum((a[k] - b[k]) ** 2 for k in 'xyz'))


def add(p: dict, dx=0.0, dy=0.0, dz=0.0) -> dict:
    return {'x': p['x'] + dx, 'y': p['y'] + dy, 'z': p['z'] + dz}


def fmt(p: dict) -> str:
    return '(' + ', '.join(f"{p[k]:.3f}" for k in 'xyz') + ')'


_PANELS: dict[str, int] = {}


def panel_index(node_id: str) -> int:
    if not _PANELS:
        tree = q.result(q.cli('scene', 'runtime-hierarchy', data={'maxDepth': 3}))

        def walk(n: dict) -> None:
            sid = n.get('sceneNodeId')
            if sid in ('tablet', 'hud') and sid not in _PANELS and n.get('entityIndex') is not None:
                _PANELS[sid] = n['entityIndex']
            for c in n.get('children', []) or []:
                walk(c)

        walk(tree)
    return _PANELS[node_id]


def ui_pos(panel_node: str, element_id: str) -> dict:
    r = q.result(q.cli('ui', 'inspect', data={
        'entityIndex': panel_index(panel_node), 'selector': f'#{element_id}'}))
    uuid = r['elements'][0]['uuid']
    t = q.result(q.cli('scene', 'transform', data={'uuid': uuid}))
    return q.vec(t.get('positionRelativeToXROrigin') or t['globalPosition'])


def ui_text(panel_node: str, element_id: str) -> str:
    r = q.result(q.cli('ui', 'inspect', data={
        'entityIndex': panel_index(panel_node), 'selector': f'#{element_id}'}))
    return r['elements'][0].get('text', '')


TAB_OF = {'dbg': 'tab-debug', 'srv': 'tab-server', 'btn-reset': 'tab-lab', 'btn-hud': 'tab-lab'}


def ui_click(panel_node: str, element_id: str) -> None:
    """Aim the laser at a tablet button and click it (trigger).

    Old panel names map to the tablet; open the right tab first.
    """
    if panel_node != 'hud':
        panel_node = 'tablet'
        for prefix, tab in TAB_OF.items():
            if element_id.startswith(prefix):
                q.aim(ui_pos('tablet', tab), distance=0.5)
                q.click()
    q.aim(ui_pos(panel_node, element_id), distance=0.5)
    q.click()


def setup() -> None:
    q.enter_xr()
    q.reset_devices()
    q.wait(1.5)  # app re-places server + panels on XR entry
    q.load_uuids()
    to_training()


def to_training() -> None:
    """Start -> (place) Next -> training; if already training, Reset."""
    q.cli('xr', 'set-input-mode', data={'mode': 'controller'})
    if ui_text('tablet', 'btn-start-lab-label') == 'Start lab':
        ui_click('tablet', 'btn-start-lab')
    else:
        ui_click('tablet', 'btn-reset')
    q.reset_devices()
    q.wait(0.8)


def start_training() -> None:
    check('Start lab unlocked the tablet', ui_text('tablet', 'btn-start-lab-label') == 'Back to lab',
          ui_text('tablet', 'btn-start-lab-label'))


def test_place() -> None:
    """Fresh page: Start, then drag the server with the laser, then Next."""
    q.cli('browser', 'reload')
    q.wait(6)
    q.enter_xr()
    q.reset_devices()
    q.wait(1.5)
    _PANELS.clear()
    q.load_uuids()
    ui_click('info-panel', 'btn-start')
    check('Start -> place step (button says Next)',
          ui_text('info-panel', 'btn-start-label') == 'Next', ui_text('info-panel', 'btn-start-label'))
    start = q.world_pos('server_root')
    # Point at the server front and drag it 20 cm to the right.
    aim_from_front(add(start, 0, 0.04, 0.0), up=0.1, back=0.4)
    c0 = q.ctrl_pos()
    q.trigger(1)
    q.move_ctrl(add(c0, 0.2, 0, 0), 0.8)
    q.trigger(0)
    after = q.world_pos('server_root')
    check('laser drag moves the server while placing', dist(start, after) > 0.08,
          f'{fmt(start)} -> {fmt(after)}')
    ui_click('info-panel', 'btn-start')
    check('Next -> training', ui_text('info-panel', 'btn-start-label') == 'Reset server',
          ui_text('info-panel', 'btn-start-label'))
    q.load_uuids()


def test_grip_fan() -> None:
    """Controller grip up close (no laser) pulls the fan out."""
    ui_click('debug-panel', 'dbg-lid')
    fan = q.world_pos('asset_fan_01')
    q.set_ctrl(add(fan, 0, 0.02, 0))
    q.cli('xr', 'set-gamepad-state', data={'device': 'controller-right', 'buttons': [{'index': 1, 'value': 1}]})
    q.wait(0.4)
    q.move_ctrl(add(fan, 0, 0.27, 0), 0.8)
    held = q.world_pos('asset_fan_01')
    q.cli('xr', 'set-gamepad-state', data={'device': 'controller-right', 'buttons': [{'index': 1, 'value': 0}]})
    q.wait(0.5)
    check('grip near fan moves it', dist(fan, held) > 0.05, f'{fmt(fan)} -> {fmt(held)}')
    check('fan out (free)', q.part_state('asset_fan_01') == 'free', q.part_state('asset_fan_01'))


def test_hand_pinch_dimm() -> None:
    """Hands: click an ejector with the laser, pinch the DIMM up close, lift."""
    ui_click('debug-panel', 'dbg-lid')
    laser_click('dimm_slot_01_clipF', up=0.2, back=0.15)
    check('one click opened both ejectors', q.operated('dimm_slot_01_clipR'))
    q.cli('xr', 'set-input-mode', data={'mode': 'hand'})
    q.wait(0.8)
    dimm = q.world_pos('asset_dimm_01')
    # Put the hand so the index tip is at the DIMM top edge.
    q.cli('xr', 'set-transform', data={'device': 'hand-right', 'position': add(dimm, 0, 0.03, 0.0)})
    q.wait(0.4)
    q.cli('xr', 'set-select-value', data={'device': 'hand-right', 'value': 1})
    q.wait(0.4)
    q.cli('xr', 'animate-to', data={'device': 'hand-right', 'position': add(dimm, 0, 0.25, 0), 'duration': 0.8})
    q.wait(1.2)
    held = q.world_pos('asset_dimm_01')
    q.cli('xr', 'set-select-value', data={'device': 'hand-right', 'value': 0})
    q.wait(0.5)
    q.cli('xr', 'set-input-mode', data={'mode': 'controller'})
    check('hand pinch moves the DIMM', dist(dimm, held) > 0.05, f'{fmt(dimm)} -> {fmt(held)}')
    check('DIMM out (free)', q.part_state('asset_dimm_01') == 'free', q.part_state('asset_dimm_01'))


def test_placement() -> None:
    head = q.vec(q.result(q.cli('xr', 'get-transform', data={'device': 'headset'}))['position'])
    server = q.world_pos('server_root')
    check('server placed in front of the user at chest height',
          0.3 < (head['y'] - server['y']) < 0.8 and 0.3 < dist(
              {'x': head['x'], 'y': 0, 'z': head['z']},
              {'x': server['x'], 'y': 0, 'z': server['z']}) < 0.7,
          f'head {fmt(head)} server {fmt(server)}')


def aim_from_front(target: dict, up: float = 0.15, back: float = 0.25) -> None:
    """Hold the controller in front of / above the target, like a user would."""
    q.set_ctrl(add(target, 0, up, back))
    q.aim(target)


def laser_click(name: str, up: float = 0.15, back: float = 0.25) -> None:
    aim_from_front(q.world_pos(name), up, back)
    q.click()


def laser_pull(name: str, offset: dict, steps: int = 4, aim_offset: dict | None = None,
               up: float = 0.15, back: float = 0.25) -> tuple[dict, dict]:
    """Aim at `name` (+aim_offset), hold trigger, move the controller by `offset`, release."""
    start = q.world_pos(name)
    o = aim_offset or {'x': 0, 'y': 0, 'z': 0}
    aim_from_front(add(start, o['x'], o['y'], o['z']), up, back)
    c0 = q.ctrl_pos()
    q.trigger(1)
    for i in range(1, steps + 1):
        f = i / steps
        q.move_ctrl(add(c0, offset['x'] * f, offset['y'] * f, offset['z'] * f), duration=0.4)
    mid = q.world_pos(name)
    q.trigger(0)
    q.wait(0.6)
    return start, mid


def test_lid() -> None:
    laser_click('lid_tab_L')
    check('lid tab L clicked', q.operated('lid_tab_L'))
    laser_click('lid_tab_R')
    check('lid tab R clicked', q.operated('lid_tab_R'))
    # Lid slides back 15 mm then lifts: pull the controller back + up.
    # Aim at the middle of the lid top (its pivot is on the front edge).
    start, held = laser_pull('asset_lid', {'x': 0, 'y': 0.25, 'z': 0.05},
                             aim_offset={'x': 0, 'y': 0.0, 'z': -0.25}, up=0.3, back=0.2)
    check('lid moved while held', dist(start, held) > 0.03, f'{fmt(start)} -> {fmt(held)}')
    check('lid is out (free)', q.part_state('asset_lid') == 'free', q.part_state('asset_lid'))


def remove_lid_by_hand() -> None:
    laser_click('lid_tab_L')
    laser_click('lid_tab_R')
    laser_pull('asset_lid', {'x': 0, 'y': 0.25, 'z': 0.05},
               aim_offset={'x': 0, 'y': 0.0, 'z': -0.25}, up=0.3, back=0.2)


def test_caddy() -> None:
    laser_click('caddy_01_button', up=0.05, back=0.3)
    check('caddy button pressed', q.operated('caddy_01_button'))
    laser_click('caddy_01_handle', up=0.05, back=0.3)
    check('caddy handle open', q.operated('caddy_01_handle'))
    # Pull it out by the open handle arm: point at it, hold, pull back.
    start, held = laser_pull('caddy_01_handle', {'x': 0, 'y': 0, 'z': 0.3}, up=0.05, back=0.3)
    check('caddy moved while held', dist(start, held) > 0.05, f'{fmt(start)} -> {fmt(held)}')
    check('caddy is out (free)', q.part_state('asset_caddy_01') == 'free',
          q.part_state('asset_caddy_01'))


def test_fan_inside() -> None:
    remove_lid_by_hand()
    check('lid out first', q.part_state('asset_lid') == 'free', q.part_state('asset_lid'))
    start, held = laser_pull('asset_fan_01', {'x': 0, 'y': 0.25, 'z': 0.0}, up=0.25, back=0.15)
    check('fan moved while held', dist(start, held) > 0.05, f'{fmt(start)} -> {fmt(held)}')
    check('fan is out (free)', q.part_state('asset_fan_01') == 'free', q.part_state('asset_fan_01'))


def test_debug_lid_and_reset() -> None:
    ui_click('debug-panel', 'dbg-lid')
    check('debug lid off -> lid gone', q.part_state('asset_lid') == 'gone', q.part_state('asset_lid'))
    laser_click('dimm_slot_01_clipF', up=0.2, back=0.15)
    check('inside clickable after debug lid off (DIMM ejector)', q.operated('dimm_slot_01_clipF'))
    ui_click('debug-panel', 'dbg-reset')
    check('reset -> lid fitted', q.part_state('asset_lid') == 'fitted', q.part_state('asset_lid'))
    check('reset -> ejector closed', not q.operated('dimm_slot_01_clipF'))


def test_moved_server() -> None:
    before = q.world_pos('server_root')
    ui_click('debug-panel', 'dbg-further')
    ui_click('debug-panel', 'dbg-up')
    after = q.world_pos('server_root')
    check('debug moved the server', dist(before, after) > 0.03, f'{fmt(before)} -> {fmt(after)}')
    test_caddy()


def test_exploded_grab() -> None:
    ui_click('debug-panel', 'dbg-explode')
    check('exploded: DIMM out', q.part_state('asset_dimm_01') == 'free', q.part_state('asset_dimm_01'))
    start, held = laser_pull('asset_dimm_01', {'x': 0.15, 'y': 0.0, 'z': 0.0}, up=0.2, back=0.2)
    check('grab a part from exploded view', dist(start, held) > 0.05, f'{fmt(start)} -> {fmt(held)}')
    ui_click('debug-panel', 'dbg-reset')


TESTS = {
    'placement': test_placement,
    'start': start_training,
    'place': test_place,
    'gripfan': test_grip_fan,
    'pinchdimm': test_hand_pinch_dimm,
    'lid': test_lid,
    'caddy': test_caddy,
    'fan': test_fan_inside,
    'debuglid': test_debug_lid_and_reset,
    'moved': test_moved_server,
    'exploded': test_exploded_grab,
}


def main(names: list[str]) -> None:
    setup()
    for n in names or list(TESTS):
        print(f'--- {n}')
        if n not in ('placement', 'start', 'place'):
            to_training()  # Reset server between tests
        try:
            TESTS[n]()
        except Exception as e:  # keep going, report the failure
            check(f'{n} ran', False, repr(e)[:300])
    failed = [r for r in RESULTS if not r[1]]
    print(f'\n{len(RESULTS) - len(failed)}/{len(RESULTS)} passed')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main(sys.argv[1:])
