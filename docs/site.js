(() => {
  const root = document.documentElement;
  const themeButton = document.getElementById('theme-toggle');
  let theme;
  try { theme = localStorage.getItem('bloons-guide-theme'); } catch {}
  if (!['light', 'dark'].includes(theme)) theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  function setTheme(value) {
    root.dataset.theme = value;
    themeButton.setAttribute('aria-label', `Switch to ${value === 'dark' ? 'light' : 'dark'} theme`);
    document.querySelector('meta[name="theme-color"]').content = value === 'dark' ? '#14231f' : '#f5f6f1';
  }
  setTheme(theme);
  themeButton.addEventListener('click', () => {
    theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(theme);
    try { localStorage.setItem('bloons-guide-theme', theme); } catch {}
  });
  const tabs = [...document.querySelectorAll('[role="tab"]')];
  function selectTab(tab, focus = false) {
    for (const item of tabs) {
      const selected = item === tab;
      item.setAttribute('aria-selected', String(selected));
      item.tabIndex = selected ? 0 : -1;
      document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
    }
    if (focus) tab.focus();
  }
  for (const tab of tabs) {
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', event => {
      const index = tabs.indexOf(tab);
      const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : null;
      if (next !== null) { event.preventDefault(); selectTab(tabs[next], true); }
    });
  }
  const toast = document.getElementById('toast');
  let toastTimer;
  function notify(message) {
    toast.textContent = message;
    toast.classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('visible'), 3500);
  }
  for (const button of document.querySelectorAll('[data-copy]')) {
    button.addEventListener('click', async () => {
      const content = document.getElementById(button.dataset.copy).textContent;
      try {
        if (!navigator.clipboard) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(content);
        notify('Commands copied.');
      } catch {
        const range = document.createRange();
        range.selectNodeContents(document.getElementById(button.dataset.copy));
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        notify('Commands selected. Press Ctrl+C or âŒ˜C to copy.');
      }
    });
  }
  const currentPage = document.body.dataset.page;
  document.querySelector(`[data-nav="${currentPage}"]`)?.setAttribute('aria-current', 'page');
  const menuButton = document.querySelector('.menu-toggle');
  const mobileNav = document.getElementById('mobile-nav');
  function closeMenu() {
    if (!mobileNav) return;
    mobileNav.hidden = true;
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.setAttribute('aria-label', 'Open navigation');
  }
  menuButton?.addEventListener('click', () => {
    mobileNav.hidden = !mobileNav.hidden;
    menuButton.setAttribute('aria-expanded', String(!mobileNav.hidden));
    menuButton.setAttribute('aria-label', mobileNav.hidden ? 'Open navigation' : 'Close navigation');
  });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
  document.addEventListener('click', event => { if (mobileNav && !event.target.closest('.topbar')) closeMenu(); });
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (!reducedMotion.matches && 'IntersectionObserver' in window) {
    root.classList.add('motion-ready');
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    }, {threshold: 0.08});
    document.querySelectorAll('.reveal').forEach(element => observer.observe(element));
    reducedMotion.addEventListener('change', event => {
      if (event.matches) { root.classList.remove('motion-ready'); observer.disconnect(); }
    });
  }
  const billingButtons = document.querySelectorAll('[data-billing]');
  if (billingButtons.length) {
    const price = document.getElementById('pro-price'), period = document.getElementById('pro-period'), note = document.getElementById('pro-billing-note');
    billingButtons.forEach(button => button.addEventListener('click', () => {
      const annual = button.dataset.billing === 'annual';
      billingButtons.forEach(item => { const active = item === button; item.classList.toggle('active', active); item.setAttribute('aria-pressed', String(active)); });
      price.textContent = annual ? '$49.99' : '$5.99'; period.textContent = annual ? 'per year' : 'per month';
      note.textContent = annual ? 'Billed annually · save 30% · planned launch 31 October 2026' : 'Billed monthly · planned launch 31 October 2026';
    }));
  }
  const releaseStatus = document.getElementById('release-status');
  if (releaseStatus) {
    const download = document.getElementById('installer-download');
    const detail = document.getElementById('download-detail');
    const notes = document.getElementById('release-notes');
    function displayRelease(release) {
      const asset = release.assets?.find(item => /^BloonsPlusSetup.*\.exe$/i.test(item.name));
      if (!asset) return false;
      const url = new URL(asset.browser_download_url);
      if (url.protocol !== 'https:' || url.hostname !== 'github.com' || !url.pathname.startsWith('/Klaasawastaken/BloonsPlus/releases/download/')) return false;
      download.href = url.href;
      download.textContent = 'Download Windows installer ↓';
      releaseStatus.textContent = `${release.tag_name} · Windows x64 preview`;
      detail.textContent = `${(asset.size / 1048576).toFixed(1)} MB · Dependencies download during setup`;
      notes.href = release.html_url;
      return true;
    }
    async function loadRelease() {
      try {
        const response = await fetch('https://api.github.com/repos/Klaasawastaken/BloonsPlus/releases/latest', {signal: AbortSignal.timeout(8000)});
        if (!response.ok) throw new Error('No published installer');
        if (!displayRelease(await response.json())) throw new Error('No installer asset');
        return;
      } catch {}
      try {
        const local = await fetch('../release.json', {cache: 'no-cache'});
        if (local.ok && displayRelease(await local.json())) return;
        throw new Error('No local installer metadata');
      } catch {
        releaseStatus.textContent = 'No installer could be confirmed. Check GitHub releases.';
        detail.textContent = 'You can download the source below and follow the guide.';
      }
    }
    loadRelease();
  }
})();

const wikiSearch = document.querySelector('#wiki-search');
wikiSearch?.addEventListener('input', () => {
  const query = wikiSearch.value.trim().toLowerCase(); let matches = 0;
  document.querySelectorAll('.wiki-entry').forEach(card => { const visible = (card.dataset.search || card.textContent).toLowerCase().includes(query); card.hidden = !visible; if (visible) matches++; });
  document.querySelector('#wiki-no-results').hidden = matches > 0;
});

// A slim progress indicator follows document scrolling without polling.
const readingProgress = document.createElement('div'); readingProgress.className = 'reading-progress'; readingProgress.setAttribute('aria-hidden', 'true'); document.body.append(readingProgress);
let progressFrame = 0;
function updateReadingProgress() { progressFrame = 0; const height = document.documentElement.scrollHeight - innerHeight; readingProgress.style.transform = `scaleX(${height > 0 ? Math.min(1, scrollY / height) : 0})`; }
addEventListener('scroll', () => { if (!progressFrame) progressFrame = requestAnimationFrame(updateReadingProgress); }, { passive: true });
addEventListener('resize', updateReadingProgress); updateReadingProgress();
