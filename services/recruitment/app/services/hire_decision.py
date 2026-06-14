"""
Hire decision service -- records hiring outcomes and checks justification for bias.
Human-in-the-loop: the system flags biased language; the manager retains final say.
"""
from shared.base.service import BaseService
from shared.bias_analyzer.bias_analyzer import BiasAnalyzer
from app.models import HireDecision

VALID_DECISIONS = frozenset({"hired", "rejected"})


class HireDecisionService(BaseService):
    """
    Records a hire/reject decision and runs a bias check on the written justification.
    Always uses rule-based analysis (no AI cost, deterministic, auditable).

    Args:
        bias_analyzer: injected BiasAnalyzer instance.
    """

    def __init__(self, bias_analyzer: BiasAnalyzer):
        self._bias_analyzer = bias_analyzer

    def record(self, candidate_id: int, decision: str, justification: str) -> HireDecision:
        """
        Validate and record a hiring decision.

        Args:
            candidate_id: ID of the candidate being decided on.
            decision: "hired" or "rejected".
            justification: written reason for the decision (checked for bias).

        Returns:
            HireDecision with bias_check populated.

        Raises:
            ValueError: if decision is invalid or justification is empty.
        """
        if not decision or decision not in VALID_DECISIONS:
            raise ValueError(
                f"decision must be one of {sorted(VALID_DECISIONS)}, got: '{decision}'"
            )
        if not justification or not justification.strip():
            raise ValueError("justification cannot be empty")

        bias_check = self._bias_analyzer.analyse_rule_based(justification)

        return HireDecision(
            candidate_id=candidate_id,
            decision=decision,
            justification=justification,
            bias_check=bias_check,
        )
