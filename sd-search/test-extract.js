const axios = require('axios');

(async () => {
    console.log('=== AX HUB Search Test (fixed Id regex) ===');
    try {
        const r = await axios.post('http://localhost:3120/api/search/axhub', {
            keyword: 'github',
            maxResults: 5,
            cacheOnly: false
        }, { timeout: 300000 });
        
        const data = r.data;
        console.log('success:', data.success);
        console.log('results:', data.results?.length || 0);
        if (data.logs) data.logs.forEach(l => console.log('  log:', l));
        if (data.results?.length > 0) {
            data.results.forEach((r, i) => {
                console.log(`\n  ${i+1}. title: ${r.title}`);
                console.log(`     url: ${r.url}`);
                console.log(`     author: ${r.author} | date: ${r.date} | id: ${r.id}`);
            });
        }
    } catch (e) {
        console.log('Error:', e.response ? e.response.status : e.message);
        if (e.response?.data) console.log('Body:', JSON.stringify(e.response.data).substring(0, 500));
    }
})();
