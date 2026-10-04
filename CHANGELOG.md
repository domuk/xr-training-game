# Changelog

## v1.2.0 (2026-10-04)

- New: the data hall. Click the lab's double door to walk into it; click either hall door to go back to the lab
- Only one room is loaded at a time, to save memory and loading
- Updated lab model (rack fixes, door closer arm moves with the door)
- Blender build scripts for the lab and the data hall added to model/scripts

## v1.1.2 (2026-10-04)

- Server comes out of the rack: grab its side (or hold the trigger on its case) and it slides out along the rails; line it up in front of a slot and it slides back in
- One hand carries the server (two-handed lifting is off for now); the tablet's Move server button is gone
- No gravity for now: things float where you let go, and held things stop at furniture, the server and each other
- Blanking panels removed for now
- Cabinet drawers only open with both cabinet doors open
- The drawer screwdriver can be grabbed and moved, including pushing it away / pulling it closer with the right stick
- Left hand: pinch (or grip) on nothing to swap between hand and screwdriver
- Menu with hands: show the back of your open right hand for 3 s (the pinch clashed with the Quest menu)
- Lasers reach as far as they point; the laser dot shows on the tablet and buttons light up clearly when pointed at
- The tablet's Server buttons work when the server is racked
- Website card shows the version as the release badge only

## v1.1.1 (2026-10-04)

- Fixes the 1.1.0 release, which went out with an out-of-date README, website card and in-app help
- Reset view now only brings you back to the table; the server stays where you left it
- The tablet's Bring all here button is now Reset view, matching the menu
- In-app help updated: welcome card, tablet Controls page and tips cover the lab, racks, two-hand carry, doors and drawers, and the Room / AR / Black menu
- README rewritten for the lab version, with a live release badge
- Website card updated, with a release badge

## v1.1.0 (2026-10-04)

- Training lab room is the default setting: start at the island table; server starts racked in rack 3
- Quick menu (double-press A, or pinch and hold the right hand 2 s): Room / AR / Black and Reset view
- Left hand is the screwdriver (X unscrew, Y screw in; hands: touch a screw with the tip)
- Racks: blanking panels pull out; carry the server with both hands (turns left / right only) and rack it
- Room doors, rack doors, tool cabinet doors and 7 drawers open and close; prop screwdriver in drawer 1
- Room is solid to walk in; loose parts fall onto surfaces
- CPU socket: open lever and plate let you take the CPU; plate stays open until the CPU is out and back
- Tablet is held by its side handles; steadier hand tracking for held parts and the tablet
- Version shown on the welcome card, tablet and browser tab; jump turned off; smaller laser dot

## v1.0.1 (2026-10-03)

- Renamed to Server Explorer
- Motherboard removal (10 screws; cards, shroud, DIMMs and CPUs come out first)
- CPU socket order enforced: heatsink, lever, plate (and reverse to refit)
- Screws only turn with the screwdriver (2 s between turns)
- Caddy button opens the handle; drives come free of the caddy
- Tablet: grab anywhere up close, fingertip buttons with hands
- Double-click a thumbstick (or Lab > Bring all here) to bring everything back
- Cables hidden for now
- Screwdriver Blender source added to model/

