var selectedDocType = 'word';
var selectedMode = 'fast';
var logDiv = document.getElementById('log');
var filePathInput = document.getElementById('filePath');

console.log('🔍 app.js 로드됨 - DOMContentLoaded 등록');

// Initialize click handlers
document.addEventListener('DOMContentLoaded', function() {
  console.log('🔍 DOMContentLoaded 발생!');
  
  var docCards = document.querySelectorAll('.doc-card');
  console.log('📄 문서 카드 개수:', docCards.length);
  
  docCards.forEach(function(card) {
    console.log('📄 카드 등록:', card.dataset.value);
    card.addEventListener('click', function() {
      console.log('📄 클릭됨:', this.dataset.value);
      selectDocType(this.dataset.value);
    });
  });
  
  var modeCards = document.querySelectorAll('.mode-card');
  console.log('🔧 모드 카드 개수:', modeCards.length);
  
  modeCards.forEach(function(card) {
    console.log('🔧 모드 카드 등록:', card.dataset.value);
    card.addEventListener('click', function() {
      console.log('🔧 모드 클릭됨:', this.dataset.value);
      selectMode(this.dataset.value);
    });
  });
});

function selectDocType(type) {
  console.log('📄 selectDocType 호출:', type);
  selectedDocType = type;
  document.querySelectorAll('.doc-card').forEach(function(card) {
    card.classList.remove('selected');
    if (card.dataset.value === type) card.classList.add('selected');
  });
}

function selectMode(mode) {
  console.log('🔧 selectMode 호출:', mode);
  selectedMode = mode;
  document.querySelectorAll('.mode-card').forEach(function(card) {
    card.classList.remove('selected');
    if (card.dataset.value === mode) card.classList.add('selected');
  });
}

function browseFile() {
  console.log('📁 browseFile 호출됨');
  var extMap = {
    word: 'Word|*.docx;*.doc;*.mht|',
    excel: 'Excel|*.xlsx;*.xls;*.csv|',
    ppt: 'PowerPoint|*.pptx;*.ppt|',
    pdf: 'PDF|*.pdf|',
    all: 'All|*.*'
  };
  var filter = extMap[selectedDocType] + extMap.all;
  console.log('📁 필터:', filter);
  var ps = 'Add-Type -AssemblyName System.Windows.Forms; $ofd = New-Object System.Windows.Forms.OpenFileDialog; $ofd.Filter = "' + filter + '"; $ofd.InitialDirectory = [Environment]::GetFolderPath("Desktop"); if ($ofd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { $ofd.FileName }';
  fetch('/api/browse', { method: 'POST', body: ps })
    .then(function(r) { return r.text(); })
    .then(function(p) { 
      console.log('📁 선택된 파일:', p);
      if (p && p.trim()) {
        filePathInput.value = p.trim();
        log('📁 파일 선택: ' + p.trim(), 'info');
      }
    })
    .catch(function(e) { log('❌ 오류: ' + e.message, 'error'); });
}

function startExtract() {
  var filePath = filePathInput.value.trim();
  if (!filePath) { alert('파일을 선택하세요'); return; }
  log('🚀 시작: ' + selectedDocType + ' / ' + selectedMode, 'info');
  log('   파일: ' + filePath, 'info');
  fetch('/api/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ docType: selectedDocType, mode: selectedMode, filePath: filePath })
  }).then(function(r) {
    var reader = r.body.getReader();
    var decoder = new TextDecoder();
    function read() {
      return reader.read().then(function(res) {
        if (res.done) return;
        var chunk = decoder.decode(res.value, { stream: true });
        chunk.split('\n').filter(function(l) { return l.trim(); }).forEach(function(line) {
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
