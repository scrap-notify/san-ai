# SAN-AI

**Scrap-And-Notify (SAN)** 서비스의 AI 서버입니다.
FastAPI 기반으로 LangChain을 활용한 AI 기능을 제공합니다.

## 기술 스택

- **Framework:** FastAPI, Uvicorn
- **AI/LLM:** LangChain, LangChain-OpenAI, Qdrant
- **패키지 관리:** uv
- **Python:** 3.11+

## 시작하기

```bash
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
uv run fastapi dev app/main.py --host "0.0.0.0" --port 8001
```

## Docker

```bash
# 환경 변수 설정
cp .env.example .env

# 컨테이너 빌드 및 실행
docker compose up --build

# health check
curl http://localhost:8001/health
```

## CI/CD 파이프라인

GitHub Actions 기반으로 세 가지 워크플로우가 동작합니다.

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

| 트리거 | 대상 브랜치 |
|--------|-------------|
| `push`, `pull_request` | `main`, `develop` |

**Build 단계 (모든 push/PR):**

```
Checkout → uv 설치 → Python 설치 → 의존성 설치(uv sync --frozen) → Lint(ruff check) → Test(pytest)
```

**Deploy 단계 (main push만):**

```
SSH 접속 → git pull → .env 복사(/var/www/san/.env.ai) → docker compose up --build → 헬스체크(localhost:8001/health)
```

### 2. PR Mattermost 알림 (`.github/workflows/pr-mattermost.yml`)

PR이 열리거나, 업데이트되거나, 머지/클로즈될 때 Mattermost 웹훅으로 알림을 전송합니다.

### 3. GitLab 동기화 (`.github/workflows/sync-to-gitlab.yml`)

`main` 브랜치에 push 시 GitLab의 `ai/default` 브랜치로 자동 동기화됩니다. `workflow_dispatch`로 수동 실행도 가능합니다.

### 필요한 GitHub Secrets

| Secret | 용도 |
|--------|------|
| `DEPLOY_HOST` | 배포 서버 호스트 |
| `DEPLOY_USER` | 배포 서버 SSH 사용자 |
| `DEPLOY_SSH_KEY` | 배포 서버 SSH 키 |
| `MATTERMOST_WEBHOOK_URL` | Mattermost 알림 웹훅 URL |
| `GITLAB_TOKEN` | GitLab 동기화용 토큰 |

## 로컬 테스트

### 직접 실행

```bash
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일에서 OPENAI_API_KEY 등 필요한 값 설정

# 린트
uv run ruff check .

# 테스트
uv run pytest

# 개발 서버 실행
uv run fastapi dev app/main.py --host "0.0.0.0" --port 8001
```

### Docker로 실행

```bash
cp .env.example .env
# .env 파일 수정 후

docker compose up --build

# 헬스체크
curl http://localhost:8001/health
```

### 환경 변수 (.env)

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `APP_ENV` | 실행 환경 | `local` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |
| `OPENAI_API_KEY` | OpenAI API 키 | - |
| `OPENAI_BASE_URL` | OpenAI API Base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 사용 모델 | `gpt-5.2` |
| `OPENAI_TIMEOUT` | 요청 타임아웃(초) | `30` |
| `OPENAI_EMBEDDING_MODEL` | 임베딩 모델 | `text-embedding-3-small` |
| `VECTORSTORE_URL` | Qdrant 벡터 DB URL | `http://localhost:6333` |

## 개발 컨벤션

[docs/ai-convention.md](docs/ai-convention.md) 참고
