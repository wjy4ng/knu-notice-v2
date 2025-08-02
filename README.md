## knu-notice-v2

공주대학교 새 소식 알림판 - 자동 공지사항 크롤링 및 표시 시스템

### 자동화 프로세스

1. **GitHub Actions 크롤링** (매시간 자동 실행)
   - Selenium을 사용하여 공주대학교 공지사항 웹사이트 크롤링
   - 크롤링된 데이터를 `crawled_data.json` 형태로 변환

2. **Render.com PostgreSQL 저장**
   - GitHub Actions에서 크롤링 완료 후 JSON 데이터를 Render API로 전송
   - 중복 공지는 업데이트, 새 공지는 생성
   - PostgreSQL에 영구 저장되어 재배포 시에도 데이터 유지

3. **웹 프론트엔드 표시**
   - Render에서 Django 서버가 PostgreSQL 조회
   - 날짜별 게시판 공지 개수 API 제공
   - 마우스 호버 시 미리보기 기능
   - 고정글 제외한 일반 공지만 카운트 및 표시

### 🛠 기술 스택
- **크롤링**: Python + Selenium + BeautifulSoup
- **백엔드**: Django + PostgreSQL 
- **프론트엔드**: HTML + CSS + JavaScript
- **배포**: Render.com (Web Service + PostgreSQL)
- **자동화**: GitHub Actions (Cron 스케줄링)