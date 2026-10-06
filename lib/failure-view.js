// The default diagnostics response retains full evidence for explicit exports.
// Page views only need the failure index, not every replay's frame/action/log arrays.
function failureResponseView(body, compact) {
  if (!compact || !body || typeof body !== 'object') return body;
  const fields = ['at','map','gamemode','route','reason','interrupted','defeatObserved',
    'lastRound','finalRound','livesLeft','result','cash','category','actionable'];
  return {...body, view:'ui', failures:(Array.isArray(body.failures) ? body.failures : []).map(failure =>
    Object.fromEntries(fields.filter(key => Object.hasOwn(failure,key)).map(key => [key,failure[key]])))};
}
module.exports = {failureResponseView};
