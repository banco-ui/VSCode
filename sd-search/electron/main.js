const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

let mainWindow = null;
let serverStarted = false;

// Express 서버를 직접 require하여 실행 (asar 호환)
function startServer() {
    try {
        const serverPath = path.join(__dirname, '..', 'gui', 'server.js');
        require(serverPath);
        serverStarted = true;
        console.log('[SDSearch] Express server started');
    } catch (err) {
        console.error('[SDSearch] Failed to start server:', err);
    }
}

// Express 서버가 시작될 때까지 재시도하며 대기
function waitForServerAndLoad() {
    const maxRetries = 10;
    let retryCount = 0;
    
    function tryLoad() {
        const http = require('http');
        const req = http.get('http://localhost:3120', (res) => {
            if (res.statusCode === 200 || res.statusCode === 302 || res.statusCode === 304) {
                mainWindow.loadURL('http://localhost:3120');
            } else {
                retry();
            }
            res.destroy();
        });
        
        req.on('error', () => {
            retry();
        });
        
        req.setTimeout(2000, () => {
            req.destroy();
            retry();
        });
    }
    
    function retry() {
        retryCount++;
        if (retryCount < maxRetries) {
            setTimeout(tryLoad, 500);
        } else {
            // 최후의 수단: 바로 로드 시도
            mainWindow.loadURL('http://localhost:3120');
        }
    }
    
    tryLoad();
}

// Electron 창 생성
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        title: 'SDSearch - Samsung Doc Search',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // Express 서버가 시작될 때까지 대기 후 로드
    waitForServerAndLoad();

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // 메뉴 단순화
    Menu.setApplicationMenu(Menu.buildFromTemplate([
        {
            label: 'File',
            submenu: [
                { role: 'reload', label: 'Reload' },
                { type: 'separator' },
                { role: 'quit', label: 'Quit' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'zoomIn', label: 'Zoom In' },
                { role: 'zoomOut', label: 'Zoom Out' },
                { role: 'resetZoom', label: 'Reset Zoom' },
                { type: 'separator' },
                { role: 'togglefullscreen', label: 'Fullscreen' }
            ]
        }
    ]));
}

// App lifecycle
app.whenReady().then(() => {
    startServer();
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    app.quit();
});
