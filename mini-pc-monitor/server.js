'use strict';

const express = require('express');
const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const app = express();
const port = Number(process.env.MONITOR_PORT || 4310);
const intervalMs = Number(process.env.MONITOR_INTERVAL_MS || 30000);
const failuresBeforeOffline = Number(process.env.MONITOR_FAILURES || 3);
const devicesFile = path.join(__dirname, 'devices.json');
app.use(express.json({ limit: '100kb' }));
app.use(express.static(path.join(__dirname, 'public')));
let devices = loadDevices();
const states = new Map();

function normalizeDevice(device) {
  if (!device || typeof device.name !== 'string' || typeof device.ip !== 'string') return null;
  const name = device.name.trim(); const ip = device.ip.trim();
  if (!name || !ip) return null;
  return { id: typeof device.id === 'string' && device.id ? device.id : `${name}-${ip}`, name, ip, enabled: device.enabled !== false };
}
function loadDevices() {
  try { const data = JSON.parse(fs.readFileSync(devicesFile, 'utf8')); return Array.isArray(data) ? data.map(normalizeDevice).filter(Boolean) : []; }
  catch (error) { console.error(`장비 목록을 읽을 수 없습니다: ${error.message}`); return []; }
}
function saveDevices(next) {
  fs.writeFileSync(devicesFile, `${JSON.stringify(next, null, 2)}\n`, 'utf8'); devices = next;
  for (const id of states.keys()) if (!devices.some((device) => device.id === id)) states.delete(id);
}
function ping(ip) {
  return new Promise((resolve) => execFile('ping.exe', ['-n', '1', '-w', '1500', ip], { windowsHide: true, timeout: 3000 }, (error, stdout) => {
    const ok = !error && /TTL=/i.test(stdout);
    const latency = ok ? Number((stdout.match(/(?:time|시간)[=<](\d+)ms/i) || [])[1]) : null;
    resolve({ ok, latency });
  }));
}
async function checkDevice(device) {
  if (!device.enabled) return;
  const previous = states.get(device.id) || { failures: 0, status: 'unknown', events: [] };
  const result = await ping(device.ip); const now = new Date().toISOString();
  const failures = result.ok ? 0 : previous.failures + 1;
  const status = result.ok ? 'online' : (failures >= failuresBeforeOffline ? 'offline' : 'degraded');
  const events = previous.events || [];
  if (previous.status !== status && status !== 'degraded') { events.unshift({ at: now, type: status, message: status === 'offline' ? '장애 감지' : '정상 복구' }); events.splice(30); }
  states.set(device.id, { status, failures, latency: result.latency, checkedAt: now, lastOnlineAt: result.ok ? now : previous.lastOnlineAt || null, events });
}
async function checkAll() { await Promise.all(devices.filter((device) => device.enabled).map(checkDevice)); }
function statusPayload() {
  const rows = devices.map((device) => { const state = states.get(device.id); return { ...device, status: device.enabled ? (state?.status || 'checking') : 'disabled', failures: state?.failures || 0, latency: state?.latency ?? null, checkedAt: state?.checkedAt || null, lastOnlineAt: state?.lastOnlineAt || null, events: state?.events || [] }; });
  return { rows, checkedIntervalSeconds: intervalMs / 1000, failuresBeforeOffline, serverTime: new Date().toISOString() };
}
app.get('/api/status', (req, res) => res.json(statusPayload()));
app.put('/api/devices', (req, res) => {
  if (!Array.isArray(req.body)) return res.status(400).json({ error: '장비 목록은 배열이어야 합니다.' });
  const next = req.body.map(normalizeDevice).filter(Boolean);
  if (next.some((device, index) => next.findIndex((item) => item.id === device.id) !== index)) return res.status(400).json({ error: '장비 ID가 중복되었습니다.' });
  saveDevices(next); checkAll(); res.json({ ok: true, devices });
});
app.post('/api/check-now', async (req, res) => { await checkAll(); res.json(statusPayload()); });
app.listen(port, '127.0.0.1', async () => { console.log(`미니PC 모니터: http://127.0.0.1:${port}`); console.log(`검사 주기: ${intervalMs / 1000}초 / 장애 기준: ${failuresBeforeOffline}회 연속 실패`); await checkAll(); setInterval(checkAll, intervalMs); });
