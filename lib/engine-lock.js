// One mouse, one keyboard, one game window: only one automation engine may run at a time, whichever
// engine it is. Every engine bridge (AutoBTD6 in automation.js, BTD6bot, btd6_autoplay) registers its
// job here instead of keeping its own private "current job" — otherwise two engines could each think
// they're idle and fight over the same cursor.
const { execFile } = require('node:child_process');

let currentJob = null;
const lastJobs = {};

function getCurrentJob() { return currentJob; }
function getLastJob(engine) { return lastJobs[engine] || null; }

function beginJob(engine, type) {
  if (currentJob) return null;
  currentJob = { engine, type, log: [], startedAt: Date.now(), stopRequested: false, paused: false,
    stopAfterReplay: false, victories: 0, defeats: 0, lastOutcome: null, seenIngame: false,
    proc: null, onEnd: null };
  return currentJob;
}

// Called by the engine itself when its job finishes on its own (win, loss, crash).
function endJob(job) {
  // A stop can kill the child and its `close` handler can then race with this
  // cleanup path. Persist the final run exactly once.
  if (job.endedAt) return;
  if (job.proc?.pid && job.proc.exitCode === null && job.proc.signalCode === null) {
    // A rejected termination must never release the mouse/keyboard to a second runner.
    if (!job.endWhenClosed) {
      job.endWhenClosed = true;
      job.proc.once('close', () => endJob(job));
    }
    return;
  }
  job.endedAt ??= Date.now();
  lastJobs[job.engine] = job;
  try { job.onEnd?.(job); } catch { /* persistence hook failures must not wedge the lock */ }
  if (currentJob === job) currentJob = null;
}

function pushLog(job, line) {
  job.log.push(line);
  if (/screen INGAME!/.test(line)) {
    job.lastOutcome = null;
    job.seenIngame = true;
  }
  const outcome = /VICTORY_CONFIRMED\b|screen (?:VICTORY|VICTORY_SUMMARY)!/.test(line) ? 'victory'
    : /screen DEFEAT!/.test(line) ? 'defeat' : null;
  // A replay can begin on a result screen left over from an earlier/manual game. Do not charge
  // that result to this job: only count a result after this job has actually observed INGAME.
  // The medal sweep counts victories only after automation confirms the saved
  // medal. A screen transition alone can precede a delayed or failed save.
  const awaitsMedal = outcome === 'victory' && job.type === 'black-border-sweep';
  if (outcome && !awaitsMedal && job.seenIngame && job.lastOutcome !== outcome) {
    job[`${outcome === 'victory' ? 'victories' : 'defeats'}`] = (job[`${outcome === 'victory' ? 'victories' : 'defeats'}`] || 0) + 1;
    job.lastOutcome = outcome;
    job.seenIngame = false;
  }
  if (job.log.length > 2000) job.log.shift();
}

// A few seconds' grace before anything actually spawns, so there's time to alt-tab into BTD6 before
// the automation starts moving the mouse. Stoppable during the countdown itself.
const STARTUP_COUNTDOWN_SECONDS = 5;
function afterCountdown(job, run) {
  let remaining = STARTUP_COUNTDOWN_SECONDS;
  pushLog(job, `starting in ${remaining}s...`);
  const tick = () => {
    if (job.stopRequested) { pushLog(job, 'cancelled before starting'); endJob(job); return; }
    remaining--;
    if (remaining <= 0) return run();
    pushLog(job, `starting in ${remaining}s...`);
    setTimeout(tick, 1000);
  };
  setTimeout(tick, 1000);
}

// Kills by the exact child PID (with /T for its own process tree only) — never a blanket image-name
// kill, which has bitten this project before.
function killProcessTree(proc) {
  return new Promise((resolve, reject) => {
    if (!proc || proc.pid == null || proc.exitCode != null || proc.signalCode != null) return resolve();
    let settled = false;
    const finish = error => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      proc.removeListener('close', closed);
      if (error) reject(error); else resolve();
    };
    const closed = () => finish();
    const timeout = setTimeout(() => finish(new Error('replay did not exit within 15 seconds')), 15_000);
    proc.once('close', closed);
    if (process.platform === 'win32') {
      execFile('taskkill', ['/PID', String(proc.pid), '/T', '/F'], { windowsHide: true, timeout: 10_000 }, error => {
        if (error && proc.exitCode == null && proc.signalCode == null) finish(error);
      });
    } else {
      try { if (!proc.kill('SIGTERM')) finish(new Error('could not signal replay process')); }
      catch (error) { finish(error); }
    }
  });
}

// Stops whichever engine is running — there's only ever one.
async function stopCurrent() {
  const job = currentJob;
  if (!job) return { error: 'not-running' };
  job.stopRequested = true;
  pushLog(job, 'stopped by user');
  const proc = job.proc;
  try { await killProcessTree(proc); }
  catch (error) {
    pushLog(job, `stop failed: ${error.message}; keeping the input lock until the replay exits`);
    return { error: error.message, engine: job.engine };
  }
  endJob(job);
  return { ok: true, engine: job.engine };
}

module.exports = { getCurrentJob, getLastJob, beginJob, endJob, pushLog, afterCountdown, killProcessTree, stopCurrent };
