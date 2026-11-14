"""Six-level confidence scale shared by the PDFs (src.reporting) and the web platform (src.webdata).

Criteria are fixed in advance; a rule moves up only by passing a stronger test. The register's older High/Medium/Low label
is the input for rules that are neither in VALIDATED nor INCONCLUSIVE.
"""
from __future__ import annotations

ORDER = ["VALIDATED", "STRONGLY SUPPORTED", "SUPPORTED", "CANDIDATE", "INCONCLUSIVE", "REJECTED"]
CRITERIA = {
    "VALIDATED": "Deterministic rule reproducing its field exactly (≥ 99.999% of rows) on every split, or a parameter whose 95% CI contains the theoretical value and which passes on all 5 splits with an independent second implementation / out-of-sample test.",
    "STRONGLY SUPPORTED": "Validator passes on all 5 splits with a wide margin; mechanism specified explicitly; best alternative tested and rejected.",
    "SUPPORTED": "Validator passes, but part of the mechanism is inferred, thresholds are analyst-chosen, or the rule rests on one evidence line.",
    "CANDIDATE": "Pattern detected and replicated, mechanism not yet formulated as a testable rule.",
    "INCONCLUSIVE": "Dependence or effect established but the generating mechanism is not identified, or the result is a documented negative (no signature found).",
    "REJECTED": "Hypothesis tested and contradicted by the data (kept for transparency).",
}
VALIDATED = {"R6", "R7", "C2", "P2", "X2", "R1", "R4", "G3"}
INCONCLUSIVE = {"G1", "X5", "T4"}


def level(rule_id: str, confidence: str) -> str:
    if rule_id in VALIDATED:
        return "VALIDATED"
    if rule_id in INCONCLUSIVE:
        return "INCONCLUSIVE"
    return "STRONGLY SUPPORTED" if confidence == "High" else "SUPPORTED"
