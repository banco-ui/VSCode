const http = require('http');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const PORT = 3456;
const OUTPUT_DIR = path.join(__dirname, 'output');

if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const server = http.createServer((req, res) => {
  if (req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    fs.readFile(path.join(__dirname, 'public', 'index.html'), 'utf8', (e, html) => {
      res.end(html || '');
    });
  } else if (req.url === '/public/app.js' || req.url.startsWith('/app.js')) {
    res.writeHead(200, { 'Content-Type': 'application/javascript' });
    fs.readFile(path.join(__dirname, 'public', 'app.js'), 'utf8', (e, js) => {
      res.end(js || '');
    });
  } else if (req.url === '/api/extract' && req.method === 'POST') {
    let body = '';
    req.on('data', c => { body += c; });
    req.on('end', () => {
      try {
        const { docType, mode, filePath } = JSON.parse(body);
        handleExtract(docType, mode, filePath, res);
      } catch (e) { res.writeHead(400); res.end('Invalid JSON'); }
    });
  } else if (req.url === '/api/browse' && req.method === 'POST') {
    let ps = '';
    req.on('data', c => { ps += c; });
    req.on('end', () => {
      exec('powershell -ExecutionPolicy Bypass -Command "' + ps + '"', { encoding: 'utf8' }, (err, stdout) => {
        res.writeHead(err ? 500 : 200);
        res.end(err ? err.message : stdout.trim());
      });
    });
  } else if (req.url === '/api/open-folder') {
    exec('explorer "' + OUTPUT_DIR + '"');
    res.writeHead(200); res.end('OK');
  } else { res.writeHead(404); res.end('Not Found'); }
});

function handleExtract(docType, mode, filePath, res) {
  const script = 'drm-ungroup.js';
  const scriptPath = path.join(__dirname, 'scripts', script);
  if (!fs.existsSync(scriptPath)) { res.writeHead(404); res.end('Not found: ' + script); return; }
  const cmd = 'node "' + scriptPath + '" "' + filePath + '" ' + docType + ' ' + mode;
  console.log('실행: ' + cmd);
  const proc = exec(cmd, { encoding: 'utf8' });
  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.write(JSON.stringify({ status: 'started' }) + '\n');
  proc.stdout.on('data', d => { console.log(d); res.write(JSON.stringify({ type: 'output', data: d }) + '\n'); });
  proc.stderr.on('data', d => { console.error(d); res.write(JSON.stringify({ type: 'error', data: d }) + '\n'); });
  proc.on('close', code => { res.write(JSON.stringify({ status: code === 0 ? 'completed' : 'failed', code }) + '\n'); res.end(); });
}

server.listen(PORT, () => {
  console.log('\n' + '='.repeat(60) + '\n  🔓 DRM 문서 풀기 GUI 서버 시작됨\n  👉 http://localhost:' + PORT + '\n  (Ctrl+C 로 종료)\n' + '='.repeat(60) + '\n');
});