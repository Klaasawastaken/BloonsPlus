const OPERATIONS = new Set(['install', 'update', 'repair', 'resume']);
const PHASES = {
  vmp: 'enabling_feature', appsandbox: 'downloading', daemon: 'starting_vm',
  iso: 'downloading', vm: 'configuring_vm', provision: 'configuring_guest',
  connected: 'validating', steam: 'validating',
};
const WEIGHTS = { vmp: 8, appsandbox: 7, daemon: 5, iso: 20, vm: 25, provision: 20, connected: 10, steam: 5 };
const clone = value => structuredClone(value);

// One coordinator owns commands. Checkpoints describe observations; they never
// replace a fresh readiness or replay-ownership probe after reopening.
function createSetupSession(config, dependencies) {
  if (!OPERATIONS.has(config.operation)) throw new TypeError('Invalid setup operation');
  if (!/^[a-f0-9]{32}$/.test(config.sessionId) || !/^[a-f0-9]{64}$/.test(config.owner))
    throw new TypeError('Invalid setup identity');
  const { getStatus, getReplayStatus, start, persist = () => {}, now = Date.now } = dependencies;
  const saved = config.checkpoint;
  const matching = saved && saved.protocolVersion === 1 && saved.sessionId === config.sessionId
    && saved.owner === config.owner && saved.operation === config.operation && Number.isSafeInteger(saved.sequence) && saved.sequence >= 0;
  let state = {
    protocolVersion: 1, sessionId: config.sessionId, owner: config.owner, operation: config.operation,
    sequence: matching ? saved.sequence : 0, observedAt: new Date(now()).toISOString(),
    phase: matching ? 'recovering' : 'idle', step: null, status: 'Ready to check setup',
    planWeight: 100, completedWeight: 0, numerator: null, denominator: null, scope: null,
    indeterminate: false, humanAction: null, error: null, environmentValidated: false,
    restartDeferred: matching && saved.restartDeferred === true,
    queued: matching && saved.queued === true,
    operationOutstanding: matching && saved.operationOutstanding === true,
    operationBootIdentity: matching && typeof saved.operationBootIdentity === 'string' ? saved.operationBootIdentity : null,
  };
  let inFlight = false;
  let issued = false;
  let cancelled = false;
  let unobservedOwner = state.operationOutstanding;
  let options = Object.freeze({ isoPath: typeof config.options?.isoPath === 'string' ? config.options.isoPath : null });
  function publish(patch) {
    state = { ...state, numerator:null, denominator:null, scope:null, ...patch, sequence: state.sequence + 1, observedAt: new Date(now()).toISOString() };
    persist(clone(state));
    return clone(state);
  }
  function validObservation(status) {
    return status?.applicable === true && typeof status.allDone === 'boolean'
      && Array.isArray(status.steps) && status.steps.length > 0
      && status.steps.every(step => Object.hasOwn(WEIGHTS, step.id) && typeof step.done === 'boolean')
      && typeof status.job?.running === 'boolean';
  }
  async function reconcile() {
    const status = await getStatus(true);
    if (!validObservation(status)) return publish({ phase: 'recovering', status: 'Setup status could not be confirmed. Reconnect and retry.', humanAction: 'retry', indeterminate: false });
    const completedWeight = Object.entries(WEIGHTS).reduce((sum, [id, weight]) => sum + (status.steps.some(step => step.id === id && step.done) ? weight : 0), 0);
    const step = status.job.stepId || status.next?.id || null;
    if (status.job.state === 'restart-required' || status.steps.some(item => item.state === 'restart-required'))
      return publish({ phase: 'restart_required', step, status: 'Restart Windows to continue setup.', humanAction: 'restart', indeterminate: false, completedWeight });
    if (status.job.running) {
      issued = true; unobservedOwner = false;
      const measured = Number.isSafeInteger(status.job.numerator) && Number.isSafeInteger(status.job.denominator)
        && status.job.numerator >= 0 && status.job.denominator > 0 && status.job.numerator <= status.job.denominator;
      return publish({ phase: cancelled ? 'recovering' : PHASES[step] || 'preflight', step,
        status: cancelled ? 'Waiting for the current setup step to finish safely.' : status.job.activity || 'Setting up your environment',
        humanAction: null, completedWeight, indeterminate: !measured, operationOutstanding: true,
        numerator: measured ? status.job.numerator : null, denominator: measured ? status.job.denominator : null,
        scope: measured && typeof status.job.scope === 'string' ? status.job.scope : null });
    }
    if (cancelled) {
      // A fresh terminal observation releases only the owner we observed here.
      // Lost ownership still needs the separate recovery probe before Resume.
      if (!unobservedOwner) issued = false;
      return publish({ phase: 'cancelled', status: 'Setup paused. Completed work is retained.', humanAction: 'resume', queued: false, indeterminate: false, operationOutstanding:unobservedOwner });
    }
    if (status.job.error && !state.queued) {
      const ownerKnown = issued || !unobservedOwner;
      issued = false;
      return publish({ phase: 'failed', step, status: 'Setup needs attention. Retry after fixing the reported component.', error: { component: step, message: status.job.error }, humanAction: 'retry', indeterminate: false, queued: false, completedWeight,
        operationOutstanding: ownerKnown ? false : state.operationOutstanding });
    }
    if (issued && status.job.state === 'waiting-replay') {
      issued = false;
      return publish({phase:'recovering', step, status:'Waiting for this replay to finish or its status to reconnect.',
        humanAction:'wait_replay',queued:true,indeterminate:false,operationOutstanding:false,completedWeight});
    }
    if (unobservedOwner) {
      const boot = dependencies.getBootIdentity ? await dependencies.getBootIdentity() : null;
      const rebooted = typeof boot === 'string' && state.operationBootIdentity && boot !== state.operationBootIdentity;
      const observation = rebooted ? 'idle' : dependencies.getOperationStatus ? await dependencies.getOperationStatus() : 'unknown';
      if (observation !== 'idle') return publish({ phase: 'recovering', step, status: 'Previous setup work cannot yet be confirmed finished. Check details before resuming.', humanAction: 'wait_setup', indeterminate: false, completedWeight });
      unobservedOwner = false;
      publish({operationOutstanding:false});
    }
    // Require the actual guest connection and Steam/game checks, not just allDone.
    if ((state.operation !== 'update' || issued) && status.allDone && ['connected', 'steam'].every(id => status.steps.some(item => item.id === id && item.done))
        && status.steps.every(item => item.done))
      return publish({ phase: 'complete', step: null, status: 'Environment ready', environmentValidated: true, completedWeight: 100, queued: false, humanAction: null, indeterminate: false, operationOutstanding: false });
    if (issued) {
      issued = false;
      if (status.job.state === 'waiting-replay') return publish({phase:'recovering', step, status:'Waiting for this replay to finish or its status to reconnect.',
        humanAction:'wait_replay',queued:true,indeterminate:false,operationOutstanding:false,completedWeight});
      return publish({ phase: 'validating', step, status: status.next?.message || 'Waiting for setup readiness',
        humanAction: step === 'steam' ? 'steam_sign_in' : 'retry', indeterminate: false, completedWeight, queued: false, operationOutstanding: false });
    }
    if (!state.queued) return publish({ phase: state.phase === 'idle' ? 'idle' : 'recovering', step, humanAction:state.phase === 'idle' ? null : 'retry',
      status: status.next?.message || 'Setup requires another check', completedWeight, indeterminate: false });
    const replay = await getReplayStatus(status);
    if (!replay || replay.running !== false)
      return publish({ phase: 'recovering', step, status: 'Waiting for this replay to finish or its status to reconnect.', humanAction: 'wait_replay', completedWeight, indeterminate: false });
    // No awaited operation separates the last ownership check and operator start.
    if (cancelled) return clone(state);
    const boot = dependencies.getBootIdentity ? await dependencies.getBootIdentity() : null;
    // Repeat replay observation after the boot probe; it may have taken time.
    if (dependencies.getBootIdentity && (await getReplayStatus(status))?.running !== false)
      return publish({phase:'recovering',humanAction:'wait_replay',status:'Waiting for this replay to finish or its status to reconnect.',indeterminate:false});
    issued = true;
    publish({ operationOutstanding: true, operationBootIdentity:typeof boot === 'string' ? boot : null, queued: false, phase: PHASES[step] || 'preflight', step, status: 'Starting setup', indeterminate: true });
    try { await start({ ...options, operation: state.operation }); }
    catch (error) { issued = false; return publish({ phase: 'failed', error: { component: step, message: error.message }, status: 'Setup could not start. Check details and retry.', humanAction: 'retry', queued: false, indeterminate: false, operationOutstanding:false }); }
    return publish({ phase: PHASES[step] || 'preflight', step, status: 'Setup started', humanAction: null, error: null, queued: false, indeterminate: true, completedWeight });
  }
  async function exclusive(work) {
    if (inFlight) throw new Error('Setup observation or command already active');
    inFlight = true;
    try { return await work(); } finally { inFlight = false; }
  }
  return {
    snapshot: () => clone(state),
    options: () => clone(options),
    configure(value) {
      if (inFlight || issued || state.queued || state.operationOutstanding) throw new Error('Setup options cannot change while work is active');
      if (typeof value?.isoPath !== 'string' || value.isoPath.length > 4096) throw new Error('Invalid ISO choice');
      options = Object.freeze({isoPath:value.isoPath});
      return publish({});
    },
    observe: () => exclusive(reconcile),
    command(command) {
      return exclusive(async () => {
        if (command.sessionId !== state.sessionId || command.sequence !== state.sequence) throw new Error('Stale setup command');
        if (command.action === 'cancel') {
          cancelled = true;
          if (dependencies.cancel) await dependencies.cancel();
          return publish({ phase: issued ? 'recovering' : 'cancelled', queued: false, humanAction: issued ? null : 'resume', status: issued ? 'Waiting for the current setup step to finish safely.' : 'Setup paused', indeterminate: false });
        }
        if (command.action === 'restart_later' && state.phase === 'restart_required') return publish({ restartDeferred: true });
        if (command.action === 'open_vm' && dependencies.openVm) { await dependencies.openVm(); return reconcile(); }
        if (command.action === 'restart_now' && state.phase === 'restart_required' && dependencies.restart) { publish({restartDeferred:false}); await dependencies.restart(); return clone(state); }
        if (!['start', 'retry', 'resume'].includes(command.action)) throw new Error('Unsupported setup command');
        if (issued || state.queued || state.phase === 'complete') throw new Error('Setup already active or complete');
        cancelled = false;
        publish({ phase: 'preflight', queued: true, error: null, humanAction: null, environmentValidated: false });
        return reconcile();
      });
    },
  };
}

module.exports = { createSetupSession };
