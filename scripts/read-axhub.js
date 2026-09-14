const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// output 디렉토리 보장
const outputDir = 'd:/Data/AI/VSCode/output';
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

// 시스템 Chrome 경로 찾기
const chromePaths = [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Users\\banco\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe'
];

let executablePath = null;
for (const p of chromePaths) {
    if (fs.existsSync(p)) {
        executablePath = p;
        break;
    }
}

const url = 'https://axhub.sec.samsung.net/AI_Community?ActionView=DETAIL&BoardId=AICrewActivityBoard&Id=POST00008055';

(async () => {
    // CDP로 이미 실행 중인 Chrome에 연결 시도
    let browser;
    try {
        console.log('Connecting to existing Chrome via CDP...');
        browser = await chromium.connectOverCDP('http://127.0.0.1:9222');
        console.log('Connected to existing Chrome!');
    } catch (e) {
        console.log('CDP connection failed, launching new Chrome with SSO...');
        browser = await chromium.launch({
            headless: false,
            executablePath: executablePath || undefined,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--proxy-server=http://168.219.61.252:8080',
                '--auth-server-whitelist=*sec.samsung.net'
            ]
        });
    }

    // CDP 연결 시 기존 페이지 사용
    let page;
    const contexts = browser.contexts();
    if (contexts.length > 0) {
        const pages = contexts[0].pages();
        // axhub 페이지 찾기
        page = pages.find(p => p.url().includes('axhub')) || pages[0];
        console.log('Using existing page:', page.url());
    }
    
    if (!page) {
        const context = await browser.newContext({
            ignoreHTTPSErrors: true,
            viewport: { width: 1280, height: 900 }
        });
        page = await context.newPage();
    }

    console.log('Current page URL:', page.url());

    try {
        // 이미 axhub 페이지면 읽기, 아니면 이동
        if (!page.url().includes('POST00008055')) {
            console.log('Navigating to:', url);
            await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
        }
        await page.waitForTimeout(5000);


        
        // 페이지 제목 출력
        const title = await page.title();
        console.log('Page title:', title);
        
        // SPA 렌더링 대기
        console.log('Waiting for SPA to render...');
        await page.waitForTimeout(10000);
        
        // body 전체 텍스트 가져오기
        const bodyText = await page.evaluate(() => {
            return document.body.innerText.trim();
        });
        
        console.log('=== FULL PAGE TEXT (first 5000 chars) ===');
        console.log(bodyText.substring(0, 5000));
        console.log('=== TOTAL LENGTH:', bodyText.length, '===');
        
        // HTML 저장
        const html = await page.content();
        require('fs').writeFileSync('d:/Data/AI/VSCode/output/axhub-github-push-article.html', html);
        require('fs').writeFileSync('d:/Data/AI/VSCode/output/axhub-github-push-article.txt', bodyText);
        console.log('=== Saved to output/axhub-github-push-article.txt ===');

        
    } catch (e) {
        console.error('Error:', e.message);
        // 스크린샷 저장
        await page.screenshot({ path: 'd:/Data/AI/VSCode/output/axhub-screenshot.png', fullPage: true });
        console.log('Screenshot saved to output/axhub-screenshot.png');
    }
    
    // 브라우저는 열어둠 (수동 확인용)
    // await browser.close();
})();
