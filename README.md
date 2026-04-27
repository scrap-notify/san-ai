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
uv run fastapi dev app/main.py --port 8001
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

## 개발 컨벤션

[docs/ai-convention.md](docs/ai-convention.md) 참고
