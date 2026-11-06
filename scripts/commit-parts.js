// 분할 조각 파일들을 배치 커밋으로 추가 (트리 크기 제한 대응)
// - .gitignore 에 원본 대형 경로 추가 (원본은 로컬 전용)
// - 조각/manifest 파일을 200개씩 나누어 커밋
// 로그: .git/commit-parts.log
// 사용법: node scripts/commit-parts.js
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const LOG = path.join(ROOT, '.git', 'commit-parts.log');
function log(msg) { fs.appendFileSync(LOG, new Date().toISOString().slice(11, 19) + ' ' + msg + '\n'); }
function git(args, input) {
  return execFileSync('git', args, { maxBuffer: 256 * 1024 * 1024, cwd: ROOT, encoding: 'utf8', input });
}

try {
  log('START commit-parts');
  const plan = JSON.parse(fs.readFileSync(path.join(ROOT, '.git', 'split-plan.json'), 'utf8'));

  // 1) .gitignore 갱신 (중복 제거)
  const giPath = path.join(ROOT, '.gitignore');
  const gi = fs.readFileSync(giPath, 'utf8');
  const additions = fs.readFileSync(path.join(ROOT, '.git', 'ignore-additions.txt'), 'utf8')
    .split('\n').map(l => l.trim()).filter(Boolean);
  const existing = new Set(gi.split('\n').map(l => l.trim()));
  const toAdd = additions.filter(l => !l.startsWith('#') && !existing.has(l));
  if (toAdd.length) {
    fs.appendFileSync(giPath, '\n# 대형 파일(분할 백업됨 - 원본은 로컬 전용)\n' + toAdd.join('\n') + '\n');
  }
  log('gitignore additions: ' + toAdd.length);

  // 2) 커밋할 파일 목록 수집
  let files = [];
  for (const f of plan.files) {
    const dir = path.join(ROOT, f.partsDir);
    for (const name of fs.readdirSync(dir)) files.push(f.partsDir + '/' + name);
  }
  files.sort();
  log('files to commit: ' + files.length);

  // 3) 배치 커밋 (200개씩)
  const PER = 200;
  let batch = 1;
  for (let i = 0; i < files.length; i += PER) {
    const chunk = files.slice(i, i + PER);
    git(['add', '--', ...chunk]);
    git(['commit', '--quiet', '-m', 'Backup: 대형 파일 분할 저장 (' + batch + '/' + Math.ceil(files.length / PER) + ' 배치, ' + chunk.length + ' files)\n\nCo-Authored-By: Cline SR']);
    log('COMMIT batch ' + batch + ' (' + chunk.length + ' files)');
    batch++;
  }
  log('DONE');
} catch (e) {
  log('ERROR ' + (e.message || e));
  process.exit(1);
}
