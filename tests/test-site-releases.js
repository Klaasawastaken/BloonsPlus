const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('docs/site.js', 'utf8');
const start = source.indexOf('  const releaseStatus =');
const end = source.indexOf('\n})();', start);
async function scenario(remote, local, fail=false) {
 const nodes = Object.fromEntries(['release-status','installer-download','download-detail','release-notes'].map(id => [id,{}]));
 const calls = [];
 let settled;
 const done=new Promise(resolve=>settled=resolve);
 let block=source.slice(start,end).replace('    loadRelease();','    loadRelease().then(done);');
 vm.runInNewContext(block,{ document:{getElementById:id=>nodes[id]}, URL, Date, encodeURIComponent, AbortSignal,
  done:settled, fetch:async url=>{ calls.push(url); if(fail&&url.startsWith('https:'))throw Error('offline'); return {ok:true,json:async()=>url.startsWith('https:')?remote:local}; } });
 await done; return {nodes,calls};
}
function release(tag,date,url='https://github.com/Klaasawastaken/BloonsPlus/releases/download/'+tag+'/BloonsPlusSetup.exe') {
 return {tag_name:tag,published_at:date,prerelease:true,assets:[{name:'BloonsPlusSetup.exe',browser_download_url:url,size:1048576}]};
}
(async()=>{
 const older=release('old','2026-10-01T00:00:00Z'), newer=release('new','2026-10-05T00:00:00Z');
 let s=await scenario([older,{...newer,draft:true},{...newer,tag_name:'no-assets',assets:[]},newer],older);
 assert.match(s.nodes['installer-download'].href,/\/new\//);assert.equal(s.calls.length,1);
 s=await scenario([release('unsafe','2026-10-06T00:00:00Z','https://example.org/setup.exe'),older],newer);
 assert.match(s.nodes['installer-download'].href,/\/old\//);
 s=await scenario([],older,true);assert.match(s.nodes['installer-download'].href,/\/old\//);
 s=await scenario([],{},true);assert.match(s.nodes['release-status'].textContent,/No installer could be confirmed/);
 console.log('Site release lookup: newest preview, drafts, missing assets, URL validation and offline fallback pass');
})().catch(e=>{console.error(e);process.exitCode=1});
