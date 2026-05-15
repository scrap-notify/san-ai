import logging
import re
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.exceptions import AIProcessingError, ContentValidationError, ResourceNotFoundError
from app.llms import LLMClient
from app.prompts.recommend import get_github_stars_search_query_prompt
from app.schemas.recommend import (
    GitHubStarsRecommendRequest,
    GitHubStarsRecommendResponse,
    RecommendationItem,
)

_DEFAULT_RECOMMENDATION_URLS = [
    "https://docs.github.com/en/actions",
    "https://docs.docker.com/get-started/overview/",
    "https://fastapi.tiangolo.com/tutorial/first-steps/",
    "https://react.dev/learn",
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
    "https://kubernetes.io/docs/concepts/overview/",
    "https://docs.python.org/3/tutorial/",
    "https://martinfowler.com/articles/microservices.html",
    "https://www.baeldung.com/cs/clean-architecture",
    "https://git-scm.com/book/en/v2",
]

_MAX_LIMIT = 10
_STAR_FETCH_LIMIT = 30
_QUERY_REPOSITORY_LIMIT = 20
_BLOCKED_RESULT_DOMAINS = {
    "almabetter.com",
    "amazon.com",
    "codingblocks.com",
    "codesignal.com",
    "coursera.org",
    "flatironschool.com",
    "linkedin.com",
    "medium.com",
    "reddit.com",
    "scribd.com",
    "stackademic.com",
    "udemy.com",
}
_PREFERRED_RESULT_DOMAINS = {
    "aws.amazon.com",
    "baeldung.com",
    "cloud.google.com",
    "developer.mozilla.org",
    "docs.docker.com",
    "docs.github.com",
    "docs.oracle.com",
    "docs.python.org",
    "docs.spring.io",
    "fastapi.tiangolo.com",
    "github.blog",
    "infoq.com",
    "kubernetes.io",
    "martinfowler.com",
    "netflixtechblog.com",
    "react.dev",
    "spring.io",
}
_BLOCKED_RESULT_TERMS = {
    "awesome",
    "beginner",
    "book",
    "bootcamp",
    "certification",
    "cheat sheet",
    "cheatsheet",
    "coding interview",
    "coding test",
    "complete guide",
    "course",
    "exam",
    "for beginners",
    "front-end vs back-end",
    "front end vs back end",
    "frontend vs backend",
    "fundamentals of software development",
    "interview",
    "leetcode",
    "prep",
    "questions",
    "roadmap",
    "what is",
    "zero to hero",
}
_PREFERRED_RESULT_TERMS = {
    "architecture",
    "best practices",
    "case study",
    "documentation",
    "engineering blog",
    "performance",
    "reference",
}
logger = logging.getLogger(__name__)


def _validate_request(request: GitHubStarsRecommendRequest) -> tuple[str, int]:
    username = request.github_username.strip()
    if not username:
        raise ContentValidationError(
            code="missing_github_username",
            message="github_username 필드는 비어있을 수 없습니다.",
        )

    if request.limit < 1 or request.limit > _MAX_LIMIT:
        raise ContentValidationError(
            code="invalid_limit",
            message=f"limit은 1 이상 {_MAX_LIMIT} 이하의 정수여야 합니다.",
        )

    return username, request.limit


