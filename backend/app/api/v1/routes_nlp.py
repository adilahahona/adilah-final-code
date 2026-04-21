"""NLP ESG scoring endpoint using pre-trained text artifacts."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.domain.nlp.service import score_text

router = APIRouter(prefix="/api/v1/nlp", tags=["nlp"])


class ReportIn(BaseModel):
    text: str
    framework: str = "gri"


@router.post("/score")
async def score_report(body: ReportIn):
    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    result = score_text(body.text, framework=body.framework)
    return result
