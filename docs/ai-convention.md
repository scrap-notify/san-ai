# AI 개발 컨벤션

LangChain과 FastAPI 기반 AI 서버 개발 시 지켜야 할 최소 컨벤션입니다.

[Notion](https://www.notion.so/dahyeonii/AI-Convention-344b91841cc5806f83b5ea30e2e1dfe3) 과 [GitHub 문서](https://github.com/Scrap-Notify/san-ai/blob/main/docs/ai-convention.md) 내용은 동기화되도록 관리합니다.

# 1. 코드 스타일 & 포맷터

- Python 코드는 `ruff`, `black` 기준으로 정리합니다.
- API 요청/응답은 `pydantic` 모델로 정의합니다.
- 함수와 클래스 이름은 역할이 드러나게 작성합니다.
- endpoint에는 요청 검증, 서비스 호출, 응답 반환만 둡니다.
- LLM, vector store, prompt 관련 설정값은 코드에 직접 쓰지 않고 설정으로 분리합니다.

# 2. 패키지 관리 및 실행

- 패키지 관리는 `uv`를 사용합니다.
- 의존성은 `pyproject.toml`에 정의하고, 잠금 파일은 `uv.lock`으로 관리합니다.
- 패키지 추가 시 `uv add <package>`를 사용합니다.
- 개발용 패키지 추가 시 `uv add --dev <package>`를 사용합니다.
- 서버 실행은 `uv run`을 통해 실행합니다.

```bash
uv sync
uv run fastapi dev app/main.py
```

운영 환경에서는 다음과 같이 실행합니다.

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

# 3. 주석

- 주석은 코드의 동작보다 의도를 설명할 때만 작성합니다.
- 복잡한 chain 구성, prompt 설계 이유, fallback 정책에는 짧게 주석을 남깁니다.
- 사용하지 않는 코드, 디버깅 주석, 임시 로그는 커밋 전에 제거합니다.
- TODO는 가능하면 이슈 번호나 담당자를 함께 남깁니다.

# 4. 패키지 구조

```
.
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── schemas/
│   ├── services/
│   ├── chains/
│   ├── prompts/
│   ├── retrievers/
│   ├── vectorstores/
│   ├── llms/
│   └── utils/
├── scripts/
├── tests/
├── docs/
├── .env.example
└── pyproject.toml
```

- `api`: FastAPI router와 endpoint를 관리합니다.
- `schemas`: 요청/응답 Pydantic 모델을 관리합니다.
- `services`: 실제 유스케이스 로직을 관리합니다.
- `chains`: LangChain chain, runnable 구성을 관리합니다.
- `prompts`: prompt 템플릿 파일을 관리합니다.
- `retrievers`: 검색, reranking, filtering 로직을 관리합니다.
- `vectorstores`: vector DB 연결 및 생성을 관리합니다.
- `llms`: LLM, embedding model 생성을 관리합니다.
- `scripts`: 문서 적재, 벡터 DB 재생성, 평가 등 실행 스크립트를 관리합니다.
- `docs`: 개발 컨벤션, API 문서, 운영 가이드 등 프로젝트 문서를 관리합니다.

기본 의존성 방향은 다음을 따릅니다.

```
api -> services -> chains/retrievers -> llms/vectorstores
```

# 5. 설정 파일 관리 및 보안

- 실제 비밀값은 `.env`에 두고 Git에 올리지 않습니다.
- `.env.example`에는 필요한 환경 변수 이름만 예시로 작성합니다.
- 설정 로딩은 `app/core/config.py`에서 관리합니다.
- API key, DB password, access token은 코드와 로그에 남기지 않습니다.
- LLM 요청/응답을 저장할 경우 개인정보 포함 여부를 먼저 확인합니다.
- 운영 환경에서는 CORS, timeout, rate limit, request size limit을 설정합니다.

```
APP_ENV=local
LOG_LEVEL=INFO
OPENAI_API_KEY=your-openai-api-key
VECTORSTORE_URL=http://localhost:6333
```

# 6. 기타

- 본 컨벤션은 팀 상황에 따라 **점진적으로 개선**할 수 있습니다.
- 변경 사항 발생 시 팀원 전체에게 공유합니다.
