/**
 * 한번만 인터넷에 연결해 실행하면 Three.js r149 UMD 파일을 vendor에 저장합니다.
 * 설치한 후에는 index.html을 file:// 방식으로 직접 열어도 Three.js 모드가 됩니다.
 * Windows/macOS: node download-three.cjs
 */
const https = require('node:https');
const fs = require('node:fs');
const path = require('node:path');
const dest = path.join(__dirname, 'vendor', 'three.min.js');
const sources = [
  'https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js',
  'https://unpkg.com/three@0.149.0/build/three.min.js'
];
function get(url, redirects = 0) {
 return new Promise((resolve, reject) => {
  if (redirects > 5) return reject(new Error('Too many redirects'));
  const req = https.get(url, {timeout: 20000}, response => {
   if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
    response.resume();return resolve(get(new URL(response.headers.location, url).toString(), redirects + 1));
   }
   if (response.statusCode !== 200) {response.resume();return reject(new Error(`HTTP ${response.statusCode}`));}
   const buffers=[];
   response.on('data', x => buffers.push(x));
   response.on('end', () => resolve(Buffer.concat(buffers)));
  });
  req.on('timeout', ()=>req.destroy(new Error('Timeout')));
  req.on('error',reject);
 });
}
(async() => {
 for(const url of sources){
  try{
   const data=await get(url);
   const text=data.toString('utf8',0,2500);
   if(data.length < 200000 || !data.toString('utf8').includes('THREE')) throw new Error('Unexpected file format');
   fs.mkdirSync(path.dirname(dest),{recursive:true});
   fs.writeFileSync(dest,data);
   console.log(`저장 완료: ${dest} (${Math.round(data.length/1024)} KB)`);
   console.log('이제 index.html을 더블클릭해도 Three.js 정사영 2D가 동작합니다.');
   return;
  }catch(err){console.warn(`${url} 실패: ${err.message}`);}
 }
 console.error('다운로드에 실패했습니다. Canvas 2D 버전은 여전히 오프라인에서 실행됩니다.');
 process.exitCode=1;
})();
