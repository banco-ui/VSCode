/**
 * 검색 결과 포맷터
 * table, json, markdown 형식 지원
 */

class Formatter {
    format(results, format = 'table') {
        switch (format) {
            case 'json':
                return this.formatJSON(results);
            case 'markdown':
                return this.formatMarkdown(results);
            case 'table':
            default:
                return this.formatTable(results);
        }
    }

    formatTable(results) {
        if (!results || results.length === 0) {
            return '\n📭 검색 결과가 없습니다.\n';
        }

        const platformEmoji = {
            mosaic: '🟦',
            confluence: '🟩',
            axhub: '🟧'
        };

        let output = '\n';
        output += '┌─────┬────────────┬──────────────────────────────────────────────────────┬────────┐\n';
        output += '│  #  │  플랫폼    │  제목                                                 │  점수  │\n';
        output += '├─────┼────────────┼──────────────────────────────────────────────────────┼────────┤\n';

        results.forEach((r, idx) => {
            const num = String(idx + 1).padStart(3);
            const platform = (platformEmoji[r.platform] || '⬜') + ' ' + r.platform.padEnd(8);
            const title = (r.title || '').substring(0, 50).padEnd(50);
            const score = (r.score || 0).toFixed(2).padStart(6);
            output += `│ ${num} │ ${platform} │ ${title} │ ${score} │\n`;
        });

        output += '└─────┴────────────┴──────────────────────────────────────────────────────┴────────┘\n';
        output += `\n총 ${results.length}개 결과\n`;

        // 플랫폼별 통계
        const stats = {};
        results.forEach(r => {
            stats[r.platform] = (stats[r.platform] || 0) + 1;
        });
        output += '통계: ' + Object.entries(stats).map(([k, v]) => `${k}(${v}건)`).join(', ') + '\n';
        
        return output;
    }

    formatJSON(results) {
        return JSON.stringify(results, null, 2);
    }

    formatMarkdown(results) {
        if (!results || results.length === 0) {
            return '> 검색 결과가 없습니다.';
        }

        let md = `## 검색 결과 (${results.length}건)\n\n`;
        md += '| # | 플랫폼 | 제목 | 점수 | URL |\n';
        md += '|---|--------|------|------|-----|\n';

        results.forEach((r, idx) => {
            const title = (r.title || '').replace(/\|/g, '\\|').substring(0, 60);
            const url = r.url || '';
            md += `| ${idx + 1} | ${r.platform} | ${title} | ${(r.score || 0).toFixed(2)} | ${url} |\n`;
        });

        return md;
    }

    formatDetail(result, format = 'table') {
        if (!result) return '\n❌ 결과를 찾을 수 없습니다.\n';

        let output = '\n';
        output += '═══════════════════════════════════════════════════════════\n';
        output += `  플랫폼: ${result.platform || 'N/A'}\n`;
        output += `  제목:   ${result.title || 'N/A'}\n`;
        output += `  작성자: ${result.author || 'N/A'}\n`;
        output += `  날짜:   ${result.date || 'N/A'}\n`;
        output += `  URL:    ${result.url || 'N/A'}\n`;
        output += `  점수:   ${(result.score || 0).toFixed(2)}\n`;
        output += '───────────────────────────────────────────────────────────\n';
        output += `  내용:\n${(result.content || '').substring(0, 3000)}\n`;
        output += '═══════════════════════════════════════════════════════════\n';
        
        return output;
    }
}

module.exports = Formatter;
