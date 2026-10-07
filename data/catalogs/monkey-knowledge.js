// Shared save-backed knowledge state. Ownership and activation are independent.
(function (root) {
  const normalize = value => String(value ?? '').toLowerCase().replace(/[^a-z0-9]/g, '')
    .replace(/^(bonusmonkey|bonusgluegunner)knowledge$/, '$1');
  function ids(value) {
    if (!Array.isArray(value)) return null;
    const result = [];
    for (const item of value) {
      const id = typeof item === 'string' ? item : item?.id ?? item?.name;
      if (typeof id !== 'string' || !normalize(id)) return null;
      if (!result.some(existing => normalize(existing) === normalize(id))) result.push(id);
    }
    return result;
  }
  function activity(knowledge, id) {
    if (knowledge?.enabled === false) return false;
    const acquired = ids(knowledge?.acquired);
    if (!acquired) return null;
    if (!acquired.some(owned => normalize(owned) === normalize(id))) return false;
    if (knowledge?.enabled !== true) return null;
    // Older profiles have no per-point switch list. A present but malformed
    // list is unknown, never equivalent to all points being enabled.
    const disabled = knowledge.disabled === undefined ? [] : ids(knowledge.disabled);
    if (!disabled) return null;
    return !disabled.some(off => normalize(off) === normalize(id));
  }
  function summarize(knowledge) {
    if (knowledge?.enabled === false) return { state: 'disabled', active: [] };
    const acquired = ids(knowledge?.acquired);
    const disabled = knowledge?.disabled === undefined ? [] : ids(knowledge.disabled);
    if (knowledge?.enabled !== true || !acquired || !disabled) return { state: 'unknown', active: null };
    const active = acquired.filter(id => activity(knowledge, id) === true);
    return { state: active.length === acquired.length ? 'enabled' : 'partial', active };
  }
  const api = Object.freeze({ ids, activity, summarize });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BloonsKnowledge = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
