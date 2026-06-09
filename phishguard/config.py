from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class AppConfig:
    model_path: Path = Path("models/phishguard_model.joblib")
    suspicious_threshold_score: int = 40
    dangerous_threshold_score: int = 80
    high_contrast_enabled: bool = True

    # Module 1 - Google Safe Browsing Lookup API v4
    safe_browsing_api_key: str | None = os.getenv("SAFE_BROWSING_API_KEY")

    # Module 2 - LLM semantic agent (OpenAI-compatible API)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
