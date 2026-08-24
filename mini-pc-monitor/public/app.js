const deviceList = document.querySelector('#deviceList');
const template = document.querySelector('#deviceTemplate');
const editor = document.querySelector('#editor');
const form = editor.querySelector('form');
let rows = []; let editingId = null; const notifiedOffline = new Set();
const formatTime = (value) => value ? new Intl.DateTimeFormat('ko-KR', { dateStyle: 'short', timeStyle: 'medium' }).format(new Date(value)) : '-';
const statusLabel = { online: '정상', offline: '장애', degraded: '재확인 중', checking: '검사 중', disabled: '중지됨' };
async function request(url, options) { const response = await fetch(url, options); if (!response.ok) throw new Error((await response.json().catch(() => ({}))).error || '요청에 실패했습니다.'); return response.json(); }
function render(payload) {
  rows = payload.rows; const online = rows.filter((row) => row.status === 'online').length; const offline = rows.filter((row) => row.status === 'offline').length;
  document.querySelector('#total').textContent = rows.length; document.querySelector('#online').textContent = online; document.querySelector('#offline').textContent = offline; document.querySelector('#checking').textContent = rows.length - online - offline;
  document.querySelector('#meta').textContent = `${payload.checkedIntervalSeconds}초마다 검사 · ${payload.failuresBeforeOffline}회 연속 실패 시 장애`;
  const alert = document.querySelector('#alert'); alert.classList.toggle('hidden', offline === 0); alert.textContent = offline ? `장애 감지: ${rows.filter((row) => row.status === 'offline').map((row) => row.name).join(', ')}` : '';
  deviceList.replaceChildren();
  rows.forEach((row) => { const node = template.content.firstElementChild.cloneNode(true); node.classList.add(row.status); node.querySelector('h3').textContent = row.name; node.querySelector('.ip').textContent = row.ip; node.querySelector('.status').textContent = statusLabel[row.status]; node.querySelector('.details').textContent = row.status === 'online' ? `${row.latency ?? '-'} ms · ${formatTime(row.checkedAt)}` : `마지막 정상: ${formatTime(row.lastOnlineAt)}`; node.querySelector('.edit').onclick = () => openEditor(row); node.querySelector('.delete').onclick = () => removeDevice(row.id); deviceList.append(node); if (row.status === 'offline' && !notifiedOffline.has(row.id) && Notification.permission === 'granted') new Notification('미니PC 장애 감지', { body: `${row.name} (${row.ip})가 응답하지 않습니다.` }); if (row.status === 'offline') notifiedOffline.add(row.id); else notifiedOffline.delete(row.id); });
}
async function refresh() { try { render(await request('/api/status')); } catch (error) { document.querySelector('#meta').textContent = error.message; } }
async function saveDevices(nextRows) { await request('/api/devices', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(nextRows) }); await refresh(); }
function openEditor(row) { editingId = row?.id || null; form.reset(); document.querySelector('#dialogTitle').textContent = row ? '장비 수정' : '장비 추가'; if (row) { form.name.value = row.name; form.ip.value = row.ip; form.enabled.checked = row.enabled; } editor.showModal(); }
async function removeDevice(id) { if (confirm('이 장비를 목록에서 삭제할까요?')) await saveDevices(rows.filter((row) => row.id !== id)); }
form.addEventListener('submit', async (event) => { event.preventDefault(); const item = { id: editingId || `${form.name.value.trim()}-${form.ip.value.trim()}`, name: form.name.value.trim(), ip: form.ip.value.trim(), enabled: form.enabled.checked }; const next = editingId ? rows.map((row) => row.id === editingId ? item : row) : [...rows, item]; try { await saveDevices(next); editor.close(); } catch (error) { alert(error.message); } });
document.querySelector('#addDevice').onclick = () => openEditor();
document.querySelector('#checkNow').onclick = async () => { const button = document.querySelector('#checkNow'); button.disabled = true; button.textContent = '검사 중…'; try { render(await request('/api/check-now', { method: 'POST' })); } finally { button.disabled = false; button.textContent = '지금 검사'; } };
document.querySelector('#notify').onclick = async () => { if (!('Notification' in window)) return alert('이 브라우저는 알림을 지원하지 않습니다.'); const permission = await Notification.requestPermission(); if (permission === 'granted') document.querySelector('#notify').textContent = '브라우저 알림 사용 중'; };
refresh(); setInterval(refresh, 5000);
