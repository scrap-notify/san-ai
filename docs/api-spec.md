# AI 서버 API 명세

[Notion 링크](https://www.notion.so/dahyeonii/AI-API-34ab91841cc580e1a443f271cb33717f)

### 공통 에러 응답

| HTTP 상태코드 | 설명 |
| --- | --- |
| `400` | 요청 값이 잘못된 경우 (필드 누락, 타입 오류 등) |
| `404` | 요청한 외부 리소스가 존재하지 않는 경우 |
| `422` | 입력값은 유효하나 AI 처리 실패한 경우 |
| `500` | AI 서버 내부 오류 |

```json
{
  "error": "error_code",
  "message": "에러 설명"
}
```

---

## 1. 카드 AI 분석

> 스크랩 원본 데이터를 해석해 지식카드 저장에 필요한 메타데이터를 일괄 생성한다.
> 

**`POST /ai/analyze`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `input_type` | `string` | ✅ 필수 | 입력 데이터의 종류. `"url"` / `"text"` / `"image"` 중 하나 |
| `content` | `string` | ✅ 필수 | 스크랩 원본 데이터. URL 문자열, 텍스트, S3 이미지 링크 |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `title` | `string` | 원문을 대표하는 제목 1개 (20자 이하 권장) |
| `summary` | `string` | 요약 텍스트 (3문장 이내, 각 문장 27자 이하 권장) |
| `tags` | `string[]` | 핵심 키워드 태그 목록(5개 이내) |
| `category` | `string` | 카테고리 체계에 따른 분류 결과 1개 |
| `embedding` | `number[]` | 입력 데이터 기반 임베딩 벡터 결과값 |

### 요청/응답 예시

**Request**

```json
{
  "input_type": "url",
  "content": "https://react.dev/learn/managing-state"
}
```

**Response**

```json
{
  "title": "React 상태 관리",
  "summary": "상태는 화면 정보를 기억한다.\nuseState로 상태를 선언한다.\n상태 위치가 설계의 핵심이다.",
  "tags": ["React", "상태관리", "useState", "리렌더링"],
  "category": "프론트엔드",
  "embedding": [0.012, -0.453, 0.891, "..."]
}
```

### 에러 코드

| 에러 코드 | 상태코드 | 설명 |
| --- | --- | --- |
| `invalid_input_type` | `400` | `input_type`이 `url` / `text` / `image` 외의 값인 경우 |
| `missing_content` | `400` | `content` 필드가 비어있는 경우 |
| `analyze_failed` | `422` | AI 분석 처리 실패 (제목·요약·태그·카테고리 생성 불가) |
| `embedding_failed` | `422` | 임베딩 벡터 생성 실패 |

---

## 2. TIL 생성

> 오늘 수집한 여러 카드 원문을 학습자 관점으로 요약/정리해 TIL 마크다운 문서를 생성한다.
> 카드별 개별 요약(병렬) → 주제별 통합 TIL 생성의 2단계 Map-Reduce 구조로 동작한다.
> 단일 카드 원문 구조화는 `/ai/card` 엔드포인트를 사용한다.

**`POST /ai/til`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `contents` | `object[]` | ✅ 필수 | TIL을 구성할 카드 목록. 1개 이상 필요. 각 항목은 `input_type`(`url`/`text`/`image`)과 `content`(URL 문자열, 텍스트 원문, S3 이미지 링크) 포함 |
| `generate_til` | `boolean` | ✅ 필수 | `true`이면 TIL 마크다운 문서를 생성해 반환. `false`이면 임베딩 벡터만 반환 |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `title` | `string \| null` | `generate_til=true`일 때만 반환. 오늘 다룬 주제들을 대표하는 한 줄 제목. `false`이면 `null` |
| `til_markdown` | `string \| null` | `generate_til=true`일 때만 반환. 카드 내용을 학습자 관점으로 요약·주제별로 구조화한 마크다운 문서. 코드가 포함된 경우 언어 식별자가 명시된 코드 펜스(` ```python ` 등)로 감싸 반환하며, 언어를 특정할 수 없으면 ` ```text ` 를 사용한다. `false`이면 `null` |
| `embedding` | `number[]` | 전체 contents를 통합한 임베딩 벡터 1개 (카드별 개별 벡터 아님) |

### 요청/응답 예시

**Request**

```json
{
  "contents": [
    { "input_type": "url", "content": "https://fastapi.tiangolo.com/async/" },
    { "input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다." },
    { "input_type": "url", "content": "https://docs.python.org/3/tutorial/classes.html" }
  ],
  "generate_til": true
}
```

**Response**

```json
{
  "title": "FastAPI 비동기 처리와 Python 핵심 개념",
  "til_markdown": "# TIL\n\n## FastAPI 비동기 처리\n\nFastAPI는 async/await를 기반으로 비동기 요청을 처리한다. ...\n\n## Python 클로저와 클래스\n\n클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다. ...",
  "embedding": [0.012, -0.453, 0.891, "..."]
}
```

### 에러 코드

| 에러 코드 | 상태코드 | 설명 |
| --- | --- | --- |
| `missing_contents` | `400` | `contents` 배열이 비어있는 경우 |
| `invalid_input_type` | `400` | `contents` 내 `input_type`이 유효하지 않은 값인 경우 |
| `til_generation_failed` | `422` | TIL 마크다운 문서 생성 실패 |
| `embedding_failed` | `422` | 임베딩 벡터 생성 실패 |

---

## 3. 카드 상세 문서화

> 단일 카드 원문을 요약 없이 그대로 구조화해 마크다운 문서로 반환한다.
> 원문 흐름을 유지하며 구조화하는 카드 상세보기 전용 엔드포인트.

**`POST /ai/card`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `content` | `object` | ✅ 필수 | 단일 카드 콘텐츠. `input_type`(`url`/`text`/`image`)과 `content`(URL 문자열, 텍스트 원문, S3 이미지 링크) 포함 |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `title` | `string` | 원문 내용을 대표하는 한 줄 제목 |
| `card_markdown` | `string` | 원문을 구조화한 마크다운 문서. 요약 없이 원문 흐름 그대로 유지. 코드가 포함된 경우 언어 식별자가 명시된 코드 펜스(` ```python ` 등)로 감싸 반환하며, 언어를 특정할 수 없으면 ` ```text ` 를 사용한다 |
| `embedding` | `number[]` | 카드 콘텐츠 임베딩 벡터 |

### 요청/응답 예시

**Request**

```json
{
  "content": {
    "input_type": "url",
    "content": "https://fastapi.tiangolo.com/tutorial/first-steps/"
  }
}
```

**Response**

```json
{
  "title": "FastAPI 첫 번째 단계",
  "card_markdown": "## FastAPI 소개\n\nFastAPI는 Python 3.8+를 기반으로 한 현대적인 고성능 웹 프레임워크다. ...\n\n## 첫 번째 API 만들기\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get(\"/\")\ndef read_root():\n    return {\"Hello\": \"World\"}\n```",
  "embedding": [0.012, -0.453, 0.891, "..."]
}
```

### 에러 코드

| 에러 코드 | 상태코드 | 설명 |
| --- | --- | --- |
| `missing_content` | `400` | `content` 필드가 비어있는 경우 |
| `invalid_input_type` | `400` | `input_type`이 `url` / `text` / `image` 외의 값인 경우 |
| `card_detail_failed` | `422` | 카드 마크다운 문서 생성 실패 |
| `embedding_failed` | `422` | 임베딩 벡터 생성 실패 |

---

## 4. 자연어 카드 검색

> 사용자의 자연어 질의를 임베딩 벡터로 변환한다.
백엔드가 이 벡터로 벡터 DB를 조회해 유사 카드를 검색·후보 조회·재정렬 후 결과를 반환한다.
> 

**`POST /ai/search`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `query` | `string` | ✅ 필수 | 사용자가 검색창에 입력한 자연어 질의 문장. 예: `"리액트 상태관리 개념 정리"` |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `embedding` | `number[]` | 자연어 질의 기반 임베딩 벡터 결과값 |

### 요청/응답 예시

**Request**

```json
{
  "query": "리액트 상태관리 개념 정리"
}
```

**Response**

```json
{
  "embedding": [0.023, -0.341, 0.756, "..."]
}
```

### 에러 코드

| 에러 코드 | 상태코드 | 설명 |
| --- | --- | --- |
| `missing_query` | `400` | `query` 필드가 비어있는 경우 |
| `embedding_failed` | `422` | 임베딩 벡터 생성 실패 |

---

## 5. 퀴즈 생성

> 스크랩된 콘텐츠를 기반으로 퀴즈 문제를 생성한다.
> - 콘텐츠 1개당 문제 1개가 자동으로 생성된다.
> - 질문·정답·해설은 콘텐츠 언어에 관계없이 **한국어**로 생성된다. 단, OpenAPI·Docker 등 고유 명사·기술 용어는 원문 표기를 그대로 사용한다.
> - 정답 비교 시 **대소문자 무시(case-insensitive) + 앞뒤 공백 trim** 처리를 권장한다.

**`POST /ai/quiz`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `contents` | `object[]` | ✅ 필수 | 퀴즈를 생성할 콘텐츠 목록. `input_type`(`url`/`text`/`image`), `content`(텍스트 원문, 사이트 링크, S3 이미지 링크) 포함. 1개 이상 필요 |
| `quiz_type` | `string` | ✅ 필수 | 퀴즈 유형. `"short_answer"`: 단답형 / `"ox"`: O/X 퀴즈 |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `quiz_type` | `string` | 생성된 퀴즈 유형 (`"short_answer"` / `"ox"`) |
| `questions` | `object[]` | 생성된 문제 목록. `quiz_type`에 따라 항목 구조가 다름 (아래 참고) |

#### `questions` 항목 구조 — `short_answer`

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `question` | `string` | 질문 |
| `answer` | `string` | 정답 (고유 용어 또는 단어 하나) |
| `explanation` | `string \| null` | 해설 한 문장. 없으면 `null` |

#### `questions` 항목 구조 — `ox`

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `statement` | `string` | O/X 판단할 문장 |
| `is_correct` | `boolean` | `true` = O, `false` = X |
| `explanation` | `string \| null` | 해설 한 문장. 없으면 `null` |

### 요청/응답 예시

**Request**

```json
{
  "contents": [
    { "input_type": "url", "content": "https://docs.python.org/3/tutorial/classes.html" },
    { "input_type": "url", "content": "https://martinfowler.com/articles/injection.html" },
    { "input_type": "text", "content": "Docker는 애플리케이션을 컨테이너로 패키징해 어디서든 동일하게 실행할 수 있게 해주는 플랫폼이다." }
  ],
  "quiz_type": "short_answer"
}
```

**Response**

```json
{
  "quiz_type": "short_answer",
  "questions": [
    {
      "question": "Python에서 클래스의 인스턴스를 생성할 때 자동으로 호출되는 초기화 메서드는?",
      "answer": "__init__",
      "explanation": "__init__ 메서드는 인스턴스가 생성될 때 자동 호출되어 초기 상태를 설정한다."
    },
    {
      "question": "Martin Fowler가 제안한, 객체가 직접 의존성을 생성하지 않고 외부에서 주입받는 패턴은?",
      "answer": "Dependency Injection",
      "explanation": "의존성 주입은 객체 간 결합도를 낮추고 테스트 용이성을 높이기 위해 외부에서 의존성을 전달하는 패턴이다."
    },
    {
      "question": "Docker에서 애플리케이션과 실행 환경을 묶어 격리된 단위로 실행하는 것을 무엇이라 하는가?",
      "answer": "컨테이너",
      "explanation": "컨테이너는 애플리케이션과 그 의존성을 하나의 실행 단위로 묶어 환경에 관계없이 동일하게 동작하게 한다."
    }
  ]
}
```

### 에러 코드

| 에러 코드 | 상태코드 | 설명 |
| --- | --- | --- |
| `missing_contents` | `400` | `contents` 배열이 비어있는 경우 |
| `invalid_input_type` | `400` | `contents` 내 `input_type`이 유효하지 않은 값인 경우 |
| `quiz_generation_failed` | `422` | AI 퀴즈 생성 실패 또는 LLM 응답 필수 필드 누락 |

---

## 5. GitHub Star 기반 cold-start 글 추천

> GitHub 사용자의 Star 목록을 기반으로 신규 사용자가 스크랩할 만한 외부 글 URL을 추천한다.
> 추천 결과는 `POST /ai/analyze` 요청 데이터에 바로 넣을 수 있는 형태로 반환한다.
>

**`POST /ai/recommend/github-stars`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `github_username` | `string` | ✅ 필수 | 추천에 사용할 GitHub 사용자명 |
| `limit` | `integer` | 선택 | 추천 결과 최대 반환 개수. 생략 시 기본값 `5`, 허용 범위 `1`~`10` |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `recommendations` | `object[]` | 추천 외부 글 URL 목록. 각 항목은 `POST /ai/analyze` 요청 Body로 그대로 사용할 수 있다. |

#### `recommendations[]`

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `input_type` | `string` | 항상 `"url"` |
| `content` | `string` | 추천 외부 글 URL |

### 요청/응답 예시

**Request**

```json
{
  "github_username": "octocat",
  "limit": 5
}
```

**Response**

```json
{
  "recommendations": [
    {
      "input_type": "url",
      "content": "https://react.dev/learn/managing-state"
    },
    {
      "input_type": "url",
      "content": "https://docs.github.com/en/actions"
    }
  ]
}
```

### 동작 방식

- AI 서버가 GitHub 공개 API를 직접 호출해 사용자의 공개 Star 목록을 조회한다. 서버에 GitHub API 토큰이 설정된 경우에만 토큰을 함께 전송한다.
- Star 목록의 저장소 이름, 설명, topics, 주요 언어 등을 LLM에 전달해 사용자의 관심사를 추론한다.
- LLM이 추론한 관심사를 Tavily 검색에 적합한 하나의 영어 검색 질의로 압축하고, Tavily 웹 검색 API를 1회 호출한다.
- Tavily 검색 결과를 사용자 관심사와의 관련성 기준으로 정제해 추천 URL 목록을 반환한다.
- Tavily 검색 결과가 요청한 `limit`보다 적은 경우에는 기본 추천 URL 목록으로 부족한 개수를 보완한다.
- Star가 하나도 없는 경우에는 사전에 정의된 기본 추천 URL 목록을 반환한다.
- AI 서버는 SAN 서비스 DB 또는 Vector DB를 조회하지 않는다.

### 에러 코드

| 에러 코드 | 상태코드 | 설명 |
| --- | --- | --- |
| `missing_github_username` | `400` | `github_username` 필드가 비어있는 경우 |
| `invalid_limit` | `400` | `limit` 값이 유효하지 않은 경우 |
| `github_user_not_found` | `404` | GitHub 사용자를 찾을 수 없는 경우 |
| `github_fetch_failed` | `422` | GitHub Star 목록 조회 실패 |
| `search_failed` | `422` | Tavily 검색 처리 실패 |
| `recommendation_failed` | `422` | 관심사 추론 또는 추천 결과 생성 실패 |

---

## 설명

**AI 서버에서는 DB, 벡터DB 모두 접근 안하기로 함**

### 1. 카드 AI 분석(사이드바)

- 입력: URL, 텍스트, 이미지 등 스크랩 원본
- 출력: 제목, 3줄 요약, 태그 목록, 카테고리, 임베딩 벡터 결과값
- 동작:
    - **입력값별 처리 방법은 추후**
    - AI 서버가 스크랩 원본 데이터를 해석해 지식카드 저장에 필요한 분석 결과를 생성한다
    - 입력 정보를 임베딩하고 결과값을 생성한다
- 용도: 크롬 사이드바에서 백엔드가 이 결과를 받아 지식카드 저장, 크롬 사이드바에서 관련 지식 카드를 추천

### 2. TIL 생성

- 입력: 지식 카드 원문 목록, `generate_til` (T/F)
- 출력: markdown 형식 TIL 문서(`generate_til=true`인 경우만), 전체 contents 통합 임베딩 벡터
- 동작:
    - 카드별 개별 요약(병렬) → 주제별 통합 TIL 생성의 2단계 Map-Reduce로 동작
    - `generate_til=false`이면 임베딩만 반환
- 용도: 리콜 TIL 페이지

### 3. 카드 상세 문서화

- 입력: 단일 카드 콘텐츠
- 출력: 원문을 구조화한 마크다운 문서, 임베딩 벡터
- 동작:
    - 단일 카드 원문을 요약 없이 그대로 구조화
    - 코드가 있으면 언어 식별자 있는 코드 펜스로 감쌈
- 용도: 카드 상세보기 페이지

### 4. 자연어 카드 검색

- 입력: 사용자의 자연어 질문
- 출력: 임베딩 벡터 결과값
- 동작: AI 서버가 자연어 질의를 임베딩하고 결과값을 생성한다
- 용도: 검색창에서 저장된 지식카드를 탐색하는 데 사용한다.

### 5. 퀴즈 생성

- 입력: 스크랩된 콘텐츠 목록(`url`/`text`/`image`), 퀴즈 유형(`short_answer` / `ox`)
- 출력: 퀴즈 유형 + 문제 목록
- 동작:
    - 콘텐츠 1개당 문제 1개를 자동 생성한다
    - `short_answer`: 핵심 개념을 묻는 단답형 문제(질문·정답·해설)를 생성한다
    - `ox`: 콘텐츠 기반 참/거짓 판단 문장(문장·정오표시·해설)을 생성한다
    - 질문·정답·해설은 콘텐츠 언어에 관계없이 한국어로 생성된다. 단, 고유 명사·기술 용어는 원문 표기 유지
- 용도: 학습한 내용을 퀴즈로 복습하는 기능에 사용한다

### 5. GitHub Star 기반 cold-start 글 추천

- 입력: GitHub 사용자명, 추천 결과 최대 개수
- 출력: `POST /ai/analyze` 요청 Body로 바로 사용할 수 있는 URL 추천 목록
- 동작:
    - AI 서버가 GitHub API를 직접 호출해 공개 Star 목록을 수집한다
    - Star 목록에서 관심 기술 스택과 주제를 추론한다
    - 추론 결과를 하나의 Tavily 검색 질의로 압축해 외부 글 후보를 수집한다
    - 검색 결과를 정제해 사용자가 스크랩할 만한 URL 목록을 반환한다
    - Star가 하나도 없는 경우 기본 추천 URL 목록을 반환한다
- 용도: 신규 사용자 또는 스크랩 이력이 부족한 사용자의 cold-start 추천
