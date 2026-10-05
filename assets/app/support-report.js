(function (root) {
  'use strict';
  function redact(value) {
    return String(value)
      .replace(/-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----/g, '[REDACTED PRIVATE KEY]')
      .replace(/(?:gh[pousr]_[A-Za-z0-9_]{15,}|github_pat_[A-Za-z0-9_]+|sk-(?:proj-)?[A-Za-z0-9_-]{20,})/g, '[REDACTED TOKEN]')
      .replace(/((?:authorization|username|steamname|playername|playerid|accountname|accountid|password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;]+)/gi, '$1[REDACTED]')
      .replace(/[A-Za-z0-9_.-]+@(?:\d{1,3}\.){3}\d{1,3}/g, '[USER]@[IP]')
      .replace(/Bearer\s+[^\s"']+/gi, 'Bearer [REDACTED]')
      .replace(/[A-Za-z]:[\\/]+Users[\\/]+[^\\/\r\n"']+/gi, 'C:\\Users\\[USER]')
      .replace(/\/(?:home|Users)\/[^/\s]+/g, '/home/[USER]')
      .replace(/\b7656119\d{10}\b/g, '[STEAM ID]')
      .replace(/\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, '[EMAIL]')
      .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[IP]')
      .replace(/([?&](?:token|key|secret|password)=)[^&\s]+/gi, '$1[REDACTED]');
  }
  root.BloonsSupport = { redact };
  if (typeof module !== 'undefined') module.exports = { redact };
})(typeof window === 'undefined' ? globalThis : window);
