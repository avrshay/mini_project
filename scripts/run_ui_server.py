import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phishguard.agent import PhishGuardAgent
from phishguard.config import AppConfig
from phishguard.types import Channel, IncomingMessage


class AnalyzeRequest(BaseModel):
    text: str


app = FastAPI(title="PhishGuard UI Server")
agent: PhishGuardAgent | None = None


@app.on_event("startup")
def startup_event() -> None:
    global agent
    agent = PhishGuardAgent(AppConfig())
    agent.boot()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(PROJECT_ROOT / "web" / "index.html")


@app.post("/analyze")
async def analyze(payload: AnalyzeRequest) -> dict:
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message text is required")

    assessment = await agent.on_message(
        IncomingMessage(sender="משתמש", channel=Channel.WHATSAPP, text=text)
    )
    return {
        "tier": assessment.tier.value,
        "confidence": round(assessment.confidence, 4),
        "final_score": assessment.final_score,
        "explanation": assessment.explanation,
        "reasons": assessment.reasons[:6],
        "module1_blocking_score": assessment.module1_blocking_score,
        "module2_s_ai": assessment.module2_s_ai,
        "skipped_module2": assessment.skipped_module2,
    }


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
