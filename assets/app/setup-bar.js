// Setup bar: shows the first-run VM setup at the top of the app until every step is done.
// Polls /api/setup/status (vm-setup.js) and drives /api/setup/start. Self-contained on purpose:
// Shares the same detected setup state with the Settings game environment panel.
(() => {
  const bar = document.getElementById('setup-bar');
  if (!bar) return;
  const $ = id => document.getElementById(id);
  const nextText = $('setup-bar-next'), button = $('setup-bar-button'), hideButton = $('setup-bar-hide');
  const isoInput = $('setup-bar-iso'), stepsList = $('setup-bar-steps'), activity = $('setup-bar-activity');
  const progress = $('setup-bar-progress'), progressFill = progress.querySelector('span');
  const settingsStatus = $('vm-settings-status'), settingsSteps = $('vm-settings-steps');
  const settingsChip = $('vm-settings-chip'), settingsStart = $('vm-settings-start');
  const settingsProgress = $('vm-settings-progress'), settingsProgressLabel = $('vm-settings-progress-label');
  const settingsIso = $('vm-settings-iso'), settingsRefresh = $('vm-settings-refresh'), settingsUpdate = $('vm-settings-update');
  let hiddenByUser = false;
  try { hiddenByUser = sessionStorage.getItem('setupBarHidden') === '1'; } catch { /* storage blocked */ }
  let firstRunSeen = false;
  try { firstRunSeen = localStorage.getItem('bloonsSetupPrepageSeen') === '1'; } catch { /* storage blocked */ }
  let timer = null, last = null, pollPending = false, actionPending = false, actionError = '';
  const downloadHelp = document.createElement('a');
  downloadHelp.href = 'https://www.microsoft.com/software-download/windows11';
  downloadHelp.target = '_blank'; downloadHelp.rel = 'noopener noreferrer';
  downloadHelp.className = 'quiet-button';
  downloadHelp.textContent = 'Get Windows 11 from Microsoft';
  downloadHelp.hidden = true;
  isoInput.insertAdjacentElement('afterend', downloadHelp);

  function render(status) {
    last = status;
    const setupJob = status.job || {};
    if (settingsStatus) {
      const next = status.next || {};
      $('vm-settings-title').textContent = status.applicable ? 'Game & VM' : 'Game connection';
      $('vm-settings-description').textContent = status.applicable
        ? 'Connect your game and keep it up to date.'
        : 'VM setup is managed from your main PC.';
      settingsStatus.textContent = actionError || (setupJob.error ? `Setup stopped: ${setupJob.error}`
        : setupJob.running ? (setupJob.activity || 'Setting up the VM…')
        : status.allDone ? 'Ready: VM connected, Steam signed in, and BTD6 installed.'
        : next.message || status.reason || 'Checking setup…');
      settingsStatus.classList.toggle('error', !!setupJob.error || !!actionError);
      settingsChip.textContent = actionError ? 'NEEDS ATTENTION' : !status.applicable ? 'LOCAL' : setupJob.running ? 'WORKING' : setupJob.error ? 'NEEDS ATTENTION' : status.allDone ? 'READY' : 'ACTION NEEDED';
      settingsStart.hidden = !status.applicable || status.allDone;
      const advanced = $('vm-settings-advanced');
      const needsIso = status.applicable && !(status.steps || []).some(step => step.id === 'vm' && step.done) && !(status.steps || []).some(step => step.id === 'iso' && step.done);
      if ($('vm-settings-iso-field')) $('vm-settings-iso-field').hidden = !needsIso;
      if ($('vm-settings-iso-hint')) $('vm-settings-iso-hint').hidden = !needsIso;
      if (advanced) advanced.hidden = !needsIso;
      const checks = status.steps || [];
      if ($('vm-settings-checks')) $('vm-settings-checks').hidden = !status.applicable || !checks.length;
      if ($('vm-settings-check-count')) $('vm-settings-check-count').textContent = `${checks.filter(step => step.done).length}/${checks.length} ready`;
      if (settingsUpdate) settingsUpdate.hidden = !status.applicable;
      if ($('vm-settings-actions')) $('vm-settings-actions').hidden = !status.applicable;
      if ($('vm-settings-update-hint')) $('vm-settings-update-hint').hidden = !status.applicable;
      if (settingsProgress && settingsProgressLabel) {
        const checks = status.steps || [];
        const completed = checks.filter(step => step.done).length;
        const partial = Number.isFinite(setupJob.progress) ? Math.max(0, Math.min(1, setupJob.progress)) : 0;
        const percent = checks.length ? Math.min(100, Math.round((completed + partial) / checks.length * 100)) : 0;
        settingsProgress.hidden = settingsProgressLabel.hidden = !setupJob.running || !checks.length;
        settingsProgress.setAttribute('aria-valuenow', String(percent));
        settingsProgress.querySelector('span').style.width = `${percent}%`;
        settingsProgressLabel.textContent = `${completed} of ${checks.length} checks ready · ${percent}%`;
      }
      settingsSteps.replaceChildren(...(status.steps || []).map(step => {
        const item = document.createElement('li');
        item.className = step.done ? 'done' : step.id === next.id ? 'current' : '';
        item.textContent = `${step.done ? '✓' : '○'} ${step.title} · ${step.detail || 'Pending'}`;
        return item;
      }));
      settingsStart.disabled = actionPending || !status.applicable || status.allDone || !!setupJob.running || !next.button;
      settingsStart.textContent = setupJob.running ? 'Working…' : setupJob.error && next.button ? 'Retry setup' : next.button || (status.allDone ? 'Setup complete' : 'Restart required');
      if (settingsUpdate) settingsUpdate.disabled = actionPending || !status.applicable || !!setupJob.running || !(status.vm?.state === 'online' || status.allDone);
    }
    const show = status.applicable && !status.allDone && !hiddenByUser;
    bar.hidden = !show;
    bar.classList.toggle('setup-prepage', show && !firstRunSeen);
    if (status.allDone && !firstRunSeen) {
      firstRunSeen = true;
      try { localStorage.setItem('bloonsSetupPrepageSeen', '1'); } catch { /* storage blocked */ }
    }
    if (!show) return;
    const job = status.job || {};
    const next = status.next || {};
    const done = (status.steps || []).filter(step => step.done).length;
    nextText.textContent = job.running ? (job.activity || 'Working…') : job.error
      ? 'Setup paused. Your completed steps are saved. Review the details below, then retry.'
      : `${done} of ${(status.steps || []).length} checks ready. ${next.message || ''}`;
    stepsList.replaceChildren(...(status.steps || []).map(step => {
      const item = document.createElement('li');
      item.className = step.done ? 'done' : step.id === next.id ? 'current' : '';
      item.textContent = `${step.done ? '✓' : step.id === next.id ? '→' : '○'} ${step.title}`;
      item.title = step.detail || '';
      return item;
    }));
    button.hidden = !next.button;
    button.textContent = job.running ? 'Working…' : job.error ? 'Retry this step' : next.button || '';
    button.disabled = actionPending || !!job.running;
    isoInput.hidden = !(next.isoInput && !job.running);
    downloadHelp.hidden = isoInput.hidden;
    isoInput.placeholder = 'Or paste the path to an existing Windows 11 ISO';
    // Always show a determinate overall step bar. A download can provide a finer
    // fraction; otherwise completed steps plus the active step still give useful
    // feedback instead of leaving users stuck on a label such as “VM online”.
    const stepCount = (status.steps || []).length;
    const doneCount = (status.steps || []).filter(step => step.done).length;
    const stepFraction = stepCount ? doneCount / stepCount : 0;
    const fraction = typeof job.progress === 'number' ? Math.min(1, (doneCount + job.progress) / Math.max(1, stepCount)) : stepFraction;
    progress.hidden = !stepCount;
    progressFill.style.width = `${Math.round(fraction * 100)}%`;
    const message = job.error ? job.error : job.running ? '' : job.activity;
    activity.hidden = !message;
    activity.textContent = message || '';
    activity.classList.toggle('error', !!job.error);
  }

  async function poll() {
    if (pollPending) return;
    pollPending = true;
    clearTimeout(timer);
    try {
      const response = await fetch('/api/setup/status', { cache: 'no-store', signal: AbortSignal.timeout(12000) });
      if (!response.ok) throw new Error(`Connection check failed (${response.status})`);
      render(await response.json());
    } catch {
      if (settingsStatus) {
        settingsStatus.textContent = actionError || 'Waiting for the Bloons+ controller to reconnect…';
        settingsStatus.classList.toggle('error', !!actionError);
      }
      if ($('vm-settings-check-count')) $('vm-settings-check-count').textContent = 'Last known state';
      if (settingsProgress) settingsProgress.hidden = true;
      if (settingsProgressLabel) settingsProgressLabel.hidden = true;
      if (settingsChip) settingsChip.textContent = 'RECONNECTING';
      // Stale setup state must not leave install/update actions available.
      if (settingsStart) settingsStart.disabled = true;
      if (settingsUpdate) settingsUpdate.disabled = true;
      button.disabled = true;
    }
    // Fast while setup works, slower otherwise; keep checking after completion so the bar returns if the VM stops.
    pollPending = false;
    const delay = last?.job?.running ? 2000 : last && (last.allDone || !last.applicable) ? 30000 : 5000;
    timer = setTimeout(poll, delay);
  }

  button.addEventListener('click', async () => {
    if (actionPending) return;
    actionPending = true; actionError = '';
    firstRunSeen = true;
    bar.classList.remove('setup-prepage');
    try { localStorage.setItem('bloonsSetupPrepageSeen', '1'); } catch { /* storage blocked */ }
    button.disabled = true;
    try {
      const response = await fetch('/api/setup/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(isoInput.hidden || !isoInput.value.trim() ? {} : { isoPath: isoInput.value.trim() }),
      });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || `HTTP ${response.status}`);
    } catch (error) {
      actionError = `Could not start setup: ${error.message}`;
      activity.hidden = false; activity.textContent = `Could not start setup: ${error.message}`; activity.classList.add('error');
    }
    actionPending = false;
    poll();
  });

  hideButton.addEventListener('click', () => {
    hiddenByUser = true;
    try { sessionStorage.setItem('setupBarHidden', '1'); } catch { /* storage blocked */ }
    bar.hidden = true;
  });

  settingsStart?.addEventListener('click', async () => {
    if (actionPending) return;
    actionPending = true; actionError = '';
    settingsStart.disabled = true;
    try {
      const response = await fetch('/api/setup/start', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(!$('vm-settings-iso-field')?.hidden && settingsIso.value.trim() ? { isoPath: settingsIso.value.trim() } : {}) });
      if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || `HTTP ${response.status}`);
    } catch (error) {
      actionError = `Could not start setup: ${error.message}`;
      settingsStatus.textContent = actionError;
      settingsStatus.classList.add('error');
    }
    actionPending = false;
    poll();
  });
  settingsRefresh?.addEventListener('click', poll);
  settingsUpdate?.addEventListener('click', async () => {
    if (actionPending) return;
    actionPending = true; actionError = '';
    settingsUpdate.disabled = true;
    if (settingsStatus) { settingsStatus.textContent = 'Sending the latest Bloons+ build to the VM…'; settingsStatus.classList.remove('error'); }
    try {
      const response = await fetch('/api/setup/update', { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || `Update failed (${response.status})`);
      if (settingsStatus) settingsStatus.textContent = 'VM update started. This page will show its progress.';
    } catch (error) {
      actionError = `Could not update VM: ${error.message}`;
      if (settingsStatus) { settingsStatus.textContent = error.message; settingsStatus.classList.add('error'); }
      // A failed update may also mean the controller disconnected. Recheck
      // availability before enabling another update request.
    }
    actionPending = false;
    await poll();
  });

  poll();
})();
