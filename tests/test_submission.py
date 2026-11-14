"""Submission PDFs exist and respect official page limits (CS p2, RR 4.4)."""
from pathlib import Path
import pytest
from pypdf import PdfReader

SUB = Path(__file__).resolve().parents[1] / "submission"


@pytest.mark.skipif(not (SUB / "dashboard.pdf").exists(), reason="run src.reporting first")
def test_page_limits():
    assert 5 <= len(PdfReader(str(SUB / "dashboard.pdf")).pages) <= 15
    assert 10 <= len(PdfReader(str(SUB / "presentation.pdf")).pages) <= 20
