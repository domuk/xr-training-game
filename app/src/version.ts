// App name + version (from package.json), shown on the welcome card, the
// tablet and the browser tab so testers can see which build they're on.
// Dev server: "dev" + the version being worked on.
import pkg from '../package.json';

// The version being worked on (released when the batch is complete).
const NEXT_VERSION = '1.1.2';

export const APP_TITLE = import.meta.env.DEV
  ? `Server Explorer dev ${NEXT_VERSION}`
  : `Server Explorer v${pkg.version}`;
