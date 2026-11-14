"""RECONSTRUCT/EXPLAIN · Rule Dependency Atlas (outputs/evidence/atlas.json).

Nodes = dataset fields and latent generator entities. Edges = reconstructed generation dependencies, each typed and linked to
the rule(s) and the evidence that support it. Edge kinds (visual semantics):
  deterministic  – field computed exactly from another (exact-match validated)
  stochastic     – validated probabilistic dependency (parameter + split replication)
  independent    – TESTED non-edge (conditional-independence / effect size below threshold)
  confounded     – association that disappears once a common driver (bank / country) is held fixed
  unresolved     – dependency established but mechanism not identified
No edge asserts causal identification; 'X → Y' means 'the data are consistent with Y being generated from X'.
Run: python -m src.atlas
"""
from __future__ import annotations
import json
from .config import EVIDENCE

V = {r["id"]: r for r in json.loads((EVIDENCE / "validation.json").read_text())["rules"]}
FO = json.loads((EVIDENCE / "forensics.json").read_text())
GR = json.loads((EVIDENCE / "graph.json").read_text())
civ = {(t["x"], t["y"]): t["cramers_v"] for t in FO["ci_tests"]}

NODES = [  # id, label, field/latent, x, y  (layout follows the reconstructed generation order, left → right)
    ("size", "Bank size", "latent", 60, 70), ("calendar", "Calendar levels", "latent", 60, 420),
    ("sbank", "ORDERING_BIC8", "field", 230, 140), ("rbank", "BENEFICIARY_BIC8", "field", 230, 300),
    ("otype", "ORDERING_TYPE", "field", 420, 40), ("btype", "BENEFICIARY_TYPE", "field", 420, 360),
    ("ibank", "Instructing bank", "latent", 420, 140), ("inter", "Intermediaries", "latent", 420, 230),
    ("path", "BIC8_PATH", "field", 610, 190), ("time", "EPOCH_SECONDS", "field", 610, 420),
    ("pc", "PARTICIPANT_COUNT", "field", 800, 110), ("cont", "CONTINUITY_QFLAG", "field", 800, 30),
    ("fx", "CURRENCY_CONVERSION_COUNT", "field", 800, 200), ("cur", "CURRENCY_CODE", "field", 800, 290),
    ("ttype", "TRANSACTION_TYPE_CODE", "field", 990, 110), ("dur", "TOTAL_DURATION", "field", 990, 230),
    ("amt", "USD_AMOUNT", "field", 990, 360), ("anom", "ANOMALY_TYPE", "field", 1180, 400),
    ("acct", "ACCOUNTS (IBAN/local)", "field", 230, 470), ("text", "DETAILS / TOKENS", "field", 420, 500),
    ("bcust", "Beneficiary address country", "field", 610, 520),
]

