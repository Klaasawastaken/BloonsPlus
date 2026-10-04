const { StringDecoder } = require('node:string_decoder');

// A pipe chunk is not a log line: UTF-8 characters and even the word "round" can
// be split across writes. Emit every line exactly once, including CR progress lines.
function createLineReader(consume) {
  const decoder = new StringDecoder('utf8');
  let pending = '';
  function drain(text, end = false) {
    pending += text;
    const lines = pending.split(/[\r\n]/);
    pending = lines.pop();
    for (const line of lines) if (line) consume(line);
    if (end && pending) { consume(pending); pending = ''; }
  }
  return { write: chunk => drain(decoder.write(chunk)), end: () => drain(decoder.end(), true) };
}

function createReplayMonitor({ now = Date.now, menuStallMs = 180_000,
  roundStallMs = 480_000, maxRunMs = 7_200_000 } = {}) {
  let startedAt = now();
  let pausedAt = null;
  let screen = 'UNKNOWN';
  let outsideGameAt = startedAt;
  let lastRoundAt = startedAt;
  let enteredGame = false;
  let round = null;
  let pendingRound = null;
  let pendingReads = 0;
  let fatal = null;

  function setPaused(paused) {
    if (paused && pausedAt === null) pausedAt = now();
    else if (!paused && pausedAt !== null) {
      const duration = Math.max(0, now() - pausedAt);
      startedAt += duration;
      lastRoundAt += duration;
      if (outsideGameAt !== null) outsideGameAt += duration;
      pausedAt = null;
    }
  }

  function observe(line) {
    if (pausedAt !== null) return;
    const timestamp = now();
    const detectedScreen = line.match(/DEBUG loop screen=([A-Z_]+)/)?.[1]
      || line.match(/\bscreen ([A-Z_]+)!/)?.[1];
    if (detectedScreen) {
      if (detectedScreen === 'INGAME') {
        if (!enteredGame) { lastRoundAt = timestamp; enteredGame = true; }
        outsideGameAt = null;
      } else if (outsideGameAt === null) {
        // Victory, pause and menu transitions get a fresh recovery window,
        // regardless of how long the preceding game lasted.
        outsideGameAt = timestamp;
      }
      screen = detectedScreen;
    }
    const match = line.match(/DEBUG OCR values .*\bround=(-?\d+)/);
    if (match && screen === 'INGAME') {
      const candidate = Number(match[1]);
      if (candidate >= 0 && candidate <= 200) {
        pendingReads = candidate === pendingRound ? pendingReads + 1 : 1;
        pendingRound = candidate;
        // Require repeat observations, and never treat OCR oscillation backwards
        // as progress. A single erroneous high round must not poison the timer.
        if (pendingReads >= 2 && (round === null || candidate > round)) {
          round = candidate;
          lastRoundAt = timestamp;
        }
      } else { pendingRound = null; pendingReads = 0; }
    }
    if (/RuntimeError: (BTD6 window not found|Could not read BTD6 client area|BTD6 window is minimized)/i.test(line)) {
      fatal = 'game-unavailable';
    } else if (/RuntimeError: BTD6 client area must be near/i.test(line)) {
      fatal = 'invalid-window';
    }
  }

  function stalled() {
    if (pausedAt !== null) return null;
    const timestamp = now();
    if (timestamp - startedAt >= maxRunMs) return 'maximum route duration reached';
    if (outsideGameAt !== null && timestamp - outsideGameAt >= menuStallMs)
      return `navigation or recovery stalled on ${screen}`;
    if (outsideGameAt === null && timestamp - lastRoundAt >= roundStallMs)
      return `round ${round ?? 'unreadable'} made no confirmed progress`;
    return null;
  }
  return { observe, stalled, setPaused, snapshot: () => ({ screen, round, fatal, lastRoundAt }) };
}

// Route edits reset the retry budget; an old failure must not disable repaired data.
function canAttempt(prior, hash) {
  if (!prior || prior.hash !== hash) return true;
  // A real played loss is evidence for this exact route version. Do not burn
  // another medal attempt after an app/sweep restart; editing the route changes
  // its hash and makes it eligible again. Navigation and instant-placement
  // failures explicitly save zero attempts and remain retryable.
  return prior.outcome !== 'cleared' && (Number(prior.attempts) || 0) < 1;
}

module.exports = { createLineReader, createReplayMonitor, canAttempt };
