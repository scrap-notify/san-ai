from fastapi import APIRouter

from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.preprocessor import preprocess

router = APIRouter(tags=["analyze"])

# /analyze 엔드포인트는 AnalyzeRequest를 입력받아 전처리를 수행한 후 AnalyzeResponse를 반환하는 POST 메서드입니다.
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    await preprocess(request.input_type, request.content)
    # 실제 분석 로직은 구현되지 않았으므로 NotImplementedError를 발생시킵니다. 추후에 LLM을 활용한 분석 로직이 이 부분에 추가될 예정입니다.
    raise NotImplementedError
