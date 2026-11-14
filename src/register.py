"""Generate findings/rule_evidence_register.md and findings/confirmed_rules.md.

Narrative fields are written by the analyst; every number is pulled from outputs/evidence/validation.json
at build time, so documents cannot drift from the validators.  Run: python -m src.register
"""
from __future__ import annotations
import json
from .config import EVIDENCE, FINDINGS
from .formulations import FORM, EFFECT_KEYS, N_KEYS

N = {  # id: (group, hypothesis/why, fields, method, counterexamples & exceptions, limitations, economic reading, chart, in deck?)
 "R6": ("Routing", "PARTICIPANT_COUNT is derived from the path, not drawn independently.", "PARTICIPANT_COUNT, BIC8_PATH",
        "Exact equality test on all rows; pure-Python re-implementation on 200k sample.", "None found.",
        "Says nothing about how many hops were hidden.", "Counts observed institutions only, i.e. what the messaging layer can see.", "pc vs path elements table", "Yes (method slide)"),
 "R7": ("Routing", "CONTINUITY_QFLAG encodes the presence of '...' placeholders.", "CONTINUITY_QFLAG, BIC8_PATH", "Exact equivalence test.", "None.",
        "Flag is an observability marker, not payment success/failure.", "A leg left the observed channel (e.g. a domestic clearing leg).", "-", "Yes"),
 "R5": ("Routing", "Header BICs and path endpoints can disagree; disagreement is random noise or a structural role split.", "ORDERING_BIC8, BENEFICIARY_BIC8, BIC8_PATH",
        "Mismatch rates per end, joint vs product (independence), stratified by type, pc, anomaly.", "ROMANCE_SCAM never swaps; CEO/ACCOUNT_REPLACEMENT never swap at the beneficiary end (mule bank is the true receiver).",
        "Cannot tell which institution is 'real' from one field alone; R5b resolves it with currency/clock/IBAN evidence.",
        "Ordering institution (account servicer, MT field 52) ≠ instructing agent that sends the message — common when a smaller bank uses a correspondent to send.", "2×2 mismatch table", "Yes"),
 "R5b": ("Routing / Currency", "On swapped rows, which BIC drives currency, timing and account format?", "CURRENCY_CODE, EPOCH_SECONDS, ORDERING_ACCOUNT, BIC8_PATH",
         "Compare home-currency match, local-night share and IBAN prefix against path[1] vs ORDERING_BIC8.", "Small share of non-home currency on both sides (vehicle currencies).",
         "Relies on our data-derived country→currency map.", "The instructing bank books and times the payment; the customer's account stays at the servicing bank.", "bar: match via path[1] vs header", "Yes"),
 "R1": ("Routing", "Number of intermediaries follows a simple distribution.", "PARTICIPANT_COUNT, TRANSACTION_TYPE_CODE",
        "Geometric MLE, successive ratios, chi-square GOF with Cohen's w, per split; per-bank Direct share vs binomial.", "None beyond sampling noise. Max pc = 22 is the far tail: the rule predicts 10M·e^-15 ≈ 3.1 rows with pc ≥ 17; 5 are observed (Poisson P(X≥5 | 3.1) ≈ 0.2).",
        "Correspondent choice is random in the generator; real networks depend on bilateral relationships.", "Each extra correspondent hop is a fixed-probability event; most payments have a direct relationship.", "observed vs predicted (log)", "Yes"),
 "R2": ("Routing", "How Covered vs Indirect is chosen among non-direct routes.", "TRANSACTION_TYPE_CODE, ORDERING_BIC8, PARTICIPANT_COUNT",
        "Share by K (Cramér's V); per-bank propensity with classes learned on half_0 and tested on half_1; within-country dispersion vs binomial.",
        "Original claim 'constant 11.3%' REJECTED by the discovery engine: share ranges 3–50% by sending country (IM 50%, SG 6%) and is 378× over-dispersed within countries — the parameter lives at bank level.",
        "Cover-bank class boundary (0.5) is analyst-chosen; cover share of a bank is not explained further.",
        "The cover method (MT103 direct + MT202 COV through correspondents) is a bank's operating choice — some institutions habitually settle by cover.", "bank-class bars", "Yes"),
 "R4": ("Routing", "Hidden hops arise per link with constant probability.", "CONTINUITY_QFLAG, PARTICIPANT_COUNT, BIC8_PATH", "Binomial-per-link model, MLE of p, max deviation per pc.",
        "Consecutive '...' chain geometrically (ratio ≈ 0.05).", "None material.", "Each inter-bank leg independently may run outside the observed network.", "obs vs formula", "Yes"),
 "R3": ("Routing", "Intermediaries are chosen by size (popularity), not by currency zone.", "BIC8_PATH, CURRENCY_CODE", "Correlation of log usage vs log sending volume; share in currency zone.",
        "Currency-zone hypothesis rejected (17% vs >50% expected under it).", "Size proxy is sending volume, itself endogenous.", "Large banks hold the most nostro accounts and act as hubs.", "scatter", "Dashboard"),
 "C2": ("Currency", "FX count is deterministic in the route.", "CURRENCY_CONVERSION_COUNT, BIC8_PATH", "Exact rule test on all rows; two rejected alternatives; pure-Python cross-check.",
        "2 rows, and they are the only 2 payments in the dataset that touch an Eritrean bank (0000ERA0, receiver). Eritrea never sends, so its home currency cannot be inferred and the rule's input is unobservable there; if ER's currency differs from the sender's, C2 predicts exactly the recorded 1 conversion. Scope: C2 holds wherever every route country has an observable home currency.", "Home currency per country is inferred from the data (modal currency).", "Each correspondent converts into the currency of its next nostro account; conversions happen at currency borders.", "pc × fx heatmap", "Yes"),
 "C3": ("Currency", "Where the payment currency comes from.", "CURRENCY_CODE, BIC8_PATH",
        "Currency matched against the home currencies of every bank on the path, by route length; per split on a 3M-row reservoir sample.",
        "1.27% of payments (126,857) use a currency of no route bank; 77.7% of them are EUR or USD. H38 (all 10M rows, 5 splits): on routes with no EUR or USD bank the payment is in EUR 1.41% and USD 0.75% of the time, stable across route length (pc 2–5) and splits (EUR 1.39–1.42%) — a route-independent vehicle draw that shows up as 'outside' only when that currency is not already on the route. Supported refinement, not a separate validated rule (the EUR/USD set was chosen after inspection).",
        "Direction (route first, then currency) is consistent with the data, not identified; the per-intermediary probability is approximate (linear fit).",
        "A payment is denominated in a currency some bank in the chain can book: the sender's (most), the receiver's, or a correspondent's clearing currency; otherwise a global vehicle currency.", "share by route position", "Yes"),
 "C1": ("Currency", "Payment currency is the instructing bank's home currency.", "CURRENCY_CODE, BIC8_PATH", "Share by split; per-country range.",
        "6.6% non-home (EUR, USD, GBP, CHF, CNY, SGD …); RU only 73% home.", "Vehicle-currency selection mechanism not fully identified.", "Local-currency funding; invoices in global vehicle currencies.", "stacked bars", "Yes"),
 "A1": ("Amount", "Log-amount mean is additive in party types.", "USD_AMOUNT, ORDERING_TYPE, BENEFICIARY_TYPE", "2×2 cell means → intercept, main effects, interaction; σ per cell; per split.",
        "Amount residual is slightly left-skewed (−0.12); 13.5% of fat-finger amounts are integers.", "Country and bank effects add structure on top (A2).", "Commercial flows ≫ personal flows; B2B largest.", "segment histograms", "Yes"),
 "A2": ("Amount", "Sending-country wealth level shifts amounts; beneficiary country does not.", "USD_AMOUNT, ORDERING_BIC8", "Country effects estimated separately on random halves; sd comparison.",
        "Effects are randomised by design (case text) — ranking is not real-world.", "Bank-level variance (0.22) not decomposed further.", "GDP-like scaling of ticket size at origin.", "diverging bars", "Yes"),
 "D1": ("Duration", "Duration is a sum of per-bank processing steps.", "TOTAL_DURATION, BIC8_PATH", "Bank speed classes learned on half_0, tested on half_1 (out-of-sample).",
        "~13% slow cases among fast-fast pairs (each 'fast' bank has a non-zero manual rate).", "Exact step distributions not fitted.", "STP vs manual repair/compliance review.", "bank-class medians", "Yes"),
 "D2": ("Duration", "Manual processing depends on bank, not on time or amount.", "TOTAL_DURATION, EPOCH_SECONDS, USD_AMOUNT", "Two-way bank fixed-effect demeaning; residual ranges by hour/weekday; corr with amount.",
        "Raw hour effect 0.037 is a Simpson artefact (bank mix across time zones).", "Linear-probability FE approximation.", "Automation level is an institution attribute.", "raw vs adjusted line", "Yes"),
 "T1": ("Time", "Timestamps are generated in the instructing bank's local time.", "EPOCH_SECONDS, BIC8_PATH", "Night-share comparison local vs UTC; offset estimation by profile alignment.",
        "Offsets are January values (no DST).", "Offsets estimated in whole hours (IN shows +5, true +5:30).", "Office-hours behaviour; cut-off driven submissions.", "local-hour line", "Yes"),
 "T3": ("Time", "Weekday shape is universal.", "EPOCH_SECONDS", "Max deviation of country weekday shares from pooled.", "Fri–Sat weekend hypothesis for Gulf/Israel rejected.", "-", "Sunday batch preparation > Saturday.", "weekday bars", "Yes"),
 "T4": ("Time", "Weekly volume level is global.", "EPOCH_SECONDS", "Correlation of country weekly series with total.", "Cause of levels unexplained.", "Only 13 full weeks.", "Possibly calendar-driven (month/quarter end).", "daily bars", "Yes"),
 "P2": ("Parties", "Account format follows the IBAN registry by country.", "ORDERING/BENEFICIARY_ACCOUNT, *_TOKENS", "Prefix match, per-country IBAN share bimodality.", "IBAN countries still use local formats ~8%.", "-", "Regulatory account-number standards.", "country bars", "Yes"),
 "P4": ("Parties", "Ordering parties live in their bank's country; beneficiaries do not.", "*_TOKENS country codes, BICs", "Match rates where country token present (61%).", "-",
        "39% of details carry no country token.", "Generator samples beneficiary residence by population, bank by banking size — a modelling shortcut.", "country comparison", "Yes"),
 "P5": ("Parties", "Why the business-customer share varies by country.", "ORDERING_TYPE, BENEFICIARY_TYPE, BICs",
        "Bank-level business share on each side, split-half correlation; within-country dispersion vs binomial.",
        "Country differences (38–96% senders) are bank mix; dispersion 549× (senders) and 196× (receivers) binomial within countries.",
        "Mechanism behind each bank's share (size? country?) not identified.", "Banks specialise: corporate banks vs retail banks serve different customer mixes.", "split-half scatter", "Dashboard"),
 "P1b": ("Parties", "Receiver type independent of sender type.", "ORDERING_TYPE, BENEFICIARY_TYPE", "Conditional shares by split.", "-", "-", "Independent sampling per side.", "-", "Dashboard"),
 "X1": ("Anomalies", "Romance scams are escalating consumer bursts.", "ANOMALY_TYPE, accounts, amounts, timestamps", "Series reconstruction, within-series log slope, detector precision/recall.",
        "Case text says C→C, but receiver type follows base mix (27% B).", "Timing (minutes apart) is unrealistic vs real grooming over weeks.", "Escalating repeated transfers by a groomed victim.", "escalation line", "Yes"),
 "X2": ("Anomalies", "Duplicates are message replays.", "all fields", "Exact-key grouping; detector over full data.", "5 normal groups and 10 romance groups also match the key.",
        "Labelling convention: every copy is labelled, including the original.", "Back-office race condition resends the same instruction.", "group sizes", "Yes"),
 "X3": ("Anomalies", "Fat-finger amounts are scaled by 10^±2.", "USD_AMOUNT", "Residual vs country+segment expectation, 2-component Gaussian mixture.",
        "Cannot separate ×100 from ×1000 per row (residual sd ≈ 0.9 log10).", "Expectation model has its own noise.", "Comma/dot decimal-separator confusion.", "residual histogram", "Yes"),
 "X4": ("Anomalies", "CEO/account-replacement scams target mule accounts.", "BENEFICIARY_ACCOUNT, BENEFICIARY_BIC8", "Share of beneficiary accounts that only receive anomalous money; bank size/STP comparison; stratified duration.",
        "No name-swap evidence for account replacement (1/649).", "Mule definition is data-driven.", "Fraud proceeds concentrate in mule accounts at weaker-control banks.", "mule share bars", "Yes"),
 "X5": ("Anomalies", "CUSTOMER_RECALL has a signature.", "all", "10 two-proportion z-tests + Mann-Whitney, Bonferroni.", "Path-gap share nominal p=0.024, not significant after correction.",
        "Label not documented in official materials.", "A recall happens after sending, so message fields cannot reveal it.", "test table", "Yes (negative result)"),
 "X6": ("Anomalies", "Anomaly label independent of routing type.", "ANOMALY_TYPE, TRANSACTION_TYPE_CODE", "Chi-square + Cramér's V.", "-", "-", "Anomalies injected after routing is generated.", "-", "Dashboard"),
 "F1": ("Fingerprints", "How amounts were produced: drawn in USD, or drawn in the payment currency and converted?", "USD_AMOUNT, CURRENCY_CODE",
        "Cents-digit distribution by currency; multiples of 100; search for a fixed FX rate that restores round originals (EUR/GBP/CHF).",
        "No single fixed rate restores round originals for EUR/GBP/CHF (best near-integer share ≈2% vs 1.2% baseline) — conversion mechanism not identified.",
        "Roundness of non-USD originals cannot be observed after conversion.", "Invoices are typically issued in round units of the invoicing currency; USD is the only currency that needs no conversion to USD.", "cents by currency", "Yes"),
 "T4b": ("Time", "Do weekly levels change at random times or at week boundaries?", "EPOCH_SECONDS",
        "Binary segmentation with BIC penalty on weekday-normalised log daily volume (91 full days); residual normality.",
        "Several adjacent weeks share a level (segments of 1–3 weeks).", "13 weeks only; cause of the levels still open (T4).", "Volume plans are set per week (business calendars), not per day.", "segmented series", "Yes"),
 "G3": ("Routing graph", "Loops in paths (a bank visited twice) are a by-product of independent size-weighted intermediary draws.", "BIC8_PATH",
        "Birthday-problem prediction from the intermediary collision probability Σp²; size exponent by log-log fit; per split.", "pc=8–9 within 3%; no residual excess of loops.",
        "Assumes the same size distribution at every position.", "Hubs appear repeatedly because the generator samples correspondents with replacement — real routes would avoid loops.", "obs vs predicted loop rate", "Yes"),
 "G1": ("Routing graph", "Sender and receiver banks are paired independently (configuration model).", "ORDERING_BIC8, BENEFICIARY_BIC8",
        "Pearson χ²/dof of pair counts vs product-of-margins expectation, on raw payments, unique account relationships and within country pairs; affinity symmetry.",
        "Independence REJECTED in all three; domestic pairs 1.2× expected; affinities directional (r = 0.11).", "Mechanism of the affinity (bank-level preference lists?) not identified.",
        "Real correspondent networks are relationship-driven; the generator encodes directional bank-to-bank preferences.", "pair O/E scatter", "Yes (partial result)"),
 "A3": ("Amount", "Amounts are lognormal, not heavy-tailed power law.", "USD_AMOUNT", "Within-country residual moments, KS vs Normal, Hill estimator drift, model-implied exceedances $100k–$1bn.",
        "Exceedance ratio 0.86 at $100M (132 vs 154 predicted, z≈−1.7).", "Fat-finger rows excluded; top 1,000 amounts are 26.5% fat finger.",
        "Payment sizes multiply many factors (firm size, invoice size) → lognormal; extreme tickets come from errors, not a fat natural tail.", "Q-Q / Hill plot", "Dashboard"),
 "D3": ("Duration", "The manual step has a specific distribution.", "TOTAL_DURATION", "Gamma vs lognormal MLE fits with KS on manual-step and fast-pair durations.",
        "Manual tail up to 21,649 s on multi-hop routes.", "Fitted on pc=2 rows with exactly one slow bank.", "Manual handling ≈ two exponential stages (queue + review) → Gamma(2).", "fitted density", "Dashboard"),
}

