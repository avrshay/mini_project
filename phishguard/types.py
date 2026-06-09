from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Channel(str, Enum):
    SMS = "SMS"
    WHATSAPP = "WhatsApp"


class RiskTier(str, Enum):
    SAFE = "בטוח"
    SUSPICIOUS = "חשוד"
    DANGEROUS = "מסוכן"


@dataclass
class IncomingMessage:
    sender: str
    channel: Channel
    text: str
    received_at: datetime = field(default_factory=datetime.now)


@dataclass
class MLResult:
    phishing_probability: float
    predicted_label: int


@dataclass
class RiskAssessment:
    tier: RiskTier
    confidence: float
    final_score: int
    explanation: str
    reasons: list[str]
    module1_blocking_score: int
    module2_s_ai: int | None
    skipped_module2: bool
