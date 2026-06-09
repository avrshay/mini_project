from phishguard.config import AppConfig
from phishguard.domain_verification import DomainVerificationEngine
from phishguard.preprocess import extract_urls
from phishguard.risk import RiskFusionEngine
from phishguard.semantic_agent import LLMSemanticAgent
from phishguard.types import IncomingMessage, RiskAssessment


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
        self.module1 = DomainVerificationEngine(config)
        self.module2 = LLMSemanticAgent(config)
        self.risk_engine = RiskFusionEngine(config)

    def boot(self) -> None:
        print("PhishGuard agent ready (Module 1 + Module 2 pipeline).")

    async def on_message(self, message: IncomingMessage) -> RiskAssessment:
        urls = extract_urls(message.text)

        # Module 1
        domain_result = await self.module1.verify_urls(urls)
        if domain_result.blocking_score == 100:
            return self.risk_engine.from_hard_override(domain_result)

        # Module 2 (skipped when Module 1 hard-blocks)
        semantic_result = await self.module2.analyze(message.text)
        return self.risk_engine.from_semantic(domain_result, semantic_result)