CONF = {  # confidence classification: High = deterministic/exact or tight effect-size pass with ≥2× margin and stable splits;
          # Medium = passes but mechanism partly inferred or thresholds analyst-chosen; Low = partial / negative / unexplained remainder
 "R6": "High", "R7": "High", "C2": "High", "P2": "High", "X2": "High", "R1": "High", "R2": "High", "P5": "High", "C3": "High", "F1": "High", "T4b": "High", "R4": "High", "A1": "High", "G3": "High",
 "R5": "High", "R5b": "Medium", "R3": "High", "C1": "Medium", "A2": "Medium", "A3": "High", "D1": "Medium", "D2": "Medium", "D3": "Medium",
 "T1": "High", "T3": "High", "T4": "Medium", "P4": "Medium", "P1b": "High", "X1": "High", "X3": "Medium", "X4": "Medium", "X5": "Low", "X6": "High", "G1": "Low",
}
LAYER = lambda g: {"Fingerprints": "Fingerprints", "Time": "Temporal", "Currency": "Currency & FX", "Routing": "Route", "Routing graph": "Route", "Routing / Currency": "Route", "Amount": "Value",
                   "Duration": "Processing", "Parties": "Parties & text", "Anomalies": "Anomaly"}[g]




def _num(x):
    """4 significant digits, except shares within 0.001 of 1 (exact-match rates), which keep 7 decimals so 0.9999998 is not shown as 1."""
    return f"{x:.7f}" if isinstance(x, float) and 0.999 < x < 1 else f"{x:.4g}"

