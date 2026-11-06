// 중간 버전 대형 blob 정리: 한 번이라도 >17KB blob 이 있었던 경로를
// filter-repo 제거 목록에 추가한다 (parts 디렉터리 제외)
// 출력: .git/ever-big-paths.txt (신규 추가 경로만), .git/fix-restore.txt (재추가할 소형 최신판 경로)
// 사용법: node scripts/fix-big-history.js
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '..');
const GIT = (args, input) => execFileSync('git', args, { maxBuffer: 256 * 1024 * 1024, cwd: ROOT, encoding: 'utf8', input });
const THRESH = 17 * 1024;

// 1) 범위 내 모든 blob 과 경로/크기
const objs = GIT(['rev-list', '--objects', 'upstream/main..main']).split('\n').filter(Boolean);
const batch = GIT(['cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)'], objs.join('\n') + '\n');
const sizes = {};
for (const line of batch.split('\n')) {
  const p = line.split(' ');
  if (p[1] === 'blob') sizes[p[0]] = +p[2];
}
// 2) blob -> 경로 (parts 제외)
const everBig = new Set();
for (const line of objs) {
  const sp = line.indexOf(' ');
  if (sp < 0) continue;
  const sha = line.slice(0, sp), fpath = line.slice(sp + 1);
  if (fpath.includes('.parts/')) continue;
  if (sizes[sha] > THRESH) everBig.add(fpath);
}
// 3) 기존 제거 목록과 비교
const old = new Set(fs.readFileSync(path.join(ROOT, '.git', 'filter-repo-paths.txt'), 'utf8')
  .split('\n').map(l => l.trim()).filter(Boolean));
const ignoreList = new Set(fs.readFileSync(path.join(ROOT, '.git', 'ignore-additions.txt'), 'utf8')
  .split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#')));
const newPaths = [...everBig].filter(p => !old.has(p)).sort();
const restore = [...everBig].filter(p => !ignoreList.has(p)).sort();
fs.writeFileSync(path.join(ROOT, '.git', 'filter-repo-paths.txt'),
  [...old, ...newPaths].join('\n'));
fs.writeFileSync(path.join(ROOT, '.git', 'fix-restore.txt'), restore.join('\n'));
console.log('ever-big:', everBig.size, 'new:', newPaths.length, 'restore-latest:', restore.length);
console.log(newPaths.slice(0, 20).join('\n'));
