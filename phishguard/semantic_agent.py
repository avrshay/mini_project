"""
Module 2 - Rules-Based Semantic Analysis Engine (LLM Agent).

Input: raw message text.
Output: structured JSON with S_AI [0,100] and Hebrew explanation.
"""

from dataclasses import dataclass
from pathlib import Path

import httpx
from pydantic import BaseModel, Field

from phishguard.config import AppConfig
from phishguard.ml import MLClassifier


class SemanticAgentJSON(BaseModel):
    """Strict JSON schema enforced for Module 2 output."""

    S_AI: int = Field(ge=0, le=100)
    explanation_he: str
    analysis_steps: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class SemanticAgentResult:
    s_ai: int
    explanation_he: str
    analysis_steps: list[str]
    engine: str  # "llm" | "ml_fallback"


class LLMSemanticAgent:
    """
    Prompt-engineered LLM agent with:
    - semantic rules in system prompt
    - few-shot examples
    - chain-of-thought in analysis_steps
    - strict JSON schema output
    """

    def __init__(self, config: AppConfig, ml_classifier: MLClassifier) -> None:
        self.config = config
        self.ml_classifier = ml_classifier
        prompt_path = Path(__file__).resolve().parent / "prompts" / "semantic_agent_system.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def analyze(self, text: str) -> SemanticAgentResult:
        if self.config.openai_api_key:
            try:
                return await self._analyze_with_llm(text)
            except Exception:
                pass
        return self._analyze_with_ml_fallback(text)

    async def _analyze_with_llm(self, text: str) -> SemanticAgentResult:
        payload = {
            "model": self.config.openai_model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": (
                        "נתח את ההודעה הבאה. החזר JSON בלבד לפי הסכמה.\n\n"
                        f"הודעה:\n{text}"
                    ),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.config.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.config.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        parsed = SemanticAgentJSON.model_validate_json(content)
        return SemanticAgentResult(
            s_ai=parsed.S_AI,
            explanation_he=parsed.explanation_he,
            analysis_steps=parsed.analysis_steps,
            engine="llm",
        )

    def _analyze_with_ml_fallback(self, text: str) -> SemanticAgentResult:
        """
        Development fallback when no LLM API key is configured.
        Produces the same JSON fields using baseline ML probability only.
        """
        ml = self.ml_classifier.predict(text)
        s_ai = int(round(ml.phishing_probability * 100))

        if s_ai >= 80:
            explanation = "נראה שמדובר בניסיון הונאה. אל תלחץ על קישורים ואל תמסור פרטים."
        elif s_ai >= 40:
            explanation = "יש סימנים מחשידים. מומלץ לעצור ולבדוק מול מקור רשמי."
        else:
            explanation = "לא נמצאו סימני סכנה משמעותיים בהודעה זו."

        steps = [
            "שלב 1: זיהוי גורם מתחזה (דורש LLM מלא)",
            "שלב 2: ניתוח לחץ פסיכולוגי (דורש LLM מלא)",
            "שלב 3: בדיקת בקשה למידע רגיש (דורש LLM מלא)",
            f"שלב 4: ציון בסיס ML = {s_ai}",
        ]
        return SemanticAgentResult(
            s_ai=s_ai,
            explanation_he=explanation,
            analysis_steps=steps,
            engine="ml_fallback",
        )

    @staticmethod
    def parse_structured_output(raw_json: str) -> SemanticAgentResult:
        parsed = SemanticAgentJSON.model_validate_json(raw_json)
        return SemanticAgentResult(
            s_ai=parsed.S_AI,
            explanation_he=parsed.explanation_he,
            analysis_steps=parsed.analysis_steps,
            engine="llm",
        )
