// Private source, build output and runtime material must never be static assets.
function privateStaticPath(requested) {
  const segments = requested.replace(/\\/g, '/').split('/');
  const first = segments[0].toLowerCase();
  return segments.some(segment => segment.startsWith('.'))
    || ['private', 'lib', 'node_modules', 'dist', 'tools', 'vm', 'autobtd6', 'python'].includes(first)
    || /\.(save|key|pem|pfx|p12|log)$/i.test(requested);
}
module.exports = { privateStaticPath };
