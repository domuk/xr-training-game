// System-free component declarations (listed in src/components.ts).
import { createComponent, Types } from '@iwsdk/core';

/** A removable part of the server (`asset_*` node). */
export const ServicePart = createComponent('ServicePart', {
  name: { type: Types.String, default: '' },
  /** fitted · seated (being pulled out) · free · gone (debug-removed). */
  state: { type: Types.String, default: 'fitted' },
});

/** A tab, button, lever, ejector or screw on the server. */
export const ServiceControl = createComponent('ServiceControl', {
  name: { type: Types.String, default: '' },
  operated: { type: Types.Boolean, default: false },
});
