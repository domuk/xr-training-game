// Info-panel words for the model's `tip` ids (draft wording,
// the user will correct). `check` / `warn` text comes from the model itself.

export const TIPS: Record<string, string> = {
  lid: 'Press both release tabs, slide the lid back, then lift. To refit: studs into the slots, slide forward until the tabs click.',
  lid_tab: 'Press to release the lid.',
  drive_caddy:
    'Press the button, swing the handle out, pull the caddy straight out. Refit: push in fully, close the handle until it clicks.',
  caddy_button: 'Press to release the handle.',
  caddy_handle: 'Swing out to unlock; close to lock the caddy in.',
  drive_in_caddy: 'Undo the 4 screws, then slide the drive out of the caddy.',
  fan: 'Hot-swap fan. Lift it straight up.',
  fan_release_tab: 'Press to free the fan.',
  dimm: 'Click an ejector to unlock, then lift the DIMM straight up.',
  dimm_ejector: 'Push outwards to release the DIMM.',
  heatsink:
    'Loosen the captive screws in order 4-3-2-1, a few turns each. Lift gently. Refit 1-2-3-4.',
  socket_lever: 'Push the lever down and out from its hook, then lift.',
  load_plate: 'Swings open once the lever is up.',
  cpu: 'Lift by the edges. Never touch the pins or socket contacts.',
  nic: 'Undo the bracket screw, lift the card straight up.',
  accel_card: 'Accelerator card. Undo the bracket screw, lift straight up.',
};

export const SCREW_TIP =
  'Screws need the screwdriver: your left hand. Put the tip on the screw. Controller: X undo, Y do up. Hands: touch the screw with the tip.';

export const START_TEXT =
  'Read the safety brief on the tablet, then press Start lab.';

export const TOOL_TEXT = {
  controller: (lower: string, upper: string) =>
    `Put the tip on a screw. ${lower} = unscrew, ${upper} = screw in.`,
  hand: 'Touch the tip to a screw to undo it (or do it up if it is undone).',
};

export const MOVE_TEXT =
  'Point at the server and hold the trigger to drag it, or grip / pinch it up close. Press Done moving when it is on the table.';

export const READY_TEXT =
  'The server is in rack 3. Grab its side (or hold the trigger on its case) and slide it out along the rails, then carry it to the table. Click or press tabs and buttons; pull parts by holding the trigger or a pinch; screws need your left hand (pinch it to swap hand / screwdriver). Click the lab door to go to the data hall.';

