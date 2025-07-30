# Render.com 환경 변수 설정 가이드

## 필수 환경 변수 (Render Dashboard에서 설정)

PYTHON_VERSION=3.13.5
DEBUG=False
RENDER=true
DJANGO_SECRET_KEY=(자동 생성됨)
CRAWL_AUTH_TOKEN=(자동 생성됨)
DATABASE_URL=(데이터베이스 연결 후 자동 설정)

## 데이터베이스 설정 단계:
1. Render Dashboard에서 "New +" → "PostgreSQL" 선택
2. Database Name: knu-notice-db
3. User: knu_notice
4. 생성 후 CONNECTION STRING 복사
5. Web Service 환경 변수에 DATABASE_URL로 추가

## GitHub Actions 설정을 위한 Secrets:
Repository Settings → Secrets and variables → Actions에서 추가:
- RENDER_APP_URL: https://knu-notice-web.onrender.com (배포 후 URL)
- CRAWL_AUTH_TOKEN: (Render의 CRAWL_AUTH_TOKEN과 동일한 값)
