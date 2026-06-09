from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ROC operating points: (suspicious_threshold, dangerous_threshold)
PROFILES = {
    "max_protection":   (25, 60),   # high sensitivity — catch more, more false positives
    "balanced":         (40, 80),   # default — F1 optimized
    "min_disturbance":  (55, 90),   # high specificity — fewer alerts, may miss some
}


@dataclass
class AppConfig:
    suspicious_threshold_score: int = 40
    dangerous_threshold_score: int = 80
    high_contrast_enabled: bool = True

    # Module 1 - Google Safe Browsing Lookup API v4
    safe_browsing_api_key: str | None = os.getenv("SAFE_BROWSING_API_KEY")

    # Module 2 - LLM semantic agent (OpenAI-compatible API)
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @classmethod
    def with_profile(cls, profile: str) -> "AppConfig":
        suspicious, dangerous = PROFILES.get(profile, PROFILES["balanced"])
        return cls(suspicious_threshold_score=suspicious, dangerous_threshold_score=dangerous)
