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
uv run fastapi dev app/main.py
```

## 로컬 테스트

### 사전 준비

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 및 실행
- `act` 설치 (Windows)
  ```powershell
  winget install nektos.act
  ```
  > macOS: `brew install act` / Linux: [공식 설치 가이드](https://nektosact.com/installation/index.html)

### Docker 실행

```bash
# 환경 변수 설정
cp .env.example .env

# 컨테이너 빌드 및 실행
docker compose up -d --build

# 종료
docker compose down

# 로그 확인
docker compose logs -f

# 헬스체크
curl http://localhost:8001/health
```

### CI 로컬 테스트 (act)

```bash
# build job만 실행
act -j build --container-architecture linux/amd64
```

## 개발 컨벤션

[docs/ai-convention.md](docs/ai-convention.md) 참고
