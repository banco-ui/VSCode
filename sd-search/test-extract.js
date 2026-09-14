const axios = require('axios');

(async () => {
    // Confluence 검색 테스트
    console.log('=== Confluence Search Test ===');
    try {
        const r = await axios.post('http://localhost:3120/api/search/confluence', {
            keyword: '5g',
            maxResults: 10,
            cacheOnly: false
        }, { timeout: 60000 });
        
        const data = r.data;
        console.log('success:', data.success);
        console.log('results:', data.results?.length || 0);
        if (data.logs) data.logs.forEach(l => console.log('  log:', l));
        if (data.results?.length > 0) {
            data.results.slice(0, 3).forEach((r, i) => {
                console.log(`  ${i+1}. ${r.title?.substring(0, 50)} | ${r.url}`);
            });
        }
    } catch (e) {
        console.log('Error:', e.response ? e.response.status : e.message);
        if (e.response?.data) console.log('Body:', JSON.stringify(e.response.data).substring(0, 500));
    }
})();
