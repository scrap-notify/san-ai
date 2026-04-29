# AI 서버 API 명세

[Notion 링크](https://www.notion.so/dahyeonii/AI-API-34ab91841cc580e1a443f271cb33717f)

### 공통 에러 응답

| HTTP 상태코드 | 설명 |
| --- | --- |
| `400` | 요청 값이 잘못된 경우 (필드 누락, 타입 오류 등) |
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
| `title` | `string` | 원문을 대표하는 제목 1개 |
| `summary` | `string` | 3줄 이내 요약 텍스트 |
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
  "title": "React 상태 관리 기본 개념",
  "summary": "React에서 상태는 컴포넌트가 기억해야 할 정보를 의미한다. useState를 통해 상태를 선언하고, 상태가 변경되면 컴포넌트가 리렌더링된다. 상태를 적절한 위치에 두는 것이 React 설계의 핵심이다.",
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

> 오늘 저장한 지식 카드 원문들을 GitHub 업로드용 마크다운 문서로 정리한다.
리콜 TIL 페이지에서 활용한다.
> 

**`POST /ai/til`**

---

### 입력값 (Request Body)

| 필드명 | 타입 | 필수 여부 | 설명 |
| --- | --- | --- | --- |
| `contents`  | `object[]` | ✅ 필수 | TIL 생성에 사용할 수집된 지식원문. `input_type`(`url`/`text`/`image`), `content`(텍스트 원문, 사이트 링크, S3 이미지 링크) 포함 |
| `generate_til` | `boolean` | ✅ 필수 | `true`이면 마크다운 TIL 문서를 생성해 반환. `false`이면 임베딩 벡터만 반환 |

---

### 출력값 (Response Body)

| 필드명 | 타입 | 설명 |
| --- | --- | --- |
| `til_markdown` | `string | null` | `generate_til=true`일 때만 반환. 카드별 단순 나열이 아닌 주제별로 구조화된 마크다운 문서. `false`이면 `null` |
| `embeddings` | `number[]` | 임베딩 벡터 결과값 |

### 요청/응답 예시

**Request**

```json
{
  "contents": [
    { "input_type": "url", "content": "https://react.dev/learn/managing-state" },
    { "input_type": "text", "content": "클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다." },
    { "input_type": "image", "content": "https://s3.amazonaws.com/bucket/capture.png" }
  ],
  "generate_til": true
}
```

**Response**

```json
{
  "til_markdown": "# TIL - 2025.04.24\n\n## React 상태 관리\n\nReact에서 상태는 컴포넌트가 기억해야 할 정보를 의미한다. ...\n\n## JavaScript 클로저\n\n클로저는 함수가 선언될 당시의 외부 변수를 기억하는 개념이다. ...",
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

## 3. 자연어 카드 검색

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

- 입력: 지식 카드 원문들, 요약 (T/F)
- 출력: markdown 형식 TIL 문서(T인 경우만), 원문 기반 임베딩 벡터 결과값
- 동작:
    - AI 서버가 입력값을 바탕으로 TIL 문서를 md 형식으로 생성
    - AI 서버가 입력값을 바탕으로 임베딩하고 결과값을 생성한다
- 용도: 리콜 TIL 페이지

### 3. 자연어 카드 검색

- 입력: 사용자의 자연어 질문
- 출력: 임베딩 벡터 결과값
- 동작: AI 서버가 자연어 질의를 임베딩하고 결과값을 생성한다
- 용도: 검색창에서 저장된 지식카드를 탐색하는 데 사용한다.