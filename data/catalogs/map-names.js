// Exact game-save names and display names share one identity. Never fuzzy-match medals.
(function (root) {
  const aliases = Object.freeze({ towncentre: 'towncenter', threeminesaround: 'threeminesround' });
  function normalize(value) {
    const key = String(value ?? '').toLowerCase().replace(/[^a-z0-9]/g, '');
    return aliases[key] || key;
  }
  const api = Object.freeze({ normalize });
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BloonsMapNames = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
