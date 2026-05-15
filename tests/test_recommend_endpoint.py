from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import AIProcessingError, ResourceNotFoundError
from app.main import app
from app.services.recommend import (
    _is_recommendable_result,
    _rank_recommendation_results,
    _search_tavily,
)

client = TestClient(app)


def test_github_stars_recommend_returns_urls() -> None:
    repositories = [
        {
            "name": "fastapi",
            "description": "FastAPI framework",
            "topics": ["python", "api"],
            "language": "Python",
        }
    ]
    searched_urls = [
        "https://fastapi.tiangolo.com/tutorial/first-steps/",
        "https://docs.python.org/3/tutorial/",
    ]

    with patch(
        "app.services.recommend._fetch_starred_repositories",
        new=AsyncMock(return_value=repositories),
    ), patch(
        "app.services.recommend._generate_search_query",
        new=AsyncMock(return_value="python fastapi backend API design guide"),
    ), patch(
        "app.services.recommend._search_tavily",
        new=AsyncMock(return_value=searched_urls),
    ):
        response = client.post(
            "/ai/recommend/github-stars",
            json={"github_username": "octocat", "limit": 2},
        )

    assert response.status_code == 200
    assert response.json() == {
        "recommendations": [
            {
                "input_type": "url",
                "content": "https://fastapi.tiangolo.com/tutorial/first-steps/",
            },
            {
                "input_type": "url",
                "content": "https://docs.python.org/3/tutorial/",
            },
        ]
    }


def test_github_stars_recommend_uses_default_limit() -> None:
    with patch(
        "app.services.recommend._fetch_starred_repositories",
        new=AsyncMock(return_value=[]),
    ), patch(
        "app.services.recommend._generate_search_query",
        new=AsyncMock(),
    ) as query_mock, patch("app.services.recommend._search_tavily", new=AsyncMock()) as search_mock:
        response = client.post(
            "/ai/recommend/github-stars",
            json={"github_username": "octocat"},
        )

    assert response.status_code == 200
    assert len(response.json()["recommendations"]) == 5
    query_mock.assert_not_called()
    search_mock.assert_not_called()


