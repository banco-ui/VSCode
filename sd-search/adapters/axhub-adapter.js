/**
 * AX HUB Adapter
 * Playwright CDP를 통한 AX HUB 검색 어댑터 (SSO 세션 활용)
 */
const { chromium } = require('playwright');

class AxhubAdapter {
    constructor(config) {
        this.config = config;
        this.baseUrl = config.baseUrl;
        this.cdpPort = config.cdpPort || 9222;
        this.boards = config.searchBoards || [];
        this.browser = null;
    }

    async connect() {
        if (this.browser) return this.browser;
        
        try {
            console.log('[axhub] CDP 연결 시도...');
            this.browser = await chromium.connectOverCDP(`http://127.0.0.1:${this.cdpPort}`);
            console.log('[axhub] CDP 연결 성공');
        } catch (e) {
            console.log('[axhub] CDP 연결 실패:', e.message);
            this.browser = null;
        }
        
        return this.browser;
    }

    async search(keyword, maxResults = 20, options = {}) {
        const cacheOnly = typeof options === 'object' ? options.cacheOnly : options;
        
        console.log(`[axhub] 검색: "${keyword}" (cacheOnly: ${cacheOnly})`);
        
        const browser = await this.connect();
        if (!browser) {
            console.log('[axhub] CDP 연결 불가, 결과 없음');
            return [];
        }

        try {
            const results = [];
            const contexts = browser.contexts();
            
            if (contexts.length === 0) {
                console.log('[axhub] 열린 컨텍스트가 없습니다');
                return [];
            }
            
            const context = contexts[0];
            const pages = context.pages();
            
            // AX HUB 게시판에서 검색 (첫 번째 게시판만 검색 - 통합 검색)
            for (const board of this.boards) {
                const boardResults = await this.searchBoard(context, pages, board, keyword, maxResults);
                results.push(...boardResults);
                
                if (results.length >= maxResults) break;
            }
            
            console.log(`[axhub] ${results.length}개 결과 발견`);
            return results.slice(0, maxResults);
        } catch (error) {
            console.log('[axhub] 검색 오류:', error.message);
            return [];
        }
    }

    /**
     * 특정 게시판에서 검색
     */
    async searchBoard(context, pages, boardId, keyword, maxResults) {
        const results = [];
        
        try {
            const boardUrl = `${this.baseUrl}/AI_Community?ActionView=LIST&BoardId=${boardId}`;
            
            let page = pages.find(p => p.url().includes('axhub'));
            if (!page) {
                page = await context.newPage();
            }
            
            console.log(`[axhub] 게시판 ${boardId} 검색 중...`);
            await page.goto(boardUrl, { waitUntil: 'domcontentloaded', timeout: this.config.timeout });
            await page.waitForTimeout(3000);
            
            // 검색 입력창에 키워드 입력 후 Enter
            const searchInput = await page.$('input[type="search"]');
            if (searchInput) {
                console.log(`[axhub] 검색창 발견, 키워드 입력: "${keyword}"`);
                await searchInput.fill(keyword);
                await searchInput.press('Enter');
                await page.waitForTimeout(3000);
            } else {
                console.log('[axhub] 검색창 없음');
                return results;
            }
            
            // 게시글 목록 파싱 - 검색 후 data-header: 분류, 제목, 등록자, 등록일
            const posts = await page.evaluate(() => {
                const items = [];
                const rows = document.querySelectorAll('tr.table-row');
                
                rows.forEach((row) => {
                    const tds = row.querySelectorAll('td');
                    let title = '', author = '', date = '', category = '';
                    tds.forEach(td => {
                        const header = td.getAttribute('data-header') || '';
                        const text = td.innerText.trim();
                        if (header === '제목') title = text;
                        else if (header === '등록자' || header === '작성자') author = text;
                        else if (header === '등록일' || header === '작성일') date = text;
                        else if (header === '분류') category = text;
                    });
                    
                    if (title && title.length > 0) {
                        items.push({ title, author, date, category, fullText: row.innerText.trim().substring(0, 500) });
                    }
                });
                return items;
            });
            
            // 각 행을 클릭하여 postId 추출 (OutSystems SPA)
            console.log(`[axhub] ${posts.length}건에서 ID 추출 중...`);
            for (let i = 0; i < posts.length; i++) {
                try {
                    const rows = await page.$$('tr.table-row');
                    if (rows[i]) {
                        const urlBefore = page.url();
                        await rows[i].click();
                        await page.waitForTimeout(1500);
                        const urlAfter = page.url();
                        
                        // Id에서 POST로 시작하는 값 추출 (BoardId와 구분)
                        const idMatch = urlAfter.match(/Id=(POST[^&]+)/);
                        if (idMatch) {
                            posts[i].postNo = idMatch[1];
                            const boardMatch = urlAfter.match(/BoardId=([^&]+)/);
                            posts[i].actualBoardId = boardMatch ? boardMatch[1] : boardId;
                        } else {
                            // POST가 아닌 경우 전체 URL에서 Id 파라미터 추출 시도
                            const urlObj = new URL(urlAfter);
                            const idParam = urlObj.searchParams.get('Id');
                            if (idParam && idParam !== posts[i].actualBoardId) {
                                posts[i].postNo = idParam;
                            }
                        }

                        
                        if (urlAfter !== urlBefore) {
                            await page.goBack({ waitUntil: 'domcontentloaded', timeout: 30000 });
                            await page.waitForTimeout(1500);
                        }
                    }
                } catch (e) {
                    console.log(`[axhub] 행 ${i} 클릭 오류: ${e.message}`);
                }
            }
            
            // 결과 생성
            for (const post of posts) {
                const postBoardId = post.actualBoardId || boardId;
                const postUrl = post.postNo 
                    ? `${this.baseUrl}/AI_Community?ActionView=LIST&BoardId=${postBoardId}&Id=${post.postNo}`
                    : `${this.baseUrl}/AI_Community?ActionView=LIST&BoardId=${boardId}`;
                results.push({
                    platform: 'axhub',
                    id: post.postNo || `axhub-${results.length}`,
                    title: post.title,
                    content: post.fullText,
                    url: postUrl,
                    author: post.author,
                    date: post.date,
                    score: 0.7,
                    keyword: keyword,
                    board: postBoardId,
                    source: 'cdp'
                });
            }
            
            console.log(`[axhub] 게시판 ${boardId}: ${posts.length}건 추출 완료`);
        } catch (error) {
            console.log(`[axhub] 게시판 ${boardId} 검색 오류:`, error.message);
        }
        
        return results;
    }

    async getDetail(postId, boardId) {
        const browser = await this.connect();
        if (!browser) return null;
        
        try {
            const contexts = browser.contexts();
            const pages = contexts[0]?.pages() || [];
            let page = pages.find(p => p.url().includes('axhub')) || pages[0];
            
            if (!page) return null;
            
            const detailUrl = `${this.baseUrl}/AI_Community?ActionView=LIST&BoardId=${boardId}&Id=${postId}`;
            await page.goto(detailUrl, { waitUntil: 'domcontentloaded', timeout: this.config.timeout });
            await page.waitForTimeout(5000);
            
            const bodyText = await page.evaluate(() => document.body.innerText.trim());
            return { id: postId, board: boardId, content: bodyText, url: detailUrl };
        } catch (error) {
            console.log('[axhub] 상세 조회 오류:', error.message);
            return null;
        }
    }

    async close() {
        // CDP 연결은 닫지 않음 (Chrome 유지)
    }
}

module.exports = AxhubAdapter;
