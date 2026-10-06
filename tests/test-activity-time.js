const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require.resolve('../assets/app/app.js'),'utf8').replace(/\r\n/g,'\n');
const start=source.indexOf('let sourceClock =');
const end=source.indexOf('\ntry { accumulatedRunLog',start);
assert.ok(start>=0 && end>start,'Production source-clock helpers must exist');
const context=vm.createContext({Date});
vm.runInContext(source.slice(start,end),context);
const now=1791226200000;
const offset=9*3600*1000;
assert.equal(context.sourceAgeMs(now,now),null,'No source clock means age is unknown');
context.observeSourceClock({sourceNow:now+offset},now-100,now+100);
assert.equal(context.sourceAgeMs(new Date(now+offset-12000).toISOString(),now),12000);
assert.equal(context.sourceAgeMs((now+offset)/1000,now),0);
assert.equal(context.sourceAgeMs(String((now+offset)/1000),now+65000),65000);
assert.equal(context.sourceAgeMs(now+offset+120000,now),null,'Large future timestamps are unknown');
assert.equal(context.sourceAgeMs(now+offset+1000,now),0,'Small transport skew is tolerated');
assert.equal(context.sourceAgeMs('invalid',now),null);
assert.equal(context.sourceAgeMs(undefined,now),null);
for(const flag of ['statusStale','statusUnavailable']){
 context.observeSourceClock({sourceNow:now+20*3600*1000,[flag]:true},now,now);
 assert.equal(context.sourceAgeMs(now+offset,now+100000),100000,'Cached responses cannot recalibrate the guest clock');
}
context.observeSourceClock({sourceNow:NaN},now,now);
assert.equal(context.sourceAgeMs(now+offset,now+110000),110000);
console.log('Activity ages use the live guest clock; cached and unknown times remain guarded.');
