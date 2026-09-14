const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const { fork } = require('child_process');

let mainWindow = null;
let serverProcess = null;

// Express 서버를 자식 프로세스로 실행
function startServer() {
    const serverPath = path.join(__dirname, 'gui', 'server.js');
    serverProcess = fork(serverPath, [], {
        env: {
            ...process.env,
            ELECTRON_RUN_AS_NODE: '1'
        },
        stdio: 'pipe'
    });

    serverProcess.stdout.on('data', (data) => {
        console.log(`[server] ${data.toString().trim()}`);
    });

    serverProcess.stderr.on('data', (data) => {
        console.error(`[server:err] ${data.toString().trim()}`);
    });

    serverProcess.on('exit', (code) => {
        console.log(`Server process exited with code ${code}`);
    });
}

// Electron 창 생성
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 900,
        minHeight: 600,
        title: 'SDSearch - Samsung Doc Search',
        icon: path.join(__dirname, 'build', 'icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // Express 서버가 시작될 때까지 대기 후 로드
    setTimeout(() => {
        mainWindow.loadURL('http://localhost:3120');
        
        // 개발 도구는 프로덕션에서 닫기
        // mainWindow.webContents.openDevTools();
    }, 2000);

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
    if (serverProcess) {
        serverProcess.kill();
    }
    app.quit();
});

app.on('before-quit', () => {
    if (serverProcess) {
        serverProcess.kill();
    }
});
