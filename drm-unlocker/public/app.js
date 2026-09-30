var docTypeSel = document.getElementById('docType');
var modeGroup = document.getElementById('modeGroup');
var logDiv = document.getElementById('log');
var filePathInput = document.getElementById('filePath');

docTypeSel.onchange = function() {
  modeGroup.style.display = this.value === 'word' ? 'block' : 'none';
};

function browseFile() {
  var ps = 'Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.Interaction]::AppActivate("Visual Studio Code"); Add-Type -AssemblyName System.Windows.Forms; $ofd = New-Object System.Windows.Forms.OpenFileDialog; $ofd.Filter = "Word|*.docx|PDF|*.pdf|모두|*.*"; if ($ofd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { [Console]::WriteLine($ofd.FileName) }';
  fetch('/api/browse', { method: 'POST', body: ps })
    .then(function(r) { return r.text(); })
    .then(function(p) { if (p && p.trim()) filePathInput.value = p.trim(); })
    .catch(function(e) { log('❌ 오류: ' + e.message, 'error'); });
}

function startExtract() {
  var docType = docTypeSel.value;
  var mode = document.querySelector('input[name="mode"]:checked');
  var selectedMode = mode ? mode.value : 'text-capture';
  var filePath = filePathInput.value.trim();
  if (!filePath) { alert('파일을 선택하세요'); return; }
  log('🚀 시작: ' + docType + ' / ' + selectedMode + '\\n   파일: ' + filePath + '\\n', 'info');
  fetch('/api/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ docType: docType, mode: selectedMode, filePath: filePath })
  }).then(function(r) {
    var reader = r.body.getReader();
    var decoder = new TextDecoder();
    function read() {
      return reader.read().then(function(res) {
        if (res.done) return;
        var chunk = decoder.decode(res.value, { stream: true });
        chunk.split('\\n').filter(function(l) { return l.trim(); }).forEach(function(line) {
          try {
            var msg = JSON.parse(line);
            if (msg.type === 'output') log(msg.data, 'info');
            else if (msg.type === 'error') log(msg.data, 'error');
            else if (msg.status === 'completed') log('✅ 완료!', 'success');
            else if (msg.status === 'failed') log('❌ 실패 (코드: ' + msg.code + ')', 'error');
          } catch(e) {}
        });
        return read();
      });
    }
    return read();
  }).catch(function(e) { log('❌ 오류: ' + e.message, 'error'); });
}

function openFolder() {
  fetch('/api/open-folder').then(function() { log('📁 결과 폴더를 엽니다.', 'info'); });
}

function log(msg, type) {
  var ts = new Date().toLocaleTimeString('ko-KR');
  var pre = type === 'info' ? '[INFO] ' : type === 'success' ? '[OK] ' : '[ERROR] ';
  logDiv.innerHTML += ts + ' ' + pre + msg + '<br>';
  logDiv.scrollTop = logDiv.scrollHeight;
}