# Server Explorer: Data Center Server Maintenance in AR

[![Code licence: MIT](https://img.shields.io/badge/code%20licence-MIT-blue.svg)](LICENSE)
[![Assets licence: CC BY 4.0](https://img.shields.io/badge/assets%20licence-CC%20BY%204.0-lightgrey.svg)](model/LICENSE.md)
[![Status: v0.1 in development](https://img.shields.io/badge/status-v0.1%20in%20development-orange.svg)](#project-status)
[![Meta Quest 3](https://img.shields.io/badge/device-Meta%20Quest%203-1c1e20.svg?logo=meta)](https://www.meta.com/quest/quest-3/)
[![WebXR](https://img.shields.io/badge/WebXR-immersive--ar-6f42c1.svg)](https://immersiveweb.dev/)
[![Immersive Web SDK](https://img.shields.io/badge/Meta%20IWSDK-1.0.1-0866ff.svg)](https://github.com/facebook/immersive-web-sdk)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178c6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js 24](https://img.shields.io/badge/Node.js-24-339933.svg?logo=node.js&logoColor=white)](https://nodejs.org/)
[![Blender](https://img.shields.io/badge/model-Blender-e87d0d.svg?logo=blender&logoColor=white)](model/)

A mixed-reality training app for **data center technicians** on the **Meta Quest 3**. Trainees see a real-size 2U rack server on a real table in passthrough AR. They take it apart and put it back together, following the same steps and rules as real hardware: release tabs, open ejectors, undo screws in the right order, then pull each part out along its real removal path.

The app runs in the **Quest browser** (WebXR). Nothing needs installing on the headset. It is built with **Meta's Immersive Web SDK (IWSDK)** on three.js.

> **Status: v0.1 proof of concept, in active development.** Core interactions work and are tested in the IWSDK emulator. They have not yet been tested on a physical headset. See [Project status](#project-status) and [Known issues](#known-issues).

---

## Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
- [Using the app](#using-the-app)
- [Testing](#testing)
- [The server model](#the-server-model)
- [Project status](#project-status)
- [Known issues](#known-issues)
- [Roadmap](#roadmap)
- [Credits and licences](#credits-and-licences)

---

## Features

**Training (v0.1)**
- **Safety brief first.** A Star Wars-style scrolling crawl of safety rules plays before training starts: ESD strap, power down, unplug, hot parts, sharp edges, lifting.
- **Real-size 2U server.** It is placed at chest height, within reach, when the session starts.
- **Realistic removal steps**, driven entirely by the model's own data:
  - **Lid:** press both release tabs (the screw is optional), then slide it back 15 mm and lift.
  - **Drive caddies (×24):** press the button, swing the handle out, pull. Each drive comes out of its caddy after 4 screws.
  - **Fans (×3):** hot-swap. Press the release tab and lift.
  - **DIMMs (×8):** open both ejectors and lift. The ejectors click shut on refit.
  - **Heatsinks (×2):** captive screws loosen in order **4-3-2-1** and tighten in order **1-2-3-4**. The wrong order is refused with a warning.
  - **CPUs (×2):** heatsink off, lever out from its hook, load plate open, then lift by the edges.
  - **Network card and accelerator card:** bracket screw, then lift straight up.
- **Rules enforced.** A part can only come out once its prerequisites are done, and the lid must be off for anything inside. If you try too early, the info panel tells you why.
- **Constrained pulling.** A fitted part only moves along its real removal path until it is clear, then moves freely.
- **Refit.** Release a part near its slot and it slides home along the same path. The panel then lists anything still to close or tighten.
- **Info panel.** It shows the part name, a tip, safety warnings, checks and the next step for whatever you are pointing at or holding.

**Input**
- **Controllers:** laser plus trigger to click tabs, buttons and screws. Point and hold the trigger to pull a part.
- **Hands:** pinch acts as the trigger, including pinch-to-grab.
- **Movement:** the left thumbstick walks, and the right thumbstick teleports and snap-turns. It can be switched off.

**Debug panel** (for testing)
- Lid off (removes it completely until Reset)
- Remove one of each part
- Open or close all controls
- Exploded view, where every part counts as removed and can be grabbed
- Show slot markers
- Movement on/off
- Reset
- Move the server: bring here, rotate 90°, up, down, closer, further

---

## How it works

```
app/public/gltf/server/server.glb   ← one real-size 2U model, made in Blender (source: model/)
   └─ glTF "extras" on each node: role, pull path, requires, motion, axis,
      limits, screw order, tip ids …  (also exported as server_manifest.json)
                │
                ▼
app/src/service/rules.ts       ← pure rules: what can be operated/removed/refitted
app/src/service/service-system.ts ← IWSDK system: reads the extras, makes every
                                  part/control interactive, enforces the rules,
                                  constrains pulls to the removal path, snaps refits
app/src/service/text.ts        ← the words shown on the info panel
```

The model is the **design authority**. Counts, layout and removal steps come from it, not from code. Adding or changing a part in Blender (with its extras) changes the training without touching the app's logic.

**Key design notes**
- **Parts:** every v0.1 part has a permanent IWSDK `DistanceGrabbable` (a laser grab). The rules are checked when a grab starts, and a refused grab is dropped straight away with a reason. Grab components are never added or removed at runtime, because IWSDK 1.0.1 keeps a grab handle alive after its component is removed.
- **Controls:** tabs, ejectors, levers and screws are `RayInteractable` and `PokeInteractable`, and they stop their click from reaching the parent part's grab.
- **Axes:** metadata vectors are stored in Blender axes and converted at load: `(x, y, z) → (x, z, -y)`.
- **Testable state:** each part's state (`fitted` / `seated` / `free` / `gone`) and each control's state (`operated`) is mirrored into ECS components, so tests can read them.

---

## Repository layout

```
.
├── app/                         The IWSDK WebXR app
│   ├── src/
│   │   ├── index.ts             World.create + system registration
│   │   ├── assets.ts            Asset manifest (server GLB + UI panels)
│   │   ├── components.ts        ECS component registry
│   │   ├── panel.ts             Browser welcome card (Enter AR)
│   │   └── service/             Training logic
│   │       ├── rules.ts         Pure rules engine (unit-tested)
│   │       ├── service-system.ts Interaction, grabs, placing, refit, debug panel
│   │       ├── components.ts    ServicePart / ServiceControl components
│   │       └── text.ts          Info-panel text
│   ├── public/
│   │   ├── gltf/server/         server.glb + server_manifest.json (CC BY 4.0)
│   │   ├── scenes/              Scene composition (main.iwsdk.scene.json)
│   │   └── ui/                  UIKitML panels: info, debug, safety, welcome
│   ├── tests/
│   │   ├── rules.test.ts        Rule tests against the real model data
│   │   └── qa/                  Emulator QA harness (laser clicks, trigger/grip/pinch pulls)
│   ├── iwsdk.config.json        Project authority: XR mode, features, emulator
│   └── package.json
└── model/                       Blender source for the server (CC BY 4.0)
    ├── server.blend
    ├── layout.json
    └── scripts/                 One build script per part; 30_export.py writes the GLB
```

---

## Getting started

### Prerequisites
- **Node.js 24** (the version pinned in `app/.nvmrc`). Node 20.19+ or 22.12+ also work.
- **Windows, macOS or Linux** to develop.
- **Meta Quest 3**, on the same Wi-Fi as the PC. Optional: everything can be tested in the built-in emulator.

### Install and run

```bash
git clone https://github.com/domuk/xr-training-game.git
cd xr-training-game/app
npm install
npm run dev
```

`npm run dev` copies the server model into `public/`, starts the IWSDK dev server over **HTTPS on port 8081**, and opens a browser window with the **IWER emulator** (an emulated Quest 3).

### On the headset
1. Run `npx iwsdk dev status` and pick a URL from `runtimeUrls.network`, e.g. `https://192.168.x.x:8081/`.
2. Open it in the **Quest browser** and accept the self-signed certificate warning. This is only needed once.
3. Press **Enter AR**.

Other setup notes:
- Run **Space Setup** on the Quest first, so it knows the room.
- If the headset can't reach the PC, allow Node.js through the Windows Firewall for Private networks.
- If the Wi-Fi isolates devices, use a USB cable with `adb reverse tcp:8081 tcp:8081`. This needs Developer Mode.

### Other scripts

| Command | What it does |
|---|---|
| `npm run dev` | Sync assets and start the dev server with the emulator |
| `npm run dev:down` | Stop the dev server |
| `npm run typecheck` | TypeScript check |
| `npm test` | Rule tests (Node's built-in test runner) |
| `npm run build` | Production build to `app/dist/` |

---

## Using the app

1. **Enter AR.** The server appears in front of you at chest height. The info panel is front-right and the debug panel is on your left.
2. Read the **safety crawl**, then press **Start training** on the info panel.
3. **Click** tabs, buttons, ejectors, levers and screws with the laser (trigger or pinch).
4. **Pull** a part by pointing at it and holding the trigger, then moving the controller. A part that isn't ready won't move, and the panel says why.
5. **Refit** by bringing the part back near its slot and letting go.

The full flow is: safety crawl → **Start** → place the server (drag it with the laser, or grip or pinch it up close) → **Next** → training.
- **With hands:** pinch acts as the trigger. Pinch near a part to pull it, and press tabs and buttons with a fingertip.
- **Drive caddies:** press the button, open the handle, then hold on the handle arm and pull.

### Emulator controls (IWER)

| Action | Control |
|---|---|
| Enter play mode (mouse look) | Toolbar play button; **Esc** exits |
| Walk | Left thumbstick: **W/A/S/D** |
| Teleport / turn | Right thumbstick: **arrow keys** |
| Move the headset directly | **Shift + W/A/S/D**, **Shift + ↑/↓** for height |
| Trigger / grip (right controller, play mode) | Left mouse / right mouse |
| Switch controllers ↔ hands | Toolbar input-mode button |

There is a full guide at [iwsdk.dev, Testing Your Experience](https://iwsdk.dev/guides/02-testing-experience.html).

---

## Testing

### Rule tests
```bash
cd app && npm test
```
These run the rules engine against the **real** `server_manifest.json`. They cover the lid tabs, the optional lid screw, caddy and drive order, the heatsink screw sequence, CPU lever and plate ordering, DIMM ejectors, refit auto-close, and a sweep proving every v0.1 part can be removed by following the rules.

### Emulator QA (end-to-end)
`app/tests/qa/` drives the emulated Quest 3 the way a user would, through the IWSDK CLI. It moves the controller in front of a target, aims the laser, clicks or holds the trigger, and moves the controller. It then checks the resulting app state and object positions.

```bash
cd app
npx iwsdk dev up --headless           # emulator without a window
python tests/qa/run_qa.py              # all tests
python tests/qa/run_qa.py lid fan      # selected tests
```

Tests: `placement`, `start`, `lid`, `caddy`, `fan`, `debuglid`, `moved`, `exploded`. Python 3.10+ is required.

---

## The server model

- **Generic 2U** (not tied to a vendor). The body is 43.8 × 64.0 × 8.92 cm, or 47.4 cm wide with the rack ears.
- **About 56k triangles and 39 materials.** It is built for the Quest browser, with an atlas pass planned.
- **80 removable assets, 90 moving parts, 126 fasteners and 50 slots.** Each carries metadata in glTF `extras`.
- **Made in Blender.** Open `model/server.blend`, then run the scripts in `model/scripts/` from Blender's text editor. `30_export.py` writes `app/public/gltf/server/server.glb` and `server_manifest.json`.

### Model metadata (glTF `extras`)
The app reads everything from the model. The same data is in `server_manifest.json`.

| Key | On | Meaning |
|---|---|---|
| `role` | all | `asset` (removable part) · `moving` · `fastener` · `indicator` · `fixed` |
| `pull` | asset | Removal path: list of steps `[dx, dy, dz]` in metres (Blender axes) |
| `requires` | asset, moving | What must be done first: fasteners/latches operated, or other assets removed |
| `motion`, `axis`, `limits` | moving, fastener | `hinge` (degrees) · `press` / `slide` (metres) · `screw`, along/around `X`/`Y`/`Z` |
| `seq`, `captive`, `rise` | fastener | Screw order number, stays attached, lift while undoing |
| `order_out`, `order_in` | asset | Screw sequence, e.g. heatsinks `4,3,2,1` / `1,2,3,4` |
| `tip`, `check`, `warn` | various | Info-panel text ids and hints |

- **Axes:** Blender is Z-up. Convert to glTF/three.js with `(x, y, z) → (x, z, -y)`. The server's front faces **+Z**.
- **Grab:** grab `asset_*` nodes. `slot_*` empties mark where each part sits when fitted.

---

## Project status

| Area | State |
|---|---|
| Framework, project setup, asset pipeline | ✅ Done |
| Rules engine (requires, lid-off, screw order, refit) | ✅ Done, unit-tested |
| Laser click + laser pull along removal paths + refit | ✅ Works on Quest 3 and in the emulator |
| Start flow: safety → place server → Next → training | ✅ Built, emulator-tested |
| Hands: pinch near-grab, finger press (hands only), grip near-grab | ✅ Built; pinch tested in emulator, headset check pending |
| Drive caddy pulled by its open handle | ✅ Fixed, emulator-tested |
| Debug panel, movement, smoothing | ✅ Built |
| Floating "tablet" window for the panels | ⏳ Next |
| Full guided step-by-step workflow | ⏳ Planned |
| Real table detection (hit-test / planes) | ⏳ Planned |

---

## Known issues

- **Grip near-grab between neighbouring parts** (e.g. fans side by side) may pick the neighbour. It was improved, but needs a headset check.
- **Grabbing from the exploded view** is flaky in the emulator tests and needs a headset check.
- **Panel layout** is functional but basic. A movable tablet-style window will replace it.
- **Model polish:** 39 materials, with a texture/atlas pass planned.

---

## Roadmap

- **v0.1:** floating tablet window; guided workflow; headset checks of hands and near-grab.
- **v0.2:** PSUs and power cords; a front-panel power-down as a real safety step; the remaining parts (shroud, backplane, board, battery, SATA).
- **Later:** rack, server lift and trolleys; a VR data hall; scoring and assessment.
- **AR rack overlay:** labels per U and cable lines over 5 physical training racks. Each rack is calibrated once and saved as an anchor, with the data in JSON.

---

## Credits and licences

**This project is open source:**
- **Code and docs:** [MIT](LICENSE). Use, modify and redistribute freely, as long as you keep the copyright notice.
- **3D model and Blender files** (`model/`, `app/public/gltf/server/`): [CC BY 4.0](model/LICENSE.md). Free to use and adapt, including commercially, with credit.

**Third-party:**
- **[Meta Immersive Web SDK](https://github.com/facebook/immersive-web-sdk)**: MIT licence. The app scaffold and agent tooling come from `@iwsdk/create`.
- **[three.js](https://threejs.org/)** (via IWSDK), **[pmndrs/uikit](https://github.com/pmndrs/uikit)**: MIT licence.
- **Reference images** used to design the model are third-party, **not included**, and not redistributed.
- The scaffold includes Meta's `@meta-quest/metavr` CLI as a dev dependency. It collects usage data under the Meta Platform Technologies SDK licence. Remove it with `npm uninstall @meta-quest/metavr` if you don't want that.
