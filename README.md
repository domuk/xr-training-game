# Server Explorer

[![Latest release](https://img.shields.io/github/v/release/domuk/xr-training-game?label=release)](https://github.com/domuk/xr-training-game/releases/latest)
[![Play it](https://img.shields.io/badge/play-ar.dom.cool%2Flab-5ff0ff.svg)](https://ar.dom.cool/lab/)
[![Code licence: MIT](https://img.shields.io/badge/code%20licence-MIT-blue.svg)](LICENSE)
[![Models licence: CC BY 4.0](https://img.shields.io/badge/models%20licence-CC%20BY%204.0-lightgrey.svg)](model/LICENSE.md)
[![Meta Quest 3](https://img.shields.io/badge/device-Meta%20Quest%203-1c1e20.svg?logo=meta)](https://www.meta.com/quest/quest-3/)
[![WebXR](https://img.shields.io/badge/WebXR-immersive--ar-6f42c1.svg)](https://immersiveweb.dev/)
[![Immersive Web SDK](https://img.shields.io/badge/Meta%20IWSDK-1.0.1-0866ff.svg)](https://github.com/facebook/immersive-web-sdk)

A mixed-reality training app for **data center technicians** on the **Meta Quest 3**.
You stand in a full-size training lab, take a real-size 2U server out of a rack,
carry it to the table, take it apart and put it back, following the same steps
and rules as real hardware.

It runs in the **Quest browser** (WebXR): nothing to install. Built with
**Meta's Immersive Web SDK (IWSDK)** on three.js.

**Play:** open **[ar.dom.cool/lab](https://ar.dom.cool/lab/)** in the Quest browser and press **Enter AR**.
**What's new:** see the [CHANGELOG](CHANGELOG.md) and [releases](https://github.com/domuk/xr-training-game/releases).

---

## Contents
- [Features](#features)
- [Controls](#controls)
- [Run it yourself](#run-it-yourself)
- [Repository layout](#repository-layout)
- [Testing](#testing)
- [The models](#the-models)
- [Known limits](#known-limits)
- [Credits and licences](#credits-and-licences)

---

## Features

**The lab**
- **Training lab room** (default): racks, an island table, a tool cabinet with drawers, benches, doors and a server lift.
- **Data hall:** click the lab's double door to walk into a full data hall (rack rows, hot aisles, power cabinets, cable baskets). Its doors, drawers, cabinets and PDC breakers work (breakers just flip for now). Click either hall door to go back. Only one room is loaded at a time.
- **Server lift:** push it along the floor (it can't be picked up). Press its up / down buttons with your hand: the shelf stops at each rack-server height and turns green when lined up.
- **Blanking panels:** click one to pull it out of the rack; a slot takes the server once both of its panels are out.
- **Three settings** from the quick menu: **Room**, **AR** (your real room through passthrough) or **Black** (a plain void).
- You start at the island table. The **server starts in rack 3**.
- Doors, rack doors, the tool cabinet's doors and its 7 drawers open and close (open both cabinet doors before the drawers).
- The room is solid to walk in. Held things stop at furniture, the server and each other instead of passing through. Let go and they fall onto whatever is below (in the rooms; AR and Black stay floating).

**The server**
- **Racking:** grab the server by its side (or hold the trigger on its case) and it slides out of the rack along the rails. Carry it with **one hand**; the right stick spins it left / right (it never tips). Line it up in front of a slot and it slides back in on the rails. While it is racked, only the drives can be swapped.
- **Real removal steps**, driven by the model's own data:
  - **Lid:** press both release tabs, slide it back and lift.
  - **Drive caddies (×24):** press the button (the handle flips open), pull. Each drive comes out of its caddy after its 4 screws.
  - **Fans (×3):** lift out.
  - **DIMMs (×8):** open the ejectors and lift.
  - **Heatsinks (×2):** screws undone in order **4-3-2-1**, done up in order **1-2-3-4**.
  - **CPUs (×2):** heatsink off, lever up, then load plate up. The plate stays open until the CPU has been taken out and put back.
  - **Air shroud, network card, accelerator card**, and the **motherboard** (after its 10 screws, the cards, shroud, DIMMs and CPUs).
- **Rules enforced:** a part only comes out once everything before it is done. The tablet says why if you are too early.
- **Refit:** bring a part back to its slot (it glows green when it will snap in) and let go.

**The tools**
- **Your left hand is the screwdriver.** Screws only turn with it, with a 2-second gap between turns. Double pinch (or double grip) to swap between hand and screwdriver.
- **The lab tablet:** safety brief first, then Lab, Server, Explode, Controls and Debug pages. Hold it by its side handles.
- **Quick menu:** Reset view (brings you back to the table) and Room / AR / Black.

## Controls

| Action | Controllers | Hands |
|---|---|---|
| Click tabs, buttons, doors, drawers | Point + trigger | Point + pinch, or press with a fingertip |
| Go to the data hall / back to the lab | Click the lab's double door / a hall door | Same |
| Pull a part out | Point at it + hold trigger | Pinch and hold on it |
| Grab up close (right hand) | Grip | Pinch |
| Carry the server | Grip on its side, or hold the trigger on its case | Pinch its side |
| Screwdriver (left hand) | Tip on a screw: **X** undo, **Y** do up | Touch a screw with the tip |
| Left hand / screwdriver swap | Double left grip | Double left pinch |
| Spin the held server | Right stick left / right | Right stick left / right |
| Server lift shelf up / down | Grip on its up / down button | Pinch its up / down button |
| Push a held part away / closer | Right stick up / down | — |
| Quick menu | Double-press **A** | Back of your open right hand towards your face for 3 s |
| Walk / teleport / turn | Left stick walks; right stick teleports and snap-turns | — |

## Run it yourself

**You need:** Node.js 24 (20.19+ and 22.12+ also work), and a Meta Quest 3 on the same Wi-Fi (optional: there is an emulator).

```bash
git clone https://github.com/domuk/xr-training-game.git
cd xr-training-game/app
npm install
npm run dev
```

`npm run dev` starts the IWSDK dev server over **HTTPS on port 8081** and opens a browser with the **IWER emulator** (an emulated Quest 3).

**On the headset:**
1. Run `npx iwsdk dev status` and pick a URL from `runtimeUrls.network`, e.g. `https://192.168.x.x:8081/`.
2. Open it in the Quest browser and accept the certificate warning (once).
3. Press **Enter AR**.

If the headset can't reach the PC, allow Node.js through the firewall for private networks, or use USB with `adb reverse tcp:8081 tcp:8081`.

| Command (in `app/`) | What it does |
|---|---|
| `npm run dev` | Dev server + emulator |
| `npm run dev:down` | Stop the dev server |
| `npm run typecheck` | TypeScript check |
| `npm test` | Rule tests |
| `npm run build` | Production build to `app/dist/` |

## Repository layout

| Path | What |
|---|---|
| `app/` | The IWSDK app (TypeScript, Vite). Logic in `app/src/service/` |
| `app/src/service/rules.ts` | The removal rules (pure logic, unit tested) |
| `app/src/service/service-system.ts` | Interaction: grabs, paths, slots, tools, room, menu |
| `app/src/service/lab.ts` | The lab room: doors, drawers, rack slots |
| `app/public/gltf/` | Models: server, screwdriver, lab, data hall |
| `app/public/ui/` | Panels: tablet, welcome card, heads-up, menu |
| `model/` | Blender source files and build scripts |
| `CHANGELOG.md` | What changed in each release |

## Testing

```bash
cd app
npm run typecheck
npm test
```

The rule tests check removal order, the CPU socket order, the motherboard and screw rules against the real model data.

## The models

The server, screwdriver and lab are built in Blender to real size, and the app is
driven by data on each object (`extras` in the glTF):

| Field | Meaning |
|---|---|
| `role` | `asset` (removable part), `moving` (tab, lever, door, drawer), `fastener` (screw), `slot` (snap target) |
| `pull` | The real removal path, step by step |
| `requires` | What must be done or removed first |
| `motion`, `axis`, `limits` | How a moving part moves |
| `order_out`, `order_in` | Screw order (heatsinks) |

Changing the model in Blender (with its extras) changes the training without changing the app's logic.

## Known limits
- Cables and power cords are hidden for now.
- Two-handed lifting is off for now.
- The lift's small up / down buttons are hard to hit with the laser; use your hand or controller on them.
- The server lift is in the room but can't be used yet.

## Credits and licences
- **Code and docs:** [MIT](LICENSE).
- **3D models and Blender files** (`model/`, `app/public/gltf/`): [CC BY 4.0](model/LICENSE.md). Free to use and adapt, with credit.
- **Third-party:** [Meta Immersive Web SDK](https://github.com/facebook/immersive-web-sdk), [three.js](https://threejs.org/) and [pmndrs/uikit](https://github.com/pmndrs/uikit), all MIT. Reference photos used to design the models are not included.
- The scaffold includes Meta's `@meta-quest/metavr` CLI as a dev dependency, which collects usage data under Meta's SDK licence. Remove it with `npm uninstall @meta-quest/metavr` if you don't want that.
