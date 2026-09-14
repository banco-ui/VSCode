const axios = require('axios');

(async () => {
    // 1. 먼저 Mosaic 검색으로 "5g" 검색 (검색 결과 캐시 생성)
    console.log('=== Step 1: Search "5g" on Mosaic ===');
    const searchRes = await axios.post('http://localhost:3120/api/search/mosaic', {
        keyword: '5g',
        maxResults: 20,
        cacheOnly: false,
        category: 'workspace'
    }, { timeout: 60000 });
    
    const searchResults = searchRes.data.results || [];
    console.log(`Search results: ${searchResults.length}`);
    
    // 검색 결과에서 /detail/1800053612 URL 찾기
    const targetPost = searchResults.find(r => (r.url || '').includes('/detail/1800053612'));
    if (targetPost) {
        console.log('Found target post in search results:');
        console.log('  title:', targetPost.title);
        console.log('  url:', targetPost.url);
        console.log('  content length:', (targetPost.content || '').length);
    } else {
        console.log('Target post not found in search results');
        console.log('First 3 URLs:');
        searchResults.slice(0, 3).forEach((r, i) => {
            console.log(`  ${i+1}. ${r.url}`);
        });
    }
    
    // 2. 추출 API 호출 (cachedResults 포함)
    console.log('\n=== Step 2: Extract with cachedResults ===');
    const extractRes = await axios.post('http://localhost:3120/api/extract', {
        url: 'https://mosaic.sec.samsung.net/collaboration/workspace/584541588/list/592839726/detail/1800053612',
        cachedResults: searchResults
    }, { timeout: 120000 });
    
    const d = extractRes.data;
    if (d.success) {
        console.log('SUCCESS!');
        console.log('title:', d.result.title);
        console.log('author:', d.result.author);
        console.log('date:', d.result.date);
        console.log('workspace:', d.result.workspaceName);
        console.log('content length:', (d.result.content || '').length);
        console.log('content preview:', (d.result.content || '').substring(0, 300));
    } else {
        console.log('FAIL:', d.error);
    }
    if (d.logs) d.logs.forEach(l => console.log('  log:', l));
})();
