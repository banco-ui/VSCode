// 분할 백업된 대형 파일들을 조각에서 일괄 복원
// 사용법: node scripts/restore-all.js
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const paths = fs.readFileSync(path.join(ROOT, '.git', 'ignore-additions.txt'), 'utf8')
  .split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'));
let ok = 0, fail = 0;
for (const p of paths) {
  try {
    execFileSync('node', [path.join(__dirname, 'restore-split.js'), p], { cwd: ROOT, stdio: ['ignore', 'pipe', 'inherit'] });
    ok++;
  } catch (e) {
    fail++;
    console.log('FAIL ' + p);
  }
}
console.log('RESTORED=' + ok + ' FAILED=' + fail);
