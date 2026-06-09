"""
Module 2 - Rules-Based Semantic Analysis Engine (LLM Agent).

Input: raw message text.
Output: structured JSON with S_AI [0,100] and Hebrew explanation.
"""

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
from pydantic import BaseModel, Field, ValidationError

from phishguard.config import AppConfig

logger = logging.getLogger(__name__)

# strip ```json ... ``` fences some models add despite response_format
_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


class SemanticAgentJSON(BaseModel):
    S_AI: int = Field(ge=0, le=100)
    explanation_he: str
    analysis_steps: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class SemanticAgentResult:
    s_ai: int
    explanation_he: str
    analysis_steps: list[str]
    engine: str  # "llm"


class SemanticAgentError(RuntimeError):
    """Raised when the LLM call or its JSON output cannot be used."""


class LLMSemanticAgent:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        prompt_path = Path(__file__).resolve().parent / "prompts" / "semantic_agent_system.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def analyze(self, text: str) -> SemanticAgentResult:
        if not self.config.openai_api_key:
            raise SemanticAgentError(
                "OPENAI_API_KEY לא מוגדר. הוסיפי את המפתח לקובץ .env והפעילי מחדש את השרת."
            )
        if not text or not text.strip():
            raise SemanticAgentError("ההודעה ריקה — אין מה לנתח.")

        # one retry if the model returns malformed JSON
        last_err: Exception | None = None
        for attempt in (1, 2):
            try:
                return await self._analyze_with_llm(text, strict=(attempt == 2))
            except (ValidationError, json.JSONDecodeError) as e:
                last_err = e
                logger.warning("Module 2: invalid JSON from LLM (attempt %s): %s", attempt, e)
        raise SemanticAgentError(f"מודול 2 החזיר פלט לא תקין: {last_err}")

    async def _analyze_with_llm(self, text: str, strict: bool) -> SemanticAgentResult:
        user_msg = (
            "נתח את ההודעה הבאה. החזר JSON בלבד לפי הסכמה, ללא טקסט נוסף וללא ```.\n\n"
            f"הודעה:\n{text}"
        )
        if strict:
            user_msg += "\n\nשים לב: בניסיון הקודם החזרת פלט לא תקין. החזר JSON חוקי בלבד."

        payload = {
            "model": self.config.openai_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_msg},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.config.openai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as e:
            raise SemanticAgentError("פסק זמן בפנייה ל-LLM (יותר מ-30 שניות).") from e
        except httpx.HTTPStatusError as e:
            raise SemanticAgentError(
                f"שגיאת HTTP מ-LLM: {e.response.status_code} {e.response.text[:200]}"
            ) from e
        except httpx.HTTPError as e:
            raise SemanticAgentError(f"שגיאת רשת בפנייה ל-LLM: {e}") from e

        content = data["choices"][0]["message"]["content"]
        cleaned = _FENCE_RE.sub("", content).strip()
        parsed = SemanticAgentJSON.model_validate_json(cleaned)

        # defensive clamp (Pydantic already validates range, but explicit is safer)
        s_ai = max(0, min(100, int(parsed.S_AI)))

        return SemanticAgentResult(
            s_ai=s_ai,
            explanation_he=parsed.explanation_he.strip(),
            analysis_steps=[s.strip() for s in parsed.analysis_steps if s and s.strip()],
            engine="llm",
        )