f = lambda x, d=3: f"{x:.{d}f}" if isinstance(x, float) else str(x)
m = lambda rid: V[rid]["metrics"].get("full", {})
EDGES = [  # source, target, kind, rules, evidence
    ("size", "inter", "stochastic", ["G3", "R3"], f"P ∝ size^β, β = {f(m('G3')['beta'], 2)}; loop rate error {f(m('G3')['max_rel_err'] * 100, 1)}%"),
    ("sbank", "ibank", "stochastic", ["R5", "R5b"], f"replaced w.p. {f(m('R5')['p_first'], 4)} (independent of other end)"),
    ("rbank", "path", "stochastic", ["R5"], f"last hop ≠ BENEFICIARY_BIC8 w.p. {f(m('R5')['p_last'], 4)}"),
    ("ibank", "path", "deterministic", ["R5b"], "path starts at the instructing bank"),
    ("inter", "path", "stochastic", ["R1", "G3"], "K = ⌊Exp(1)⌋ intermediaries inserted"),
    ("path", "pc", "deterministic", ["R6"], f"pc = known BICs (exact {f(m('R6')['share_exact'], 6)})"),
    ("path", "cont", "deterministic", ["R7"], "N ⇔ '...' present (exact); each link hidden w.p. 0.05 (R4)"),
    ("path", "fx", "deterministic", ["C2"], f"FX = currency borders, exceptions {int(m('C2')['exceptions'])} of 10M"),
    ("pc", "ttype", "deterministic", ["R1"], "Direct ⇔ pc = 2"),
    ("sbank", "ttype", "stochastic", ["R2"], f"cover banks {f(m('R2')['oos_cover_banks_share'] * 100, 0)}% Covered vs {f(m('R2')['oos_other_banks_share'] * 100, 1)}% (out of sample)"),
    ("path", "cur", "stochastic", ["C3"], f"{f(m('C3')['in_route_share'] * 100, 1)}% in a route currency; +{f(m('C3')['intermediary_slope_per_hop'] * 100, 1)} pts per intermediary"),
    ("ibank", "cur", "stochastic", ["C1", "C3"], f"home currency of instructing bank {f(m('C1')['home_share'] * 100, 1)}%"),
    ("ibank", "time", "stochastic", ["T1"], f"local office clock; night share {f(m('T1')['night_local'] * 100, 1)}% local vs {f(m('T1')['night_utc'] * 100, 1)}% UTC"),
    ("calendar", "time", "stochastic", ["T3", "T4", "T4b"], f"weekly steps, {m('T4b')['change_points']} change points all on Monday"),
    ("otype", "amt", "stochastic", ["A1"], f"+{f(m('A1')['effect_ordering_B'], 2)} ln units if business"),
    ("btype", "amt", "stochastic", ["A1"], f"+{f(m('A1')['effect_beneficiary_B'], 2)} ln units if business"),
    ("sbank", "amt", "stochastic", ["A2"], f"country level, split-half r = {f(m('A2')['split_half_corr'], 4)}"),
    ("sbank", "otype", "stochastic", ["P5"], f"bank customer mix, split-half r = {f(m('P5')['sender_split_half_r'], 3)}"),
    ("rbank", "btype", "stochastic", ["P5"], f"bank customer mix, split-half r = {f(m('P5')['receiver_split_half_r'], 3)}"),
    ("sbank", "dur", "stochastic", ["D1", "D3"], "bank STP rate; manual step ~ Gamma(2, ~817 s)"),
    ("rbank", "dur", "stochastic", ["D1"], f"additive per bank, ratio {f(m('D1')['value'] if 'value' in m('D1') else V['D1']['metrics']['additivity_ratio']['value'], 2)} out of sample"),
    ("inter", "dur", "stochastic", ["D1"], "each intermediary adds a fast or manual step"),
    ("sbank", "acct", "deterministic", ["P2"], "IBAN prefix = BIC country (100%); IBAN only in IBAN countries"),
    ("otype", "text", "deterministic", ["P1b"], "business vs person token grammar, never mixed"),
    ("otype", "anom", "stochastic", ["X1", "X4"], "ROMANCE: sender C 100%; CEO: sender B 100%"),
    ("anom", "amt", "stochastic", ["X1", "X3"], "romance ×1.5 per step; fat finger ×100 / ÷100"),
    ("anom", "rbank", "stochastic", ["X4"], "CEO / account-replacement → mule accounts at small banks"),
    ("sbank", "rbank", "unresolved", ["G1"], f"pairing not independent: χ²/dof {f(m('G1')['chi2_dof_raw'], 0)}; mechanism open"),
    ("calendar", "calendar", "unresolved", ["T4"], "why these weekly levels — not identified"),
    # tested non-edges
    ("rbank", "bcust", "independent", ["P4"], f"address country = bank country only {f(m('P4')['b_match'] * 100, 2)}%"),
    ("otype", "btype", "independent", ["P1b"], f"|ΔP(B)| = {f(m('P1b')['diff'], 4)}"),
    ("anom", "ttype", "independent", ["X6"], f"Cramér's V = {f(m('X6')['cramers_v'], 4)}"),
    ("time", "dur", "independent", ["D2"], f"hour effect {f(m('D2')['fe_range_by_hour'], 3)} after bank fixed effects"),
    ("otype", "ttype", "independent", ["R1"], f"Cramér's V = {f(civ[('routing type', 'sender type')], 4)}"),
    ("rbank", "amt", "independent", ["A2"], f"beneficiary-country effect sd {f(m('A2')['sd_beneficiary'], 2)} vs ordering {f(m('A2')['sd_ordering'], 2)}"),
    # confounded associations
    ("amt", "time", "confounded", ["A2", "T1"], f"V = {f(civ[('amount decade', 'UTC quarter-day')], 3)} via sending country (wealth level × time zone)"),
    ("amt", "dur", "confounded", ["A2", "D1"], f"V = {f(civ[('amount decade', 'manual step')], 3)} via sending bank (bank effects on both)"),
]
EDGES = [e for e in EDGES if not (e[0] == e[1])] + [("calendar", "time", "unresolved", ["T4"], "cause of the weekly step levels not identified")]

out = dict(
    nodes=[dict(id=a, label=b, kind=c, x=x, y=y) for a, b, c, x, y in NODES],
    edges=[dict(source=s, target=t, kind=k, rules=r, evidence=e, status="/".join(sorted({V[i]["status"] for i in r if i in V})) or "n/a") for s, t, k, r, e in EDGES],
    legend={"deterministic": "exact, validated on all rows", "stochastic": "validated probabilistic dependency", "independent": "tested non-edge",
            "confounded": "association explained by a common driver", "unresolved": "dependency established, mechanism open"},
    note="Edges are generation dependencies consistent with the data, not causal identification.")
(EVIDENCE / "atlas.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
print(f"atlas: {len(out['nodes'])} nodes, {len(out['edges'])} edges", {k: sum(e['kind'] == k for e in out['edges']) for k in out['legend']})
