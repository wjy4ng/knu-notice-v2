const express = require('express');
const path = require('path');
const app = express();

// root directory 설정
app.use(express.static(path.join(__dirname, '/')));

// /proxy 경로에 GET 요청이 오면 비동기 실행
app.get('/proxy', async (req, res) => {
  const url = req.query.url; // 크롤링할 url
  if (!url) {
    // CORS 정책 우회
    res.set('Access-Control-Allow-Origin', '*');
    return res.status(400).send('url query required'); // HTTP 400(Bad Request)
  }
  try {
    const response = await fetch(url, { // 외부 사이트로 요청을 보냄
      headers: {
        'User-Agent': // 실제 사용자 웹 브라우저처럼 헤더 설정
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        // HTML 문서 요청
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
    });
    const text = await response.text();
    
    // 사용자가 이 서버에 접근 가능하도록 CORS 헤더 설정
    res.set('Access-Control-Allow-Origin', '*');
    res.send(text);
  } catch (e) {
    res.set('Access-Control-Allow-Origin', '*');
    res.status(500).send('fetch error: ' + e.message);
  }
});

// 3001번 포트에서 실행
app.listen(3001, () => console.log('Proxy server running on 3001'));