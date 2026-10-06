const {execFileSync} = require('node:child_process');

function readActiveSteamAccount() {
  try {
    const text = execFileSync('reg', ['query','HKCU\\Software\\Valve\\Steam\\ActiveProcess','/v','ActiveUser'],
      {windowsHide:true,timeout:5000,encoding:'utf8',stdio:['ignore','pipe','ignore']});
    const match = text.match(/ActiveUser\s+REG_DWORD\s+(0x[0-9a-f]+|[0-9]+)/i);
    const id = match ? Number(match[1]) : NaN;
    if (Number.isSafeInteger(id) && id >= 0 && id <= 0xffffffff)
      return {state:id ? 'active' : 'inactive', id:id ? String(id) : null};
  } catch { /* No active Steam client signal; a single cache can still be read. */ }
  return {state:'unknown',id:null};
}
function selectSteamAccount(candidates, account) {
  const ids = [...new Set(candidates)];
  if (account.state === 'active') return ids.includes(account.id) ? account.id : null;
  if (account.state === 'inactive') return null;
  return ids.length === 1 ? ids[0] : null;
}
module.exports = {readActiveSteamAccount,selectSteamAccount};
