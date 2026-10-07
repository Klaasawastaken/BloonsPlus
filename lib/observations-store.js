const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);

// This queue serializes this writer's updates across retry delays. Each attempt
// stays synchronous so the existing in-process scanners cannot interleave a
// write between our read and replacement. Separate processes are not locked;
// every retry reads their latest document before merging.
function createObservationWriter({ io = fs, delay = ms => new Promise(resolve => setTimeout(resolve, ms)) } = {}) {
  const pending = new Map();
  async function write(file, mutate) {
    for (let attempt = 0; ; attempt++) {
      const temporary = `${file}.${process.pid}.${randomUUID()}.tmp`;
      let created = false;
      try {
        let value;
        try { value = JSON.parse(io.readFileSync(file, 'utf8')); }
        catch (error) {
          if (error.code !== 'ENOENT') throw error;
          value = { source: 'live-scan', maps: {} };
        }
        if (!isObject(value) || (value.maps !== undefined && !isObject(value.maps))) {
          throw new TypeError('Observation cache is not a valid document');
        }
        value.maps ||= {};
        mutate(value);
        const handle = io.openSync(temporary, 'wx');
        created = true;
        try {
          io.writeFileSync(handle, JSON.stringify(value, null, 2), 'utf8');
          io.fsyncSync(handle);
        } finally { io.closeSync(handle); }
        io.renameSync(temporary, file);
        return;
      } catch (error) {
        if (!['EPERM', 'EACCES', 'EBUSY'].includes(error.code) || attempt >= 3) throw error;
        await delay(50 << attempt);
      } finally {
        // Never remove the destination to work around a failed replacement.
        if (created) { try { io.unlinkSync(temporary); } catch {} }
      }
    }
  }
  return (file, mutate) => {
    const key = path.resolve(file);
    const next = (pending.get(key) || Promise.resolve()).then(() => write(file, mutate));
    const settled = next.catch(() => {}).finally(() => {
      if (pending.get(key) === settled) pending.delete(key);
    });
    pending.set(key, settled);
    return next;
  };
}

module.exports = { createObservationWriter, updateObservations: createObservationWriter() };