def _find(m, keys):
    """first matching metric in the 'full' split (or any split / flat dict)."""
    pools = [m.get("full", {})] if isinstance(m, dict) else []
    pools += [v for v in m.values() if isinstance(v, dict)] if isinstance(m, dict) else []
    for k in keys:
        for pl in pools:
            if isinstance(pl, dict) and k in pl and isinstance(pl[k], (int, float)):
                return k, pl[k]
    return None, None


def facts(rid, r):
    m = r["metrics"]; nk, nv = _find(m, N_KEYS); ek, ev = _find(m, EFFECT_KEYS)
    splits = sorted(k for k, v in m.items() if isinstance(v, dict) and k in ("full", "half_0", "half_1", "P1", "P2")) if isinstance(m, dict) else []
    return dict(formulation=FORM[rid][0], logic=FORM[rid][1], sample_size=(f"{int(nv):,} ({nk})" if nv is not None else "10,000,000 (full data)"),
                effect_size=(f"{ek} = {_num(ev)}" if ev is not None else "see metrics"),
                validation=(f"{r['status']} on {len(splits)} splits ({', '.join(splits)})" if len(splits) > 1 else f"{r['status']} · full-data / out-of-sample test"))


def headline(r):
    m = r["metrics"]; f = m.get("full", m) if isinstance(m, dict) else {}
    keys = list(f)[:4] if isinstance(f, dict) else []
    return "; ".join(f"{k}={_num(f[k])}" if isinstance(f[k], (int, float)) else f"{k}={f[k]}" for k in keys)


