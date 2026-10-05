// UI polling needs the active sweep, not its persistent candidate/failure history.
// The full status API and stored progress remain unchanged.
function uiFarmStatus(status) {
  const progress = {};
  for (const key of ['blackBorderSweep', 'routeVerification', 'achievementsSweep', 'medalScan']) {
    if (Object.prototype.hasOwnProperty.call(status.progress || {}, key)) {
      progress[key] = status.progress[key];
    }
  }
  return { ...status, progress };
}

module.exports = { uiFarmStatus };
