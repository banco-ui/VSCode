/**
 * 통합 검색 엔진 (Unified Searcher)
 * Mosaic, Confluence, axhub 3개 플랫폼 통합 검색
 */
const MosaicAdapter = require('../adapters/mosaic-adapter');
const ConfluenceAdapter = require('../adapters/confluence-adapter');
const AxhubAdapter = require('../adapters/axhub-adapter');
const Cache = require('./cache');
const Formatter = require('./formatter');

class Searcher {
    constructor(config) {
        this.config = config;
        this.adapters = {};
        this.cache = new Cache(config.cache);
        this.formatter = new Formatter();
        
        // 어댑터 초기화
        this.adapters.mosaic = new MosaicAdapter(config.mosaic);
        this.adapters.confluence = new ConfluenceAdapter(config.confluence);
        this.adapters.axhub = new AxhubAdapter(config.axhub);
    }

    /**
     * 통합 검색 실행
     */
    async search(keyword, options = {}) {
        const platforms = options.platforms || this.config.defaults.platforms;
        const maxResults = options.maxResults || this.config.defaults.maxResults;
        const outputFormat = options.format || this.config.defaults.outputFormat;
        
        console.log(`\n🔍 통합 검색: "${keyword}"`);
        console.log(`   플랫폼: ${platforms.join(', ')}`);
        console.log(`   최대 결과: ${maxResults}개\n`);
        
        // 캐시 확인
        const cacheKey = `search:${keyword}:${platforms.join(',')}:${maxResults}`;
        const cached = this.cache.get(cacheKey);
        if (cached) {
            console.log('📦 캐시에서 로드됨\n');
            return this.formatter.format(cached, outputFormat);
        }
        
        // 각 플랫폼별 병렬 검색
        const searchPromises = platforms.map(platform => {
            const adapter = this.adapters[platform];
            if (!adapter) {
                console.warn(`⚠️  알 수 없는 플랫폼: ${platform}`);
                return Promise.resolve([]);
            }
            return adapter.search(keyword, maxResults).catch(err => {
                console.error(`❌ [${platform}] 오류:`, err.message);
                return [];
            });
        });
        
        const searchResults = await Promise.all(searchPromises);
        
        // 결과 통합
        let allResults = [];
        searchResults.forEach((results, idx) => {
            const platform = platforms[idx];
            results.forEach(r => {
                r.platform = platform;
                allResults.push(r);
            });
        });
        
        // 랭킹/정렬
        allResults = this.rankResults(allResults, keyword);
        
        // 최대 결과 수 제한
        allResults = allResults.slice(0, maxResults);
        
        // 캐시 저장
        this.cache.set(cacheKey, allResults);
        
        // 결과 출력
        return this.formatter.format(allResults, outputFormat);
    }

    /**
     * 검색 결과 랭킹/정렬
     */
    rankResults(results, keyword) {
        const kw = keyword.toLowerCase();
        
        return results.map(r => {
            let score = r.score || 0;
            
            // 제목 매칭 가중치
            if (r.title && r.title.toLowerCase().includes(kw)) {
                score += 1.0;
            }
            
            // 내용 매칭 가중치
            if (r.content && r.content.toLowerCase().includes(kw)) {
                score += 0.5;
            }
            
            // 캐시가 아닌 실시간 결과 가중치
            if (r.source !== 'cache') {
                score += 0.3;
            }
            
            r.score = score;
            return r;
        }).sort((a, b) => b.score - a.score);
    }

    /**
     * 상세 내용 조회
     */
    async getDetail(platform, id, options = {}) {
        const adapter = this.adapters[platform];
        if (!adapter) {
            throw new Error(`알 수 없는 플랫폼: ${platform}`);
        }
        
        let result;
        if (platform === 'axhub') {
            const boardId = options.board || this.config.axhub.searchBoards[0];
            result = await adapter.getDetail(id, boardId);
        } else {
            result = await adapter.getDetail(id);
        }
        
        return result;
    }

    /**
     * 플랫폼별 통계
     */
    getStats(results) {
        const stats = {};
        for (const r of results) {
            stats[r.platform] = (stats[r.platform] || 0) + 1;
        }
        return stats;
    }
}

module.exports = Searcher;
