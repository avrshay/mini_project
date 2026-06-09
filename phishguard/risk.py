from phishguard.config import AppConfig
from phishguard.domain_verification import DomainVerificationResult
from phishguard.semantic_agent import SemanticAgentResult
from phishguard.types import RiskAssessment, RiskTier


class RiskFusionEngine:
    """
    Module C - accessible output mapping.
    Hard override when Module 1 blocking_score == 100.
    Otherwise final score comes from Module 2 S_AI.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def from_hard_override(
        self, domain_result: DomainVerificationResult
    ) -> RiskAssessment:
        reasons = [
            "מודול 1: נמצא קישור זדוני במסד Google Safe Browsing",
            *[f"קישור זדוני: {u}" for u in domain_result.matched_urls[:2]],
        ]
        return RiskAssessment(
            tier=RiskTier.DANGEROUS,
            confidence=1.0,
            final_score=100,
            explanation="זוהה קישור זדוני ידוע. ההודעה מסוכנת ויש למחוק אותה מיד.",
            reasons=reasons,
            module1_blocking_score=100,
            module2_s_ai=None,
            skipped_module2=True,
        )

    def from_semantic(
        self, domain_result: DomainVerificationResult, semantic: SemanticAgentResult
    ) -> RiskAssessment:
        final_score = semantic.s_ai
        tier = self._tier_from_score(final_score)
        reasons = list(semantic.analysis_steps[:4])
        reasons.append(f"מודול 2 (S_AI): {semantic.s_ai}/100")

        return RiskAssessment(
            tier=tier,
            confidence=final_score / 100.0,
            final_score=final_score,
            explanation=semantic.explanation_he,
            reasons=reasons,
            module1_blocking_score=domain_result.blocking_score,
            module2_s_ai=semantic.s_ai,
            skipped_module2=False,
        )

    def _tier_from_score(self, score: int) -> RiskTier:
        if score >= self.config.dangerous_threshold_score:
            return RiskTier.DANGEROUS
        if score >= self.config.suspicious_threshold_score:
            return RiskTier.SUSPICIOUS
        return RiskTier.SAFE
