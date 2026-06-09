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
    engine: str  # "llm"


class LLMSemanticAgent:
    """
    Prompt-engineered LLM agent with:
    - semantic rules in system prompt
    - few-shot examples
    - chain-of-thought in analysis_steps
    - strict JSON schema output
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        prompt_path = Path(__file__).resolve().parent / "prompts" / "semantic_agent_system.txt"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")

    async def analyze(self, text: str) -> SemanticAgentResult:
        if not self.config.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY לא מוגדר. הוסיפי את המפתח לקובץ .env והפעילי מחדש את השרת."
            )
        return await self._analyze_with_llm(text)

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
