/**
 * axhub Adapter
 * Playwright CDP를 통한 axhub 검색 어댑터 (SSO 세션 활용)
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

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
            console.log('[axhub] CDP 연결 실패, 캐시 모드로 전환');
            this.browser = null;
        }
        
        return this.browser;
    }

    async search(keyword, maxResults = 20) {
        console.log(`[axhub] 검색: "${keyword}"`);
        
        const browser = await this.connect();
        if (!browser) {
            return this.searchFromCache(keyword);
        }
        
        try {
            const results = [];
            const contexts = browser.contexts();
            
            if (contexts.length === 0) {
                console.log('[axhub] 열린 페이지가 없습니다');
                return this.searchFromCache(keyword);
            }
            
            const pages = contexts[0].pages();
            
            // axhub 게시판 목록 페이지에서 검색
            for (const board of this.boards) {
                const boardResults = await this.searchBoard(pages, board, keyword, maxResults);
                results.push(...boardResults);
                
                if (results.length >= maxResults) break;
            }
            
            console.log(`[axhub] ${results.length}개 결과 발견`);
            return results.slice(0, maxResults);
        } catch (error) {
            console.error('[axhub] 검색 오류:', error.message);
            return this.searchFromCache(keyword);
        }
    }

    /**
     * 특정 게시판에서 검색
     */
    async searchBoard(pages, boardId, keyword, maxResults) {
        const results = [];
        
        try {
            // axhub 검색 URL 구성
            const searchUrl = `${this.baseUrl}/AI_Community?ActionView=LIST&BoardId=${boardId}&SearchKeyword=${encodeURIComponent(keyword)}`;
            
            // 기존 페이지 재사용 또는 새 페이지 생성
            let page = pages.find(p => p.url().includes('axhub'));
            if (!page) {
                page = await contexts[0].newPage();
            }
            
            console.log(`[axhub] 게시판 ${boardId} 검색 중...`);
            await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: this.config.timeout });
            await page.waitForTimeout(3000); // SPA 렌더링 대기
            
            // 게시글 목록 파싱
            const posts = await page.evaluate((kw) => {
                const items = [];
                const rows = document.querySelectorAll('tr, .board-list-item, .post-item, [class*="item"]');
                
                rows.forEach((row, idx) => {
                    const text = row.innerText || '';
                    if (text.toLowerCase().includes(kw.toLowerCase()) && text.trim().length > 10) {
                        const link = row.querySelector('a');
                        items.push({
                            title: text.split('\n')[0].trim().substring(0, 200),
                            content: text.trim().substring(0, 500),
                            url: link ? link.href : '',
                            id: link ? link.href.match(/Id=([^&]+)/)?.[1] || `post-${idx}` : `post-${idx}`
                        });
                    }
                });
                
                return items;
            }, keyword);
            
            for (const post of posts) {
                results.push({
                    platform: 'axhub',
                    id: post.id,
                    title: post.title,
                    content: post.content,
                    url: post.url || searchUrl,
                    author: '',
                    date: '',
                    score: 0.7,
                    keyword: keyword,
                    board: boardId
                });
            }
        } catch (error) {
            console.error(`[axhub] 게시판 ${boardId} 검색 오류:`, error.message);
        }
        
        return results;
    }

    /**
     * 특정 게시글 상세 읽기
     */
    async getDetail(postId, boardId) {
        const browser = await this.connect();
        if (!browser) return null;
        
        try {
            const contexts = browser.contexts();
            const pages = contexts[0]?.pages() || [];
            let page = pages.find(p => p.url().includes('axhub')) || pages[0];
            
            if (!page) return null;
            
            const detailUrl = `${this.baseUrl}/AI_Community?ActionView=DETAIL&BoardId=${boardId}&Id=${postId}`;
            await page.goto(detailUrl, { waitUntil: 'domcontentloaded', timeout: this.config.timeout });
            await page.waitForTimeout(5000);
            
            const bodyText = await page.evaluate(() => document.body.innerText.trim());
            return { id: postId, board: boardId, content: bodyText, url: detailUrl };
        } catch (error) {
            console.error('[axhub] 상세 조회 오류:', error.message);
            return null;
        }
    }

    /**
     * 캐시에서 검색 (기존 output 파일)
     */
    async searchFromCache(keyword) {
        console.log('[axhub] 캐시에서 검색 중...');
        const results = [];
        const cacheDir = path.resolve(__dirname, '../output');
        
        try {
            const files = fs.readdirSync(cacheDir).filter(f => f.startsWith('axhub-'));
            
            for (const file of files) {
                const filePath = path.join(cacheDir, file);
                const stat = fs.statSync(filePath);
                
                if (stat.isFile()) {
                    const text = fs.readFileSync(filePath, 'utf8').toLowerCase();
                    
                    if (text.includes(keyword.toLowerCase())) {
                        // 텍스트에서 제목 추출 시도
                        const lines = text.split('\n').filter(l => l.trim());
                        const titleLine = lines.find(l => 
                            !l.includes('Home') && !l.includes('AI ') && l.trim().length > 5
                        ) || file;
                        
                        results.push({
                            platform: 'axhub',
                            id: file,
                            title: titleLine.substring(0, 200),
                            content: text.substring(0, 500),
                            url: `${this.baseUrl}`,
                            author: '',
                            date: stat.mtime.toISOString(),
                            score: 0.5,
                            keyword: keyword,
                            source: 'cache'
                        });
                    }
                }
            }
        } catch (e) {
            // 디렉토리 없음
        }
        
        console.log(`[axhub] 캐시에서 ${results.length}개 결과 발견`);
        return results;
    }

    async close() {
        // CDP 연결은 닫지 않음 (Chrome 유지)
    }
}

module.exports = AxhubAdapter;
