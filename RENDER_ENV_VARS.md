# Render.com Environment Variables 설정 가이드

## 🔑 필수 환경 변수

### 기본 설정
PYTHON_VERSION=3.13.5
DEBUG=False
RENDER=true

### 보안 키 (Generate 버튼으로 자동 생성 권장)
DJANGO_SECRET_KEY=[자동 생성]
CRAWL_AUTH_TOKEN=[자동 생성]

### 데이터베이스 연결
DATABASE_URL=[PostgreSQL 생성 후 자동 연결]

## 📊 선택적 환경 변수 (필요시 추가)

### 크롤링 설정
CRAWL_DAYS_BACK=7
CRAWL_MAX_PAGES=5
CRAWL_DELAY_SECONDS=3

### 로깅 레벨
LOG_LEVEL=INFO

### 타임존 설정
TZ=Asia/Seoul

## 🔧 Render Dashboard 설정 순서

1. **PostgreSQL 데이터베이스 생성**
   - New + → PostgreSQL
   - Name: knu-notice-db
   - Database Name: knu_notice
   - User: knu_notice

2. **Web Service 생성**
   - New + → Web Service
   - Connect GitHub → knu-notice-v2
   - Name: knu-notice-web
   - Build Command: ./build.sh
   - Start Command: gunicorn knu_notice.wsgi:application

3. **환경 변수 확인**
   - render.yaml이 있으므로 자동으로 설정됨
   - Environment 탭에서 확인 및 수정 가능

## 🤖 GitHub Actions Secrets 설정

Repository → Settings → Secrets and variables → Actions:

RENDER_APP_URL=https://knu-notice-web.onrender.com
CRAWL_AUTH_TOKEN=[Render의 CRAWL_AUTH_TOKEN과 동일한 값]

## ✅ 배포 후 확인할 점

1. 환경 변수가 모두 설정되었는지 확인
2. 데이터베이스 연결이 정상인지 확인
3. Chrome이 제대로 설치되었는지 확인 (빌드 로그)
4. Manual Crawl API가 작동하는지 테스트