def main():
    v = json.loads((EVIDENCE / "validation.json").read_text())
    R = {r["id"]: r for r in v["rules"]}
    L = ["# Rule evidence register", "", f"Built from validation run {v['generated']}. Status = validator outcome on all splits (full, random halves, two periods).", "",
         "| ID | Group | Type | Confidence | Rule | Headline evidence (full data) | Status | In deck |", "|---|---|---|---|---|---|---|---|"]
    for rid, n in N.items():
        r = R[rid]; L.append(f"| {rid} | {n[0]} | {r['type']} | {CONF[rid]} | {r['title']} | {headline(r)} | {r['status']} | {n[8]} |")
    L += ["", "## Entries", ""]
    for rid, n in N.items():
        r = R[rid]
        L += [f"### {rid} — {r['title']}", f"- **Hypothesis / why it matters:** {n[1]}", f"- **Fields:** {n[2]}", f"- **Sample size:** 10,000,000 rows (splits ≈5M each) unless stated",
              f"- **Explicit rule:** {FORM[rid][0]}", f"- **Logic:** `{FORM[rid][1]}`", f"- **Method:** {n[3]}", f"- **Acceptance criterion:** {r['criterion']}", f"- **Result:** {r['status']} — {headline(r)}", f"- **Confidence:** {CONF[rid]}",
              f"- **Counterexamples / exceptions:** {n[4]}", f"- **Limitations:** {n[5]}", f"- **Economic interpretation (interpretation, not proven by data):** {n[6]}",
              f"- **Visualisation:** {n[7]} · **Presentation:** {n[8]}", ""]
    (FINDINGS / "rule_evidence_register.md").write_text("\n".join(L), encoding="utf-8")
    C = ["# Confirmed rules", "", "Rules whose validator PASSES on every split. Confidence: High / Medium / Low (see register). G1 and X5 are confirmed *negative* findings.", ""]
    for rid, n in N.items():
        r = R[rid]
        if r["status"] == "PASS":
            C.append(f"- **{rid} ({n[0]}, type {r['type']}, confidence {CONF[rid]})** — {r['title']}. Evidence: {headline(r)}.")
    (FINDINGS / "confirmed_rules.md").write_text("\n".join(C), encoding="utf-8")
    keys = ["group", "hypothesis", "fields", "method", "counterexamples", "limitations", "economic", "chart", "deck"]
    out = [dict(id=rid, title=R[rid]["title"], type=R[rid]["type"], status=R[rid]["status"], criterion=R[rid]["criterion"], confidence=CONF[rid],
                layer=LAYER(n[0]), metrics=R[rid]["metrics"], **facts(rid, R[rid]), **dict(zip(keys, n))) for rid, n in N.items()]
    rep = EVIDENCE / "reports"; rep.mkdir(exist_ok=True)
    for o in out:   # downloadable per-rule evidence report
        lines = [f"# {o['id']} — {o['title']}", "", f"Status **{o['status']}** · confidence **{o['confidence']}** · type {o['type']} · feature group {o['group']} · validated {v['generated']}", "",
                 f"**Hypothesis.** {o['hypothesis']}", "", f"**Explicit rule.** {o['formulation']}", "", f"**Logic.** `{o['logic']}`", "",
                 f"**Fields.** {o['fields']}", "", f"**Method.** {o['method']}", "", f"**Acceptance criterion.** {o['criterion']}", "",
                 f"**Sample size.** {o['sample_size']} · **Effect size.** {o['effect_size']} · **Validation.** {o['validation']}", "",
                 f"**Counterexamples / exceptions.** {o['counterexamples']}", "", f"**Limitations.** {o['limitations']}", "",
                 f"**Economic interpretation (interpretation, not proven by data).** {o['economic']}", "", "## Metrics by split", "```json",
                 json.dumps(o["metrics"], indent=1, default=float), "```", "", f"Validator: `src/rules.py` · `{o['id']}` · reproduce with `python -m src.validation`"]
        (rep / f"{o['id']}.md").write_text("\n".join(lines), encoding="utf-8")
    (EVIDENCE / "register.json").write_text(json.dumps(out, default=float, indent=1), encoding="utf-8")
    print("register + confirmed rules written:", sum(R[k]["status"] == "PASS" for k in N), "/", len(N), "confirmed")


if __name__ == "__main__":
    main()