def _github_headers(token: str | None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _fetch_starred_repositories(username: str) -> list[dict]:
    settings = get_settings()
    url = f"{settings.github_api_base_url.rstrip('/')}/users/{username}/starred"
    params = {"per_page": _STAR_FETCH_LIMIT, "sort": "created", "direction": "desc"}

    try:
        async with httpx.AsyncClient(timeout=settings.github_timeout) as client:
            response = await client.get(
                url,
                headers=_github_headers(settings.github_api_token),
                params=params,
            )
    except httpx.HTTPError as exc:
        raise AIProcessingError(code="github_fetch_failed", message=str(exc)) from exc

    if response.status_code == 404:
        raise ResourceNotFoundError(
            code="github_user_not_found",
            message="GitHub 사용자를 찾을 수 없습니다.",
        )
    if response.status_code >= 400:
        raise AIProcessingError(
            code="github_fetch_failed",
            message=f"GitHub Star 목록 조회 실패: status={response.status_code}",
        )

    data = response.json()
    if not isinstance(data, list):
        raise AIProcessingError(
            code="github_fetch_failed",
            message="GitHub Star 목록 응답 형식이 올바르지 않습니다.",
        )
    return data


def _format_repository_context(repositories: list[dict]) -> str:
    lines = []
    for index, repo in enumerate(repositories[:_QUERY_REPOSITORY_LIMIT], start=1):
        topics = repo.get("topics") or []
        if isinstance(topics, list):
            topic_text = ", ".join(str(topic) for topic in topics[:8] if topic)
        else:
            topic_text = ""

        lines.append(
            "\n".join([
                f"{index}. name: {repo.get('full_name') or repo.get('name') or 'unknown'}",
                f"   description: {repo.get('description') or ''}",
                f"   topics: {topic_text}",
                f"   language: {repo.get('language') or ''}",
            ])
        )
    return "\n".join(lines)


async def _generate_search_query(repositories: list[dict]) -> str:
    repository_context = _format_repository_context(repositories)
    if not repository_context.strip():
        raise AIProcessingError(
            code="recommendation_failed",
            message="GitHub Star 목록에서 추천 검색어를 만들 수 없습니다.",
        )

    prompt = get_github_stars_search_query_prompt(repository_context)
    result = await LLMClient().acall_json(prompt=prompt, error_code="recommendation_failed")
    query = result.get("query")
    if not isinstance(query, str) or not query.strip():
        raise AIProcessingError(
            code="recommendation_failed",
            message="LLM 응답에 유효한 query 필드가 없습니다.",
        )

    return " ".join(query.split())


async def _search_tavily(query: str, limit: int) -> list[str]:
    settings = get_settings()
    if not settings.tavily_api_key:
        raise AIProcessingError(
            code="search_failed",
            message="TAVILY_API_KEY가 설정되어 있지 않습니다.",
        )

    logger.debug("tavily search query: %s", query)

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": min(limit * 2, 20),
        "include_answer": False,
        "include_raw_content": False,
        "exclude_domains": sorted(_BLOCKED_RESULT_DOMAINS),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.tavily_timeout) as client:
            response = await client.post(settings.tavily_api_url, json=payload)
    except httpx.HTTPError as exc:
        raise AIProcessingError(code="search_failed", message=str(exc)) from exc

    if response.status_code >= 400:
        raise AIProcessingError(
            code="search_failed",
            message=f"Tavily 검색 처리 실패: status={response.status_code}",
        )

    data = response.json()
    results = data.get("results")
    if not isinstance(results, list):
        raise AIProcessingError(
            code="search_failed",
            message="Tavily 검색 응답 형식이 올바르지 않습니다.",
        )

    return _rank_recommendation_results(results)


def _is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_blocked_domain(hostname: str) -> bool:
    hostname = hostname.lower().removeprefix("www.")
    if hostname in _PREFERRED_RESULT_DOMAINS:
        return False
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in _BLOCKED_RESULT_DOMAINS)


def _is_preferred_domain(hostname: str) -> bool:
    hostname = hostname.lower().removeprefix("www.")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in _PREFERRED_RESULT_DOMAINS)


def _is_recommendable_result(item: dict) -> bool:
    url = item.get("url")
    if not _is_http_url(url):
        return False

    parsed = urlparse(str(url))
    if parsed.hostname and _is_blocked_domain(parsed.hostname):
        logger.debug("filtered recommendation domain: %s", url)
        return False

    searchable_text = " ".join(
        str(item.get(field) or "").lower()
        for field in ("url", "title", "content", "snippet")
    )
    if _contains_blocked_term(searchable_text):
        logger.debug("filtered recommendation term: %s", url)
        return False

    return True


def _contains_blocked_term(text: str) -> bool:
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text)
        for term in _BLOCKED_RESULT_TERMS
    )


def _result_quality_score(item: dict) -> int:
    score = 0
    parsed = urlparse(str(item.get("url")))
    if parsed.hostname and _is_preferred_domain(parsed.hostname):
        score += 3

    searchable_text = " ".join(
        str(item.get(field) or "").lower()
        for field in ("url", "title", "content", "snippet")
    )
    score += sum(1 for term in _PREFERRED_RESULT_TERMS if term in searchable_text)
    return score


def _rank_recommendation_results(results: list) -> list[str]:
    scored_results = [
        (index, _result_quality_score(item), item["url"])
        for index, item in enumerate(results)
        if isinstance(item, dict) and _is_recommendable_result(item)
    ]
    scored_results.sort(key=lambda result: (-result[1], result[0]))
    return [url for _, _, url in scored_results]


def _build_response(urls: list[str], limit: int) -> GitHubStarsRecommendResponse:
    deduped_urls = list(dict.fromkeys(urls + _DEFAULT_RECOMMENDATION_URLS))[:limit]
    return GitHubStarsRecommendResponse(
        recommendations=[
            RecommendationItem(input_type="url", content=url)
            for url in deduped_urls
        ]
    )


async def recommend_github_stars(
    request: GitHubStarsRecommendRequest,
) -> GitHubStarsRecommendResponse:
    username, limit = _validate_request(request)
    repositories = await _fetch_starred_repositories(username)

    if not repositories:
        return _build_response([], limit)

    query = await _generate_search_query(repositories)
    searched_urls = await _search_tavily(query, limit)
    return _build_response(searched_urls, limit)
