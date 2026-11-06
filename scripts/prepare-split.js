// 대형 파일 분할 준비: 17KB 초과 blob의 최신 버전을 25KB 조각으로 분할
// - 조각: <원본경로>.parts/part-00001 ... + manifest.json (복원 정보)
// - 출력: .git/filter-repo-paths.txt (히스토리 제거 대상 경로)
//         .git/ignore-additions.txt (.gitignore 추가 항목)
//         .git/split-plan.json (배치 커밋용 파일 목록)
// 사용법: node scripts/prepare-split.js
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.resolve(__dirname, '..');
const GIT = (args, input) => execFileSync('git', args, { maxBuffer: 256 * 1024 * 1024, cwd: ROOT, encoding: 'utf8', input });
const GITBUF = (args) => execFileSync('git', args, { maxBuffer: 256 * 1024 * 1024, cwd: ROOT });
const PART_SIZE = 25000;          // 조각 크기 (25KB - 프록시 본문 한계 32KB 이내 확인됨)
const BIG_THRESHOLD = 17 * 1024;  // 이보다 큰 blob 은 분할 대상
const JUNK = /(^|\/)(__pycache__\/|[^\/]*\.pyc$)/;   // 정크(파이썬 캐시)는 백업하지 않음

function main() {
  // 1) 미푸시 범위의 고유 blob 목록 (size 포함) - 2회 호출
  const objs = GIT(['rev-list', '--objects', 'upstream/main..main']).split('\n').filter(Boolean);
  const sizeOf = {};
  const batch = GIT(['cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)'],
    objs.join('\n') + '\n');
  for (const line of batch.split('\n')) {
    const p = line.split(' ');
    if (p.length >= 4 && p[1] === 'blob') sizeOf[p[0]] = { size: +p[2], path: p.slice(3).join(' ') };
  }
  console.log('unique objects:', Object.keys(sizeOf).length);

  // 2) 전체 변경 이력을 1회 호출로 수집 (최신 커밋이 먼저 옴)
  const raw = GITBUF(['log', '--format=%x01%H', '--raw', '--no-abbrev', '--no-renames', '-z', '--root',
    'upstream/main..main']).toString();
  const segments = raw.split('\u0001').filter(s => s.trim());
  const latest = {};   // path -> blobSha (최신 버전)
  for (const seg of segments) {
    const nl = seg.indexOf('\0');
    if (nl < 0) continue;
    const tokens = seg.slice(nl + 1).split('\0');
    for (let i = 0; i < tokens.length - 1; i++) {
      const tok = tokens[i];
      if (!tok.startsWith(':')) continue;
      const fpath = tokens[++i];
      const parts = tok.split(' ');
      const newSha = parts[3];
      if (newSha === '0000000000000000000000000000000000000000') continue;
      if (!latest[fpath]) latest[fpath] = newSha;
    }
  }
  console.log('paths touched:', Object.keys(latest).length);

  // 3) 대형 경로 선정 (최신 blob 이 threshold 초과, 정크 제외)
  const bigPaths = [];
  for (const [fpath, blobSha] of Object.entries(latest)) {
    if (JUNK.test(fpath)) continue;
    const info = sizeOf[blobSha];
    const size = info ? info.size : +GIT(['cat-file', '-s', blobSha]);
    if (size > BIG_THRESHOLD) bigPaths.push({ path: fpath, blobSha, size });
  }
  bigPaths.sort((a, b) => a.path.localeCompare(b.path));
  console.log('big paths:', bigPaths.length);
  if (bigPaths.length === 0) {
    console.log('NOTHING_TO_SPLIT');
    fs.writeFileSync(path.join(ROOT, '.git', 'filter-repo-paths.txt'), '');
    return;
  }

  // 4) 조각 생성
  const plan = { partSize: PART_SIZE, files: [] };
  let totalParts = 0;
  for (const { path: fpath, blobSha, size } of bigPaths) {
    const content = GITBUF(['cat-file', 'blob', blobSha]);
    const sha256 = crypto.createHash('sha256').update(content).digest('hex');
    const dir = fpath + '.parts';
    fs.mkdirSync(dir, { recursive: true });
    const names = [];
    for (let off = 0, idx = 1; off < content.length; off += PART_SIZE, idx++) {
      const name = 'part-' + String(idx).padStart(5, '0');
      fs.writeFileSync(path.join(ROOT, dir, name), content.subarray(off, off + PART_SIZE));
      names.push(name);
      totalParts++;
    }
    const manifest = {
      originalPath: fpath,
      originalSize: content.length,
      sha256,
      partSize: PART_SIZE,
      partCount: names.length,
      parts: names,
      restore: 'node scripts/restore-split.js "' + fpath + '"'
    };
    fs.writeFileSync(path.join(ROOT, dir, 'manifest.json'), JSON.stringify(manifest, null, 2));
    plan.files.push({ path: fpath, partsDir: dir, size, parts: names.length });
    console.log('split ' + fpath + ' -> ' + names.length + ' parts (' + Math.round(size / 1024) + 'KB)');
  }
  console.log('total parts:', totalParts);

  // 5) filter-repo 경로 목록 (UTF-8 BOM 없음)
  fs.writeFileSync(path.join(ROOT, '.git', 'filter-repo-paths.txt'), bigPaths.map(x => x.path).join('\n'));
  // 6) gitignore 추가 항목
  fs.writeFileSync(path.join(ROOT, '.git', 'ignore-additions.txt'),
    '# 대형 파일(분할 백업됨 - 원본은 로컬 전용)\n' + bigPaths.map(x => x.path).join('\n') + '\n');
  // 7) 배치 커밋 계획 (트리 크기 제한: 커밋당 최대 120 파일)
  const batches = [];
  const PER = 120;
  for (let i = 0; i < plan.files.length; i += PER) {
    batches.push(plan.files.slice(i, i + PER).map(f => f.partsDir));
  }
  plan.batches = batches;
  fs.writeFileSync(path.join(ROOT, '.git', 'split-plan.json'), JSON.stringify(plan, null, 2));
  console.log('batches:', batches.length);
}
main();
