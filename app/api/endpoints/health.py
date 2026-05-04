from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="헬스체크",
    description="서버가 정상 동작 중인지 확인합니다.",
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}
