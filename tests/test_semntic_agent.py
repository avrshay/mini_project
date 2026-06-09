import json
import pytest
import respx
from httpx import Response

from phishguard.config import AppConfig
from phishguard.semantic_agent import LLMSemanticAgent, SemanticAgentError


def _cfg() -> AppConfig:
    c = AppConfig()
    c.openai_api_key = "sk-test"
    c.openai_base_url = "https://api.openai.com/v1"
    c.openai_model = "gpt-4o-mini"
    return c


def _llm_response(payload: dict) -> Response:
    return Response(200, json={
        "choices": [{"message": {"content": json.dumps(payload, ensure_ascii=False)}}]
    })


@pytest.mark.asyncio
@respx.mock
async def test_phishing_high_score():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=_llm_response({
            "S_AI": 92,
            "explanation_he": "ההודעה דורשת פעולה דחופה ופרטים אישיים — סימן מובהק לפישינג.",
            "analysis_steps": ["התחזות לבנק", "לחץ דחיפות", "בקשת סיסמה", "S_AI=92"],
        })
    )
    agent = LLMSemanticAgent(_cfg())
    r = await agent.analyze("דחוף! חשבונך נחסם, הזן סיסמה כאן")
    assert r.s_ai == 92
    assert len(r.analysis_steps) == 4


@pytest.mark.asyncio
@respx.mock
async def test_legit_low_score():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=_llm_response({
            "S_AI": 10,
            "explanation_he": "תזכורת לתור רפואי, נראית שגרתית.",
            "analysis_steps": ["ללא התחזות", "ללא דחיפות", "ללא בקשת מידע", "S_AI=10"],
        })
    )
    agent = LLMSemanticAgent(_cfg())
    r = await agent.analyze("תזכורת: מחר יש לך תור לרופא בשעה 10:00")
    assert r.s_ai == 10


@pytest.mark.asyncio
@respx.mock
async def test_invalid_json_then_retry_succeeds():
    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        side_effect=[
            Response(200, json={"choices": [{"message": {"content": "not json at all"}}]}),
            _llm_response({"S_AI": 50, "explanation_he": "אפור.", "analysis_steps": ["x"]}),
        ]
    )
    agent = LLMSemanticAgent(_cfg())
    r = await agent.analyze("הודעה כלשהי")
    assert r.s_ai == 50
    assert route.call_count == 2


@pytest.mark.asyncio
async def test_missing_api_key_raises():
    cfg = AppConfig()
    cfg.openai_api_key = None
    with pytest.raises(SemanticAgentError, match="OPENAI_API_KEY"):
        await LLMSemanticAgent(cfg).analyze("טקסט")
