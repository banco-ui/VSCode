// 분할 저장된 파일 복원: node scripts/restore-split.js "<원본경로>"
// <원본경로>.parts/manifest.json 을 읽어 조각을 합쳐 원본 파일을 복원한다.
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const target = process.argv[2];
if (!target) { console.error('usage: node scripts/restore-split.js "<원본경로>"'); process.exit(1); }
const ROOT = path.resolve(__dirname, '..');
const dir = path.join(ROOT, target + '.parts');
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
const chunks = manifest.parts.map(name => fs.readFileSync(path.join(dir, name)));
const content = Buffer.concat(chunks);
const sha256 = crypto.createHash('sha256').update(content).digest('hex');
if (sha256 !== manifest.sha256) {
  console.error('SHA256 MISMATCH! expected=' + manifest.sha256 + ' got=' + sha256);
  process.exit(1);
}
const dest = process.argv[3] || path.join(ROOT, target);
fs.mkdirSync(path.dirname(dest), { recursive: true });
fs.writeFileSync(dest, content);
console.log('restored ' + target + ' (' + content.length + ' bytes, sha256 verified)');
