"""Reference (pure-Python) implementations of the reconstructed generator rules.

These are deliberately independent of the DuckDB SQL in rules.py: the validation step
recomputes key rules both ways on a sample and asserts agreement (two-implementation check).
They also double as a minimal *generator* specification: another team could simulate the data from them.
"""
from __future__ import annotations
import math
from typing import Mapping, Sequence

GAP = "..."


def known_bics(path: str) -> list[str]:
    """BIC8s in a path, excluding '...' placeholders."""
    return [b for b in path.split(";") if b != GAP]


def bic_country(bic8: str) -> str:
    """ISO country = characters 5-6 of a BIC (BIC structure: 4 bank, 2 country, 2 location)."""
    return bic8[4:6]


def participant_count(path: str) -> int:
    """Rule R6: PARTICIPANT_COUNT = number of known BICs in BIC8_PATH."""
    return len(known_bics(path))


def continuity_flag(path: str) -> str:
    """Rule R7: CONTINUITY_QFLAG = 'N' iff the path contains a '...' placeholder."""
    return "N" if GAP in path.split(";") else "Y"


def fx_count(path: str, home_ccy: Mapping[str, str]) -> int:
    """Rule C2: conversions = adjacent known-BIC pairs whose home currencies differ."""
    cl = [home_ccy.get(bic_country(b)) for b in known_bics(path)]
    return sum(1 for a, b in zip(cl, cl[1:]) if a != b)


def hop_pmf(k: int, q: float = math.exp(-1)) -> float:
    """Rule R1: P(K=k intermediaries) = (1-q) q^k, q = 1/e  <=>  K = floor(Exp(1))."""
    return (1 - q) * q ** k


def p_gap(pc: int, p_link: float = 0.05) -> float:
    """Rule R4: P(path has >=1 '...') = 1 - (1-p)^(pc-1), p = 0.05 per link."""
    return 1 - (1 - p_link) ** (pc - 1)


def log_amount_mean(otype: str, btype: str, country_effect: float = 0.0) -> float:
    """Rule A1/A2: E[ln USD_AMOUNT] = 6 + 2*[O=B] + 2*[B=B] + country effect of the ordering country."""
    return 6.0 + 2.0 * (otype == "B") + 2.0 * (btype == "B") + country_effect


def is_iban_country_consistent(account: str, bic8: str) -> bool:
    """Rule P2: an IBAN-formatted account's country prefix equals its BIC country."""
    acc = account.replace("_FAKE_", "")
    return acc[:2] == bic_country(bic8)


def mt_4x35_ok(details: str) -> bool:
    """Rule P3: optional '/account' line + at most 4 body lines of at most 35 chars."""
    lines = details.split("\n")
    body = lines[1:] if lines and lines[0].startswith("/") else lines
    return len(body) <= 4 and all(len(x) <= 35 for x in body)


def romance_like(series: Sequence[tuple[int, float]], max_span: int = 4200, min_n: int = 3) -> bool:
    """Detector X1: >=3 payments, same consumer->beneficiary, within 70 min, amounts rising (corr>0.5)."""
    if len(series) < min_n:
        return False
    ts = [s[0] for s in series]
    if max(ts) - min(ts) > max_span:
        return False
    xs, ys = ts, [math.log(s[1]) for s in series]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxx > 0 and syy > 0 and sxy / math.sqrt(sxx * syy) > 0.5
