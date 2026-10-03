"""Tiny helper around the IWSDK CLI for emulator QA (run from app/).

Drives the emulated Quest 3 the way a user would: aim the controller laser,
press the trigger, move the controller, then reads back app state
(ServicePart.state / ServiceControl.operated) and object positions.
"""
import json
import subprocess
import time

_UUIDS: dict[str, str] = {}


def cli(*args: str, data: dict | None = None, timeout: int = 60) -> dict:
    cmd = ['npx.cmd', 'iwsdk', *args]
    if data is not None:
        cmd += ['--input-json', json.dumps(data)]
    out = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout, shell=False,
        encoding='utf-8', errors='replace',
    ).stdout
    start = out.find('{')
    if start < 0:
        raise RuntimeError(f'no JSON from {args}: {out[:300]}')
    env = json.loads(out[start:])
    if not env.get('ok', False):
        raise RuntimeError(f'{args} failed: {json.dumps(env)[:500]}')
    return env.get('data', env)


def result(d: dict) -> dict:
    return d.get('result', d)


def vec(v) -> dict:
    """Accept [x, y, z] or {x, y, z}."""
    if isinstance(v, (list, tuple)):
        return {'x': v[0], 'y': v[1], 'z': v[2]}
    return {'x': v['x'], 'y': v['y'], 'z': v['z']}


def wait(s: float) -> None:
    time.sleep(s)


# ------------------------------------------------------------------ XR


def xr_status() -> dict:
    return result(cli('xr', 'status'))


def enter_xr() -> None:
    st = xr_status()
    if not (st.get('sessionActive') or st.get('active')):
        cli('xr', 'enter', data={})
        wait(2)


def reset_devices() -> None:
    cli('xr', 'set-device-state', data={})
    wait(0.5)


def set_ctrl(pos: dict, device: str = 'controller-right') -> None:
    cli('xr', 'set-transform', data={'device': device, 'position': pos})


def ctrl_pos(device: str = 'controller-right') -> dict:
    return vec(result(cli('xr', 'get-transform', data={'device': device}))['position'])


def aim(target: dict, distance: float | None = None, device: str = 'controller-right') -> None:
    data = {'device': device, 'target': target}
    if distance is not None:
        data['moveToDistance'] = distance
    cli('xr', 'look-at', data=data)
    wait(0.3)


def trigger(value: float, device: str = 'controller-right') -> None:
    cli('xr', 'set-select-value', data={'device': device, 'value': value})
    wait(0.3)


def click(device: str = 'controller-right') -> None:
    cli('xr', 'select', data={'device': device, 'duration': 0.15})
    wait(0.5)


def move_ctrl(pos: dict, duration: float = 0.8, device: str = 'controller-right') -> None:
    cli('xr', 'animate-to', data={'device': device, 'position': pos, 'duration': duration})
    wait(duration + 0.4)


# --------------------------------------------------------------- scene


def load_uuids() -> None:
    _UUIDS.clear()
    tree = result(cli('scene', 'runtime-hierarchy', data={'maxDepth': 30}, timeout=120))

    def walk(node: dict) -> None:
        name = node.get('name')
        if name and name not in _UUIDS:
            _UUIDS[name] = node.get('uuid')
        for c in node.get('children', []) or []:
            walk(c)

    walk(tree.get('hierarchy', tree))


def transform(name: str) -> dict:
    if name not in _UUIDS:
        load_uuids()
    return result(cli('scene', 'transform', data={'uuid': _UUIDS[name]}))


def _qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def _qrot(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    # v' = q v q*
    ix = w * vx + y * vz - z * vy
    iy = w * vy + z * vx - x * vz
    iz = w * vz + x * vy - y * vx
    iw = -x * vx - y * vy - z * vz
    return (ix * w + iw * -x + iy * -z - iz * -y,
            iy * w + iw * -y + iz * -x - ix * -z,
            iz * w + iw * -z + ix * -y - iy * -x)


def _entity_values(idx: int) -> dict:
    r = result(cli('ecs', 'query', data={'entityIndex': idx, 'components': ['Transform']}))
    for c in r.get('components', []):
        if c.get('componentId') == 'Transform':
            return c['values']
    raise RuntimeError(f'no Transform on {idx}')


def world_pos(name: str) -> dict:
    """World position (≈ XR-origin space here) of any named server object.

    The runtime hierarchy listing truncates big child lists, so walk the ECS
    Transform parents up to an object whose world transform is known.
    """
    if name in _UUIDS or not _UUIDS:
        if not _UUIDS:
            load_uuids()
        if name in _UUIDS:
            t = transform(name)
            return vec(t.get('positionRelativeToXROrigin') or t['globalPosition'])
    found = result(cli('ecs', 'find', data={'namePattern': f'^{name}$', 'limit': 3}))
    idx = found['entities'][0]['entityIndex']
    pos = (0.0, 0.0, 0.0)
    rot = (0.0, 0.0, 0.0, 1.0)
    while True:
        v = _entity_values(idx)
        lp = tuple(v['position'])
        lq = tuple(v['orientation'])
        # world = parent ∘ local
        pos = tuple(a + b for a, b in zip(_qrot(lq, pos), lp))
        rot = _qmul(lq, rot)
        parent = v.get('parent') or {}
        pname = parent.get('name')
        if pname in _UUIDS:
            t = transform(pname)
            pp = t.get('positionRelativeToXROrigin') or t['globalPosition']
            pq = tuple(t['globalQuaternion'])
            w = tuple(a + b for a, b in zip(_qrot(pq, pos), pp))
            return vec(list(w))
        idx = parent['entityIndex']


# ------------------------------------------------------------------ ECS


def entity_index(name: str, component: str) -> int:
    found = result(cli('ecs', 'find', data={
        'withComponents': [component], 'namePattern': f'^{name}$', 'limit': 5,
    }))
    ents = found.get('entities', found)
    if not ents:
        raise RuntimeError(f'no entity {name} with {component}')
    return ents[0]['entityIndex']


def component(name: str, comp: str) -> dict:
    idx = entity_index(name, comp)
    q = result(cli('ecs', 'query', data={'entityIndex': idx, 'components': [comp]}))
    for c in q.get('components', []):
        if c.get('componentId') == comp:
            return c['values']
    raise RuntimeError(f'{name} has no {comp}')


def part_state(name: str) -> str:
    return component(name, 'ServicePart').get('state')


def operated(name: str) -> bool:
    return bool(component(name, 'ServiceControl').get('operated'))
