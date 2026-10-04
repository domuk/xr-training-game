// Panel buttons tagged class="hb" get a clearly different colour while the
// laser / finger is on them (the kit's own hover was one shade of grey).
export function strongHover(panel: unknown): void {
  const doc = panel as {
    getElementsByClassName?: (c: string) => { setProperties: (p: object) => void }[];
  };
  for (const el of doc.getElementsByClassName?.('hb') ?? []) {
    el.setProperties({ hover: { backgroundColor: '#22d3ee', color: '#0b1220' } });
  }
}
