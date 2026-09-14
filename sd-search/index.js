#!/usr/bin/env node
/**
 * SDSearch - Samsung Doc Search
 * Mosaic, Confluence, axhub 통합 검색 CLI
 * 
 * 사용법:
 *   node index.js search "키워드"
 *   node index.js search "키워드" --platform mosaic,confluence
 *   node index.js search "키워드" --format json
 *   node index.js search "키워드" --max 30
 *   node index.js detail <platform> <id>
 *   node index.js cache clear
 */
const fs = require('fs');
const path = require('path');
const Searcher = require('./core/searcher');
const Cache = require('./core/cache');

// 설정 로드
const configPath = path.resolve(__dirname, 'config/search-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const searcher = new Searcher(config);

// CLI 인자 파싱
const args = process.argv.slice(2);
const command = args[0];

function parseOptions(args) {
    const options = {};
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--platform' && args[i + 1]) {
            options.platforms = args[++i].split(',').map(s => s.trim());
        } else if (args[i] === '--format' && args[i + 1]) {
            options.format = args[++i];
        } else if (args[i] === '--max' && args[i + 1]) {
            options.maxResults = parseInt(args[++i]);
        } else if (args[i] === '--board' && args[i + 1]) {
            options.board = args[++i];
        } else if (args[i] === '--cache-only') {
            options.cacheOnly = true;
        }

    }
    return options;
}

async function main() {
    switch (command) {
        case 'search': {
            const keyword = args[1];
            if (!keyword) {
                console.log('사용법: node index.js search "키워드" [--platform mosaic,confluence] [--format json|table|markdown] [--max 20]');
                process.exit(1);
            }
            const options = parseOptions(args.slice(2));
            const output = await searcher.search(keyword, options);
            console.log(output);
            break;
        }

        case 'detail': {
            const platform = args[1];
            const id = args[2];
            if (!platform || !id) {
                console.log('사용법: node index.js detail <platform> <id> [--board BoardId]');
                process.exit(1);
            }
            const options = parseOptions(args.slice(3));
            console.log(`\n📄 상세 조회: ${platform}/${id}\n`);
            const result = await searcher.getDetail(platform, id, options);
            if (result) {
                console.log(JSON.stringify(result, null, 2).substring(0, 5000));
            } else {
                console.log('❌ 결과를 찾을 수 없습니다.');
            }
            break;
        }

        case 'cache': {
            const subCmd = args[1];
            if (subCmd === 'clear') {
                const cache = new Cache(config.cache);
                cache.clear();
                console.log('✅ 캐시가 삭제되었습니다.');
            } else {
                console.log('사용법: node index.js cache clear');
            }
            break;
        }

        case 'stats': {
            const keyword = args[1];
            if (!keyword) {
                console.log('사용법: node index.js stats "키워드"');
                process.exit(1);
            }
            // 플랫폼별 검색 결과 건수만 출력
            const platforms = ['mosaic', 'confluence', 'axhub'];
            for (const p of platforms) {
                try {
                    const adapter = searcher.adapters[p];
                    const results = await adapter.search(keyword, 100);
                    console.log(`${p}: ${results.length}건`);
                } catch (e) {
                    console.log(`${p}: 오류 (${e.message})`);
                }
            }
            break;
        }

        default:
            console.log(`
╔══════════════════════════════════════════════════════════════╗
║  SDSearch - Samsung Doc Search v1.0                           ║
║  Mosaic / Confluence / axhub 통합 검색 툴                     ║
╚══════════════════════════════════════════════════════════════╝

사용법:
  node index.js search "키워드"           통합 검색
  node index.js search "키워드" --platform mosaic,confluence  플랫폼 선택
  node index.js search "키워드" --format json                 JSON 출력
  node index.js search "키워드" --format markdown              Markdown 출력
  node index.js search "키워드" --max 30                       최대 결과 수
  node index.js detail <platform> <id>      상세 내용 조회
  node index.js stats "키워드"              플랫폼별 결과 건수
  node index.js cache clear                캐시 삭제

예시:
  node index.js search "GitHub"
  node index.js search "USM" --platform mosaic --format json
  node index.js search "자동화" --format markdown
  node index.js detail axhub POST00008055 --board AICrewActivityBoard
            `);
    }
}

main().catch(err => {
    console.error('❌ 오류:', err.message);
    process.exit(1);
});
