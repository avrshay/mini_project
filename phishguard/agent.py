from phishguard.alerts import AccessibleAlertManager
from phishguard.config import AppConfig
from phishguard.domain_verification import DomainVerificationEngine
from phishguard.ml import MLClassifier
from phishguard.preprocess import extract_urls
from phishguard.risk import RiskFusionEngine
from phishguard.semantic_agent import LLMSemanticAgent
from phishguard.types import IncomingMessage, RiskAssessment, RiskTier


class PhishGuardAgent:
    """
    Orchestrator:
    1) Pre-process URLs
    2) Module 1 - Domain verification (0/100). Hard override on 100.
    3) Module 2 - LLM semantic agent (S_AI + explanation), only if Module 1 == 0
    4) Map to accessible risk output
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.ml_engine = MLClassifier(config.model_path)
        self.module1 = DomainVerificationEngine(config)
        self.module2 = LLMSemanticAgent(config, self.ml_engine)
        self.risk_engine = RiskFusionEngine(config)
        self.alert_manager = AccessibleAlertManager(
            high_contrast=config.high_contrast_enabled
        )

    def boot(self) -> None:
        self.ml_engine.load()
        print("PhishGuard agent ready (Module 1 + Module 2 pipeline).")

    async def on_message(self, message: IncomingMessage) -> RiskAssessment:
        urls = extract_urls(message.text)

        # Module 1
        domain_result = await self.module1.verify_urls(urls)
        if domain_result.blocking_score == 100:
            assessment = self.risk_engine.from_hard_override(domain_result)
            self._maybe_alert(message, assessment)
            return assessment

        # Module 2 (skipped when Module 1 hard-blocks)
        semantic_result = await self.module2.analyze(message.text)
        assessment = self.risk_engine.from_semantic(domain_result, semantic_result)
        self._maybe_alert(message, assessment)
        return assessment

    def _maybe_alert(self, message: IncomingMessage, assessment: RiskAssessment) -> None:
        if assessment.tier in (RiskTier.SUSPICIOUS, RiskTier.DANGEROUS):
            self.alert_manager.notify(message, assessment)