def test_empty_github_username_returns_400() -> None:
    response = client.post(
        "/ai/recommend/github-stars",
        json={"github_username": "   ", "limit": 5},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "missing_github_username"


def test_missing_github_username_returns_400() -> None:
    response = client.post("/ai/recommend/github-stars", json={"limit": 5})

    assert response.status_code == 400
    assert response.json()["error"] == "missing_github_username"


def test_invalid_limit_returns_400() -> None:
    response = client.post(
        "/ai/recommend/github-stars",
        json={"github_username": "octocat", "limit": 11},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_limit"


def test_github_user_not_found_returns_404() -> None:
    with patch(
        "app.services.recommend._fetch_starred_repositories",
        new=AsyncMock(side_effect=ResourceNotFoundError(
            code="github_user_not_found",
            message="GitHub 사용자를 찾을 수 없습니다.",
        )),
    ):
        response = client.post(
            "/ai/recommend/github-stars",
            json={"github_username": "unknown", "limit": 5},
        )

    assert response.status_code == 404
    assert response.json()["error"] == "github_user_not_found"


def test_github_fetch_failure_returns_422() -> None:
    with patch(
        "app.services.recommend._fetch_starred_repositories",
        new=AsyncMock(side_effect=AIProcessingError(
            code="github_fetch_failed",
            message="GitHub 실패",
        )),
    ):
        response = client.post(
            "/ai/recommend/github-stars",
            json={"github_username": "octocat", "limit": 5},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "github_fetch_failed"


def test_tavily_failure_returns_422() -> None:
    repositories = [
        {
            "name": "react",
            "description": "React library",
            "topics": ["react", "frontend"],
            "language": "TypeScript",
        }
    ]

    with patch(
        "app.services.recommend._fetch_starred_repositories",
        new=AsyncMock(return_value=repositories),
    ), patch(
        "app.services.recommend._generate_search_query",
        new=AsyncMock(return_value="react frontend state management guide"),
    ), patch(
        "app.services.recommend._search_tavily",
        new=AsyncMock(side_effect=AIProcessingError(
            code="search_failed",
            message="Tavily 실패",
        )),
    ):
        response = client.post(
            "/ai/recommend/github-stars",
            json={"github_username": "octocat", "limit": 5},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "search_failed"


def test_query_generation_failure_returns_422() -> None:
    repositories = [
        {
            "name": "react",
            "description": "React library",
            "topics": ["react", "frontend"],
            "language": "TypeScript",
        }
    ]

    with patch(
        "app.services.recommend._fetch_starred_repositories",
        new=AsyncMock(return_value=repositories),
    ), patch(
        "app.services.recommend._generate_search_query",
        new=AsyncMock(side_effect=AIProcessingError(
            code="recommendation_failed",
            message="검색 질의 생성 실패",
        )),
    ), patch("app.services.recommend._search_tavily", new=AsyncMock()) as search_mock:
        response = client.post(
            "/ai/recommend/github-stars",
            json={"github_username": "octocat", "limit": 5},
        )

    assert response.status_code == 422
    assert response.json()["error"] == "recommendation_failed"
    search_mock.assert_not_called()


def test_low_quality_tavily_results_are_filtered() -> None:
    blocked_results = [
        {
            "url": "https://www.scribd.com/document/915339899/Backend-Interview-Guide",
            "title": "Backend Interview Guide",
        },
        {
            "url": "https://codesignal.com/learn/paths/four-week-coding-interview-prep-in-java",
            "title": "Coding interview prep in Java",
        },
        {
            "url": "https://www.amazon.com/Backend-Java-Interview-Questions-Complete/dp/B0GS3P364H",
            "title": "Backend Java Interview Questions",
        },
        {
            "url": "https://www.techinterviewhandbook.org/algorithms/study-cheatsheet/",
            "title": "Algorithms study cheatsheet",
        },
        {
            "url": "https://medium.com/@author/java-backend-development-roadmap",
            "title": "Java backend development roadmap",
        },
        {
            "url": "https://blog.stackademic.com/java-backend-roadmap",
            "title": "Java backend roadmap",
        },
        {
            "url": "https://www.linkedin.com/posts/user_must-know-backend-engineering-topics",
            "title": "Must know backend engineering topics",
        },
        {
            "url": "https://example.com/java-backend-complete-guide",
            "title": "Java backend complete guide for beginners",
        },
        {
            "url": "https://www.almabetter.com/bytes/articles/backend-technologies",
            "title": "Backend technologies",
        },
        {
            "url": "https://github.com/zhashkevych/awesome-backend",
            "title": "Awesome Backend",
        },
        {
            "url": "https://flatironschool.com/blog/what-is-software-engineering-front-end-vs-back-end-explained/",
            "title": "What is software engineering? Front-end vs Back-end explained",
        },
        {
            "url": "https://www.reddit.com/r/ExperiencedDevs/comments/1jgod64/example/",
            "title": "Experienced devs discussion",
        },
    ]
    allowed_result = {
        "url": "https://docs.spring.io/spring-framework/reference/web.html",
        "title": "Spring Framework Web Documentation",
    }

    assert [_is_recommendable_result(item) for item in [*blocked_results, allowed_result]] == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        True,
    ]


def test_recommendation_results_prioritize_authoritative_sources() -> None:
    results = [
        {
            "url": "https://example.com/backend-patterns",
            "title": "Backend patterns",
        },
        {
            "url": "https://docs.spring.io/spring-framework/reference/web.html",
            "title": "Spring Framework Web Documentation",
        },
        {
            "url": "https://martinfowler.com/articles/microservices.html",
            "title": "Microservices architecture article",
        },
    ]

    assert _rank_recommendation_results(results) == [
        "https://docs.spring.io/spring-framework/reference/web.html",
        "https://martinfowler.com/articles/microservices.html",
        "https://example.com/backend-patterns",
    ]


@pytest.mark.asyncio
async def test_tavily_search_requests_wider_candidate_pool(monkeypatch) -> None:
    captured_payload = {}

    class FakeResponse:
        status_code = 200

        def json(self) -> dict:
            return {
                "results": [
                    {
                        "url": "https://docs.spring.io/spring-framework/reference/web.html",
                        "title": "Spring Framework Web Documentation",
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, timeout: float):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return False

        async def post(self, url: str, json: dict):
            captured_payload.update(json)
            return FakeResponse()

    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setattr("app.services.recommend.httpx.AsyncClient", FakeAsyncClient)

    urls = await _search_tavily("spring backend architecture best practices", limit=5)

    assert urls == ["https://docs.spring.io/spring-framework/reference/web.html"]
    assert captured_payload["max_results"] == 20
    assert "reddit.com" in captured_payload["exclude_domains"]
