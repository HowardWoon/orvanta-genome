"""Cross-deliverable consistency: validation, register, registry, ledger, replay, PDFs, research report and website data agree."""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.mark.skipif(not (ROOT / "submission" / "ORVANTA_Comprehensive_Research_Report.md").exists(), reason="run python -m src.research_report")
def test_all_deliverables_agree():
    from consistency_check import check
    assert check() == []
