/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

import { AssetType, defineAssets } from '@iwsdk/core';

const publicAssetUrl = (filePath: string): string =>
  `${import.meta.env.BASE_URL}${filePath.replace(/^\/+/u, '')}`;

export default defineAssets({
  // 2U server model (source: ../model/server.blend).
  server: {
    url: publicAssetUrl('gltf/server/server.glb'),
    type: AssetType.GLTF,
    name: '2U Server',
  },
  // Training lab room (source: assets/blender/lab.blend). Default setting.
  lab: {
    url: publicAssetUrl('gltf/lab/lab.glb'),
    type: AssetType.GLTF,
    name: 'Training Lab',
  },
  screwdriver: {
    url: publicAssetUrl('gltf/tools/screwdriver.glb'),
    type: AssetType.GLTF,
    name: 'Screwdriver',
  },
  'welcome-panel': {
    url: publicAssetUrl('ui/welcome.uikitml'),
    type: AssetType.UIKitML,
    name: 'Welcome Panel',
  },
  tablet: {
    url: publicAssetUrl('ui/tablet.uikitml'),
    type: AssetType.UIKitML,
    name: 'Lab Tablet',
  },
  hud: {
    url: publicAssetUrl('ui/hud.uikitml'),
    type: AssetType.UIKitML,
    name: 'Heads-up Instructions',
  },
  menu: {
    url: publicAssetUrl('ui/menu.uikitml'),
    type: AssetType.UIKitML,
    name: 'Quick Menu',
  },
});
