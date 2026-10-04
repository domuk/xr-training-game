// Owner-only: copies a fresh model export from ../assets/glb (private
// workspace) into public/gltf/server/. Skips quietly when that folder isn't
// there (e.g. a fresh clone) — the committed model in public/ is used as is.
import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const appRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const source = resolve(appRoot, '../assets/glb');
const target = resolve(appRoot, 'public/gltf/server');

if (!existsSync(resolve(source, 'server.glb'))) {
  console.log('No ../assets/glb export found; using the model in public/gltf/server.');
  process.exit(0);
}
mkdirSync(target, { recursive: true });
for (const file of ['server.glb', 'server_manifest.json']) {
  cpSync(resolve(source, file), resolve(target, file));
}
const tools = resolve(appRoot, 'public/gltf/tools');
mkdirSync(tools, { recursive: true });
for (const file of ['screwdriver.glb', 'screwdriver_manifest.json']) {
  if (existsSync(resolve(source, file))) cpSync(resolve(source, file), resolve(tools, file));
}
const lab = resolve(appRoot, 'public/gltf/lab');
mkdirSync(lab, { recursive: true });
for (const file of ['lab.glb', 'lab_manifest.json']) {
  if (existsSync(resolve(source, file))) cpSync(resolve(source, file), resolve(lab, file));
}
const hall = resolve(appRoot, 'public/gltf/datahall');
mkdirSync(hall, { recursive: true });
for (const file of ['datahall.glb', 'datahall_manifest.json']) {
  if (existsSync(resolve(source, file))) cpSync(resolve(source, file), resolve(hall, file));
}
console.log(`Synced server, tool, lab and data hall assets -> public/gltf/`);
