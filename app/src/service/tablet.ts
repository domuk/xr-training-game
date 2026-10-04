// The lab tablet: a simple device body + side grips built around the
// `tablet` UIKitML screen, plus the heads-up (HUD) box that follows the view.
// Pages: safety (until Start lab) → Lab / Server / Debug tabs.
import {
  BoxGeometry,
  Mesh,
  MeshStandardMaterial,
  Quaternion,
  Vector3,
  type Object3D,
  type UIKitMLAsset,
  type World,
} from '@iwsdk/core';
import { APP_TITLE } from '../version.js';
import { strongHover } from './hover.js';

export type TabletPage = 'safety' | 'lab' | 'server' | 'explode' | 'controls' | 'debug';

const PAGES: TabletPage[] = ['safety', 'lab', 'server', 'explode', 'controls', 'debug'];

/** Screen size in UIKit units (tablet.uikitml); 1 unit = 0.01 local metres. */
const SCREEN_W = 6.0;
const SCREEN_H = 3.4;

/** HUD placement relative to the head (metres): up-left, in front. */
const HUD_OFFSET = new Vector3(-0.17, 0.11, -0.5);
const HUD_FOLLOW = 10; // 1/s — how quickly the HUD catches up with the head

export class LabTablet {
  screen?: UIKitMLAsset;
  hud?: Object3D & UIKitMLAsset;
  /** The two side grips (laser grab targets). */
  grips: Object3D[] = [];
  /** Device body behind the screen (near grab anywhere on the tablet). */
  body?: Object3D;
  hudOn = false;
  private page: TabletPage = 'safety';
  private unlocked = false;
  private hudScale = 0.05;
  private tmpPos = new Vector3();
  private tmpQuat = new Quaternion();

  constructor(private world: World) {}

  /** Find the screen + HUD scene objects and build the device body. */
  tryInit(): boolean {
    const screen = this.world.getSceneObject<UIKitMLAsset>('tablet');
    const hud = this.world.getSceneObject<UIKitMLAsset>('hud');
    if (screen == null || hud == null) return false;
    this.screen = screen;
    this.hud = hud as Object3D & UIKitMLAsset;
    // Hidden UIKit text doesn't lay out, so "off" = shrunk to nothing, not
    // invisible (the text stays measured and ready).
    this.hudScale = this.hud.scale.x;
    this.hud.scale.setScalar(1e-5);
    // HUD must never catch the laser.
    (this.hud as Object3D & { pointerEvents?: string }).pointerEvents = 'none';
    this.buildBody(screen);
    screen.getElementById('app-title')?.setProperties({ text: APP_TITLE });
    strongHover(screen);
    this.on('tab-lab', () => this.show('lab'));
    this.on('tab-server', () => this.show('server'));
    this.on('tab-explode', () => this.show('explode'));
    this.on('tab-controls', () => this.show('controls'));
    this.on('tab-debug', () => this.show('debug'));
    this.show('safety');
    return true;
  }

  /** Dark body behind the screen + two lighter grips on the short sides. */
  private buildBody(screen: Object3D): void {
    const body = new Mesh(
      new BoxGeometry(SCREEN_W + 0.3, SCREEN_H + 0.3, 0.15),
      new MeshStandardMaterial({ color: 0x2b2e33, roughness: 0.6, metalness: 0.1 }),
    );
    body.position.set(0, 0, -0.09);
    body.name = 'tablet_body';
    screen.add(body);
    this.body = body;
    const gripMaterial = new MeshStandardMaterial({ color: 0x575d66, roughness: 0.8 });
    for (const side of [-1, 1]) {
      const grip = new Mesh(new BoxGeometry(0.45, SCREEN_H * 0.8, 0.32), gripMaterial);
      grip.position.set(side * (SCREEN_W / 2 + 0.38), 0, -0.09);
      grip.name = side < 0 ? 'tablet_grip_left' : 'tablet_grip_right';
      screen.add(grip);
      this.grips.push(grip);
    }
  }

  on(id: string, fn: () => void): void {
    this.screen?.getElementById(id)?.addEventListener('click', fn);
  }

  show(page: TabletPage): void {
    if (page !== 'safety' && !this.unlocked) return;
    this.page = page;
    for (const p of PAGES) {
      this.screen
        ?.getElementById(`page-${p}`)
        ?.setProperties({ display: p === page ? 'flex' : 'none' });
      if (p !== 'safety') {
        // Active tab in the accent (blue) style.
        this.screen
          ?.getElementById(`tab-${p}`)
          ?.setProperties({ variant: p === page ? 'primary' : 'secondary' } as never);
      }
    }
  }

  get current(): TabletPage {
    return this.page;
  }

  /** Start lab: show the tabs and go to the Lab page. */
  unlock(): void {
    this.unlocked = true;
    this.screen?.getElementById('tabs')?.setProperties({ display: 'flex' });
    this.setText('btn-start-lab-label', 'Back to lab');
    this.show('lab');
  }

  setText(id: string, text: string): void {
    this.screen?.getElementById(id)?.setProperties({ text });
  }

  /** Lab page + HUD instructions. */
  say(title: string, body: string, status: string): void {
    this.setText('info-title', title);
    this.setText('info-body', body);
    this.setText('info-status', status);
    this.hud?.getElementById('hud-title')?.setProperties({ text: title });
    this.hud?.getElementById('hud-body')?.setProperties({ text: body });
    this.hud?.getElementById('hud-status')?.setProperties({ text: status });
  }

  toggleHud(): void {
    this.hudOn = !this.hudOn;
    if (this.hud != null) this.hud.scale.setScalar(this.hudOn ? this.hudScale : 1e-5);
    this.setText('btn-hud-label', this.hudOn ? 'Heads-up: on' : 'Heads-up: off');
    this.snapHud = true;
  }

  private snapHud = true;

  /** Keep the HUD at the top-left of the view, smoothed. */
  updateHud(head: Object3D, delta: number): void {
    const hud = this.hud;
    if (hud == null || !this.hudOn) return;
    head.updateWorldMatrix(true, false);
    const headQuat = head.getWorldQuaternion(this.tmpQuat);
    const target = this.tmpPos
      .copy(HUD_OFFSET)
      .applyQuaternion(headQuat)
      .add(new Vector3().setFromMatrixPosition(head.matrixWorld));
    const parent = hud.parent;
    const localQuat = headQuat.clone();
    if (parent != null) {
      parent.updateWorldMatrix(true, false);
      parent.worldToLocal(target);
      localQuat.premultiply(parent.getWorldQuaternion(new Quaternion()).invert());
    }
    if (this.snapHud) {
      hud.position.copy(target);
      hud.quaternion.copy(localQuat);
      this.snapHud = false;
      return;
    }
    const k = 1 - Math.exp(-delta * HUD_FOLLOW);
    hud.position.lerp(target, k);
    hud.quaternion.slerp(localQuat, k);
  }
}
