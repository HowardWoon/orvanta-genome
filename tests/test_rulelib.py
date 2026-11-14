"""Unit tests for the reference rule implementations (no dataset needed)."""
import math
import pytest
from src import rulelib as R

HOME = {"US": "USD", "DE": "EUR", "FR": "EUR", "GB": "GBP", "JP": "JPY"}


def test_known_bics_skips_gaps():
    assert R.known_bics("0001US30;...;0002DEF0") == ["0001US30", "0002DEF0"]


@pytest.mark.parametrize("path,pc", [("0001US30;0002DEF0", 2), ("0001US30;...;...;0002DEF0", 2), ("A1B2US30;...;C3D4GB20;E5F6JPJ0", 3)])
def test_participant_count(path, pc):
    assert R.participant_count(path) == pc


@pytest.mark.parametrize("path,flag", [("0001US30;0002DEF0", "Y"), ("0001US30;...;0002DEF0", "N")])
def test_continuity_flag(path, flag):
    assert R.continuity_flag(path) == flag


@pytest.mark.parametrize("path,fx", [
    ("0001DEF0;0002FRP0", 0),                    # EUR -> EUR, no border
    ("0001DEF0;0002US30", 1),                    # EUR -> USD
    ("0001DEF0;0002US30;0003FRP0", 2),           # EUR -> USD -> EUR (two borders even though endpoints share EUR)
    ("0001DEF0;...;0002US30;0003US30", 1),       # gaps ignored; USD -> USD adds nothing
    ("0001GB20;0002JPJ0;0003US30;0004DEF0", 3),
])
def test_fx_count_counts_currency_borders(path, fx):
    assert R.fx_count(path, HOME) == fx


def test_hop_pmf_sums_to_one_and_has_ratio_inv_e():
    total = sum(R.hop_pmf(k) for k in range(200))
    assert abs(total - 1) < 1e-12
    assert abs(R.hop_pmf(3) / R.hop_pmf(2) - math.exp(-1)) < 1e-12
    assert abs(R.hop_pmf(0) - (1 - math.exp(-1))) < 1e-12


def test_p_gap_formula():
    assert R.p_gap(2) == pytest.approx(0.05)
    assert R.p_gap(3) == pytest.approx(1 - 0.95 ** 2)


def test_log_amount_lattice():
    assert R.log_amount_mean("C", "C") == 6
    assert R.log_amount_mean("B", "C") == R.log_amount_mean("C", "B") == 8
    assert R.log_amount_mean("B", "B") == 10


def test_iban_and_mt_layout():
    assert R.is_iban_country_consistent("_FAKE_DE25020100000000286854", "0201DEF0")
    assert not R.is_iban_country_consistent("_FAKE_DE25020100000000286854", "0201FRP0")
    assert R.mt_4x35_ok("/DE25\nACME GMBH\nHAUPTSTR 1\n10115 BERLIN DE")
    assert not R.mt_4x35_ok("/X\n" + "A" * 36)
    assert not R.mt_4x35_ok("/X\na\nb\nc\nd\ne")


def test_romance_detector():
    rising = [(0, 50.0), (200, 75.0), (500, 110.0), (900, 170.0)]
    assert R.romance_like(rising)
    assert not R.romance_like(rising[:2])                                   # too short
    assert not R.romance_like([(0, 50.0), (3000, 75.0), (9000, 110.0)])    # too slow
    assert not R.romance_like([(0, 170.0), (200, 110.0), (500, 75.0)])     # falling
