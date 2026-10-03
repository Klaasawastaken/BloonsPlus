(() => {
  const panel = document.getElementById('vm-viewer');
  if (!panel) return;
  const image = document.getElementById('vm-viewer-image');
  const status = document.getElementById('vm-viewer-status');
  const empty = document.getElementById('vm-viewer-empty');
  let controller = null, timer = null, frameUrl = null;
  const visible = () => panel.open && !document.hidden && panel.getClientRects().length > 0;
  async function refresh() {
    clearTimeout(timer);
    if (!visible() || controller) return;
    controller = new AbortController();
    const timeout = setTimeout(() => controller?.abort(), 15000);
    try {
      const response = await fetch('/api/live-screen', { cache: 'no-store', signal: controller.signal });
      if (!response.ok) { const error = await response.json(); throw new Error(error.error || 'VM screen unavailable'); }
      const next = URL.createObjectURL(await response.blob());
      if (frameUrl) URL.revokeObjectURL(frameUrl);
      frameUrl = next; image.src = next; image.hidden = false; empty.hidden = true;
      status.textContent = `VM screen · updated ${new Date().toLocaleTimeString()}`;
    } catch (error) {
      if (visible()) status.textContent = error.name === 'AbortError' ? 'VM screen timed out; reconnecting…' : error.message;
      image.hidden = true; empty.hidden = false; empty.textContent = 'Screen unavailable. Open BTD6 in the VM.';
    } finally {
      clearTimeout(timeout); controller = null;
      if (visible()) timer = setTimeout(refresh, 2000);
    }
  }
  function sync() {
    if (!visible()) { clearTimeout(timer); controller?.abort(); }
    else refresh();
  }
  panel.addEventListener('toggle', sync);
  document.addEventListener('visibilitychange', sync);
  new MutationObserver(sync).observe(panel.closest('section'), { attributes: true, attributeFilter: ['class', 'hidden', 'style'] });
  document.getElementById('vm-viewer-fullscreen').addEventListener('click', () => document.getElementById('vm-viewer-stage').requestFullscreen().catch(() => {}));
  addEventListener('pagehide', () => { clearTimeout(timer); controller?.abort(); if (frameUrl) URL.revokeObjectURL(frameUrl); });
})();
