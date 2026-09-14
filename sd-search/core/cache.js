/**
 * 검색 결과 캐시 모듈
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class Cache {
    constructor(config) {
        this.enabled = config.enabled !== false;
        this.ttl = (config.ttlSeconds || 300) * 1000;
        this.cacheDir = path.resolve(__dirname, '../..', config.cacheDir || 'output/search-cache');
        
        if (this.enabled) {
            fs.mkdirSync(this.cacheDir, { recursive: true });
        }
    }

    get(key) {
        if (!this.enabled) return null;
        
        const hash = this.hashKey(key);
        const filePath = path.join(this.cacheDir, `${hash}.json`);
        
        try {
            if (!fs.existsSync(filePath)) return null;
            
            const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
            const age = Date.now() - data.timestamp;
            
            if (age > this.ttl) {
                fs.unlinkSync(filePath);
                return null;
            }
            
            return data.results;
        } catch (e) {
            return null;
        }
    }

    set(key, results) {
        if (!this.enabled) return;
        
        const hash = this.hashKey(key);
        const filePath = path.join(this.cacheDir, `${hash}.json`);
        
        try {
            fs.writeFileSync(filePath, JSON.stringify({
                key: key,
                timestamp: Date.now(),
                results: results
            }, null, 2));
        } catch (e) {
            // 캐시 저장 실패는 무시
        }
    }

    clear() {
        if (!this.enabled || !fs.existsSync(this.cacheDir)) return;
        
        const files = fs.readdirSync(this.cacheDir);
        for (const file of files) {
            if (file.endsWith('.json')) {
                fs.unlinkSync(path.join(this.cacheDir, file));
            }
        }
        console.log(`🗑️  캐시 삭제: ${files.length}개 파일`);
    }

    hashKey(key) {
        return crypto.createHash('md5').update(key).digest('hex');
    }
}

module.exports = Cache;
