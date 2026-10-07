const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
async function read(width, shortReading) {
  let output='', finish;
  const done=new Promise(resolve=>{finish=resolve;});
  const crops=[];
  const context={Buffer,require(name){
    if(name==='../lib/ocr')return {
      async readTitle(){return 'noise';},
      async readNaturalText(bytes,box){crops.push(box);return box.w===Math.round(260*width/2560)?shortReading:'nps';},
      shutdown:finish,
    };
    if(name==='pngjs')return {PNG:{sync:{read:()=>({width,height:width*9/16,data:Buffer.alloc(width*(width*9/16)*4)})}}};
    throw Error(name);
  },process:{stdin:{async *[Symbol.asyncIterator](){yield Buffer.from('fixture');}},
    stdout:{write(value){output+=value;}},stderr:{write(value){throw Error(value);}}}};
  vm.runInNewContext(fs.readFileSync('tools/read-hero-selection.js','utf8'),context);
  await done;return {state:JSON.parse(output),crops};
}
(async()=>{
  for(const width of [960,1920,2560]){
    const {state,crops}=await read(width,"'PSI=—");
    assert.ok(state.titleCandidates.includes('psi'),'Keep exact PSI from the short banner crop');
    assert.equal(state.button,'unknown','A readable title does not establish selection');
    assert.ok(crops.some(box=>box.x===Math.round(860*width/2560)&&box.y===Math.round(40*width/2560)&&box.w===Math.round(260*width/2560)));
  }
  for(const value of ['','PS','PSIM','CAPT','NOTPSI','EZIL','SAUD']){
    const {state}=await read(960,value);
    assert.ok(!state.titleCandidates.includes('psi'),'Do not infer PSI from fragments');
    assert.ok(!state.titleCandidates.includes(value.toLowerCase()),'Do not expose arbitrary truncated names');
  }
  console.log('Short PSI title requires exact readable text and never implies selection.');
})().catch(error=>{console.error(error);process.exitCode=1;});
