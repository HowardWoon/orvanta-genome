"""Static charts (PNG) for the PDF dashboard and slides, drawn from the same evidence files as the app.

Run: python -m src.charts   -> outputs/charts/*.png
Each chart makes one point; its title states the takeaway. Source data = outputs/evidence/{evidence,validation}.json.
"""
from __future__ import annotations
import json, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
from .config import EVIDENCE, CHARTS, TABLES

# Synthetic Rule Intelligence Lab design tokens (neo-brutalist): Data Blue = observed data, Ink = model/prediction, Coral = anomaly/risk only
INK, INK2, MUTED, GRID = "#111827", "#111827", "#747474", "#e9e3d6"
S1, S2, S3, S4, RISK, YELLOW = "#2479D8", "#111827", "#1F8A70", "#C9A800", "#EF5147", "#F4D52E"
plt.rcParams.update({"font.family": ["Segoe UI"], "font.size": 10, "axes.edgecolor": INK, "axes.linewidth": 1.6, "axes.labelcolor": INK, "xtick.color": INK,
                     "ytick.color": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": .8, "axes.axisbelow": True,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 12.5, "axes.titleweight": "bold",
                     "axes.titlecolor": INK, "axes.titlelocation": "left", "legend.frameon": False, "legend.fontsize": 9, "figure.dpi": 100,
                     "patch.edgecolor": INK, "patch.linewidth": 1.0, "patch.force_edgecolor": True})
TITLE_FONT = {"family": "Bahnschrift", "weight": "bold"}
E = json.loads((EVIDENCE / "evidence.json").read_text())
V = {r["id"]: r for r in json.loads((EVIDENCE / "validation.json").read_text())["rules"]}
kfmt = FuncFormatter(lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else (f"{v/1e3:.0f}k" if v >= 1e3 else f"{v:.0f}"))


def save(fig, name, note=None):
    import textwrap
    for ax in fig.axes:
        ax.title.set_fontfamily("Bahnschrift")
        for tt in (ax._left_title, ax.title, ax._right_title):
            t = tt.get_text()
            if t:   # wrap any title line wider than the figure (prevents clipped titles)
                maxc = max(18, int(0.95 * fig.get_figwidth() * 72 / (tt.get_fontsize() * 0.55)))
                tt.set_text("\n".join(textwrap.fill(line, maxc) for line in t.split("\n")))
    if note:
        fig.text(0.01, 0.01, note, fontsize=7.5, color=MUTED, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04 if note else 0, 1, 1))
    fig.savefig(CHARTS / f"{name}.png", dpi=200); plt.close(fig)


SRC = "Source: Swift UMDAC 2026 synthetic dataset, n = 10,000,000"


def time_daily():
    d = pd.DataFrame(E["daily"]); d["d"] = pd.to_datetime(d.d)
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.bar(d.d, d.n, color=[S2 if w in (0, 6) else S1 for w in d.dow], width=.85)
    ax.yaxis.set_major_formatter(kfmt); ax.set_ylabel("Payments per UTC day")
    ax.set_title("Volume moves in week-long steps; weekday shape repeats every week")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=S1), plt.Rectangle((0, 0), 1, 1, color=S2)], labels=["Weekday", "Weekend"], loc="upper left")
    save(fig, "time_daily", SRC + " · 30 Apr–31 Jul 2023")


def time_localhour():
    h = pd.DataFrame(E["local_hour"]); fig, ax = plt.subplots(figsize=(6, 3.0))
    for t, c, lab in (("B", S1, "Business senders"), ("C", S2, "Consumer senders")):
        x = h[h.otype == t].sort_values("lh"); ax.plot(x.lh, x.n / x.n.sum(), color=c, lw=2, label=lab)
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xticks(range(0, 24, 2)); ax.set_xlabel("Local hour of sending country")
    ax.set_title("On the local clock, activity starts at 07:00 for every country"); ax.legend()
    save(fig, "time_localhour", SRC)


def time_weekday():
    d = pd.DataFrame(E["local_dow"]); d["s"] = d.n / d.n.sum(); lab = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    fig, ax = plt.subplots(figsize=(5.4, 3.3)); ax.bar([lab[i] for i in d.ldow], d.s, color=[S2 if i in (0, 6) else S1 for i in d.ldow])
    for i, v in zip(range(7), d.s): ax.text(i, v + .004, f"{v:.1%}", ha="center", fontsize=8, color=INK2)
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_title(f"One weekday shape in all countries\n(max country deviation {V['T3']['metrics']['full']['max_dev']:.1%})")
    save(fig, "time_weekday", SRC)


def ccy_mix():
    L = pd.DataFrame(E["local_ccy_by_country"]).head(12).iloc[::-1]
    oth = (1 - L.local_sh - L.eur - L.usd).clip(lower=0)
    fig, ax = plt.subplots(figsize=(5.6, 3.6)); y = np.arange(len(L)); left = np.zeros(len(L))
    for vals, c, lab in ((L.local_sh, S1, "Home currency"), (L.eur, S2, "EUR (vehicle)"), (L.usd, S3, "USD (vehicle)"), (oth, MUTED, "Other")):
        ax.barh(y, vals, left=left, color=c, label=lab, height=.72, edgecolor="white", linewidth=.6); left += vals.values
    ax.set_yticks(y, L.cc); ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlim(0, 1)
    ax.set_title(f"{V['C1']['metrics']['full']['home_share']:.1%} of payments use the instructing bank's home currency"); ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(.5, -.22))
    save(fig, "ccy_mix", SRC + " · country = first bank in BIC8_PATH")


def fx_heat():
    f = pd.DataFrame(E["fx_by_pc"]); pv = f.pivot(index="fx", columns="pc", values="n").fillna(0); pv = pv / pv.sum()
    fig, ax = plt.subplots(figsize=(5, 3.4)); im = ax.imshow(pv.values, cmap="Blues", origin="lower", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(pv.shape[1]), pv.columns); ax.set_yticks(range(pv.shape[0]), pv.index); ax.grid(False)
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]):
            v = pv.values[i, j]
            if v > 0: ax.text(j, i, f"{v:.0%}" if v >= .01 else "<1%", ha="center", va="center", fontsize=7.5, color="white" if v > .5 else INK)
    ax.set_xlabel("Participant count"); ax.set_ylabel("FX conversions")
    c = V["C2"]["metrics"]["full"]; ax.set_title(f"FX never exceeds hops (pc − 1)\nborder rule fits {int(c['n']-c['exceptions']):,} of {int(c['n']):,} rows")
    save(fig, "fx_heat", SRC)


def hops():
    h = pd.DataFrame(E["hops"]); h = h[h.pc <= 14]; pred = 1e7 * (1 - math.exp(-1)) * np.exp(-(h.pc - 2))
    fig, ax = plt.subplots(figsize=(5.6, 3.2)); ax.bar(h.pc, h.n, color=S1, label="Observed"); ax.plot(h.pc, pred, color=S2, marker="o", ms=4, lw=1.8, label="(1−e⁻¹)·e⁻ᵏ × 10M")
    ax.set_yscale("log"); ax.yaxis.set_major_formatter(kfmt); ax.set_xlabel("Participant count (K + 2)"); ax.set_xticks(h.pc)
    r = V["R1"]["metrics"]["full"]; ax.set_title(f"Each extra hop is 1/e as likely: MLE q = {r['q_mle']:.4f} vs 1/e = 0.3679"); ax.legend()
    save(fig, "hops", SRC + " · log scale")


def gaps():
    g = pd.DataFrame(E["gap_by_pc"]); g = g[g.pc <= 9]
    fig, ax = plt.subplots(figsize=(5, 3.2)); ax.plot(g.pc, 1 - .95 ** (g.pc - 1), color=S2, ls="--", lw=1.8, label="1 − 0.95^(pc−1)")
    ax.plot(g.pc, g.p, "o", color=S1, ms=6, label="Observed share N")
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("Participant count"); ax.set_title(f"Every link hides with p = {V['R4']['metrics']['full']['p_link_mle']:.3f}"); ax.legend()
    save(fig, "gaps", SRC)


def endpoint_swap():
    m = V["R5b"]["metrics"]["full"]
    lab = ["Currency = home ccy\nof first path bank", "Currency = home ccy\nof ORDERING_BIC8", "IBAN prefix =\nORDERING_BIC8 country"]
    v = [m["ccy_follows_path_first"], m["ccy_follows_obic"], m["iban_follows_obic"]]
    fig, ax = plt.subplots(figsize=(5, 3.2)); b = ax.bar(lab, v, color=[S1, MUTED, S3], width=.6)
    for r, x in zip(b, v): ax.text(r.get_x() + r.get_width() / 2, x + .02, f"{x:.0%}", ha="center", color=INK, fontsize=10, weight="semibold")
    ax.set_ylim(0, 1.12); ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.tick_params(axis="x", labelsize=8)
    ax.set_title(f"On the 5% swapped rows, two banks play two roles\n(n = {int(m['n']):,})")
    save(fig, "endpoint_swap", SRC + " · rows where first path BIC ≠ ORDERING_BIC8")


def dur_hist():
    d = pd.DataFrame(E["dur_hist_pc2"]); fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.bar(d.lb, d.n, color=[S2 if x >= 7 else S1 for x in d.lb], width=.85)
    ax.set_xticks(d.lb, [f"{2**x:.0f}s" if 2**x < 120 else (f"{2**x/60:.0f}m" if 2**x < 3600 else f"{2**x/3600:.1f}h") for x in d.lb], fontsize=8)
    ax.yaxis.set_major_formatter(kfmt); ax.set_xlabel("Duration bin (log₂ seconds)"); ax.set_title("Two-bank payments take seconds or ~20 minutes")
    save(fig, "dur_hist", SRC + " · Direct payments (pc = 2)")


def dur_class():
    d1 = V["D1"]["metrics"]; keys = ["fast->fast", "fast->slow", "slow->fast", "slow->slow"]
    fig, ax = plt.subplots(figsize=(5, 3.2)); v = [d1[k]["median_s"] for k in keys]
    b = ax.bar([k.replace("->", " → ") for k in keys], v, color=[S1, S2, S2, YELLOW], width=.6)
    for r, x in zip(b, v): ax.text(r.get_x() + r.get_width() / 2, x + 40, f"{x:,.0f}s", ha="center", fontsize=9, color=INK)
    ax.set_ylabel("Median duration (s)"); ax.set_title(f"Slow banks add up: both slow ≈ {d1['additivity_ratio']['value']:.2f}× one slow\n(out-of-sample: classes from half A, tested on half B)")
    save(fig, "dur_class", SRC)


def simpson():
    s = pd.DataFrame(E["simpson_hour"]); fig, ax = plt.subplots(figsize=(5.6, 3.2))
    ax.plot(s.hr, s.raw, color=S2, marker="o", ms=3, label=f"Raw (range {s.raw.max()-s.raw.min():.3f})")
    adj = s.adjusted + s.raw.mean(); ax.plot(s.hr, adj, color=S1, marker="o", ms=3, label=f"Bank fixed effects removed (range {adj.max()-adj.min():.3f})")
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("UTC hour"); ax.set_ylabel("Slow share"); ax.legend(loc="upper center", bbox_to_anchor=(.5, -.2), ncol=1, fontsize=8)
    ax.set_title("The hour effect is bank mix (Simpson), not time of day")
    save(fig, "simpson", SRC + " · fast–fast pairs, pc = 2")


def amt_segments():
    a = pd.DataFrame(E["amt_hist"]); fig, ax = plt.subplots(figsize=(6, 3.2))
    for seg, c, lab in (("CC", S3, "Consumer → Consumer"), ("BC", S1, "Business → Consumer"), ("CB", S4, "Consumer → Business"), ("BB", S2, "Business → Business")):
        x = a[(a.seg == seg) & (a.lb.between(-1, 9))].sort_values("lb"); ax.plot(x.lb, x.n / x.n.sum(), color=c, lw=2, label=lab)
    ax.set_xlabel("log₁₀ USD amount"); ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.legend(fontsize=8)
    m = V["A1"]["metrics"]["full"]
    ax.set_title(f"Each business party shifts ln(amount) by +2 (×7.4)\nfit: {m['intercept']:.2f} + {m['effect_ordering_B']:.2f}·[O=B] + {m['effect_beneficiary_B']:.2f}·[B=B], interaction {m['interaction']:+.3f}")
    save(fig, "amt_segments", SRC + " · normal rows")


def amt_country():
    c = pd.DataFrame(E["amt_country"]); c = pd.concat([c.head(8), c.tail(8)])
    fig, ax = plt.subplots(figsize=(6, 3.7)); ax.barh(c.cc, c.eff, color=[S2 if v < 0 else S1 for v in c.eff], height=.7)
    ax.axvline(0, color=INK2, lw=.8); ax.set_xlabel("Effect on ln(amount)")
    ax.set_title(f"Sending country shifts amounts up to ±e³\n(split-half r = {V['A2']['metrics']['full']['split_half_corr']:.4f})")
    save(fig, "amt_country", SRC)


def tokens():
    t = pd.DataFrame(E["token_presence"]); keep = ["business", "company_keyword", "last_name", "first_name", "street", "city", "country_code", "post_code", "iban", "line_break"]
    t = t[t.tok.isin(keep)].pivot(index="tok", columns="ty", values="share").reindex(keep[::-1]).fillna(0)
    fig, ax = plt.subplots(figsize=(6, 3.7)); y = np.arange(len(t))
    ax.barh(y + .2, t.B, height=.38, color=S1, label="Business"); ax.barh(y - .2, t.C, height=.38, color=S2, label="Consumer")
    ax.set_yticks(y, t.index, fontsize=8.5); ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.legend(loc="lower right")
    ax.set_title("B and C names use disjoint token sets")
    save(fig, "tokens", "Source: 500,000-row random sample of ORDERING_TOKENS")


def country_compare():
    c = pd.DataFrame(E["country_dist_compare"]).head(12).iloc[::-1]; y = np.arange(len(c))
    fig, ax = plt.subplots(figsize=(6, 3.7)); ax.barh(y + .2, c.o_bank, height=.38, color=S1, label="Sending bank country")
    ax.barh(y - .2, c.b_cust, height=.38, color=S2, label="Beneficiary address country"); ax.set_yticks(y, c.cc)
    ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.legend(loc="lower right", fontsize=8)
    ax.set_title(f"Beneficiaries rarely live where they bank ({V['P4']['metrics']['full']['b_match']:.1%} match)")
    save(fig, "country_compare", SRC)


def romance():
    r = pd.DataFrame(E["romance_steps"]); fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.plot(r.k, r.mlog, "o-", color=S1, lw=2, label="Observed mean ln(amount)"); ax.plot(r.k, r.mlog.iloc[0] + .4 * (r.k - 1), "--", color=S2, label="+0.40 per payment (×1.5)")
    ax.set_xlabel("Position in series"); ax.set_ylabel("mean ln(USD)"); ax.legend()
    ax.set_title(f"Romance scams escalate ×{math.exp(V['X1']['metrics']['full']['median_ln_step']):.2f} per payment ({int(V['X1']['metrics']['full']['series'])} series)")
    save(fig, "romance", SRC + " · ROMANCE_SCAM series")


def fatfinger():
    f, n = pd.DataFrame(E["fat_finger_hist"]), pd.DataFrame(E["normal_resid_hist"]); fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.bar(f.lb + .25, f.n / f.n.sum(), width=.45, color=RISK, label="FAT_FINGER_MISTAKE"); ax.plot(n.lb + .25, n.n / n.n.sum(), color=MUTED, lw=2, label="Normal payments")
    x = V["X3"]["metrics"]["full"]; ax.axvline(x["mode_low"], color=INK2, ls=":", lw=1); ax.axvline(x["mode_high"], color=INK2, ls=":", lw=1)
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("log₁₀(amount ÷ expected)"); ax.legend(fontsize=8)
    ax.set_title(f"Fat-finger amounts sit ≈100× off expectation\nmodes {x['mode_low']:+.1f} and {x['mode_high']:+.1f} (log₁₀); {x['up_share']:.0%} inflated")
    save(fig, "fatfinger", SRC)


def anomaly_profile():
    a = pd.DataFrame(E["anom_profile"]); a["o"] = a.a.eq("NORMAL").map({True: 1, False: 0}); a = a.sort_values(["o", "med_amt"])
    lab = [x.replace("_SCAM", "").replace("_MISTAKE", "").replace("ACCOUNT_REPLACEMENT", "ACCT_REPLACE").replace("_", " ").lower() for x in a.a]
    col = [MUTED if x == "NORMAL" else (RISK if x.endswith("SCAM") else S2) for x in a.a]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.0, 3.7), sharey=True)
    ax1.barh(lab, a.med_amt, color=col, height=.65); ax1.set_xscale("log"); ax1.set_xlabel("Median amount (USD, log)")
    for i, v in enumerate(a.med_amt): ax1.text(v * 1.15, i, f"${v:,.0f}", va="center", fontsize=7.5)
    ax1.set_xlim(50, a.med_amt.max() * 12)
    ax2.barh(lab, a.med_dur, color=col, height=.65); ax2.set_xlabel("Median duration (s)")
    for i, v in enumerate(a.med_dur): ax2.text(v + 20, i, f"{v:,.0f}", va="center", fontsize=7.5)
    ax2.set_xlim(0, a.med_dur.max() * 1.3)
    ax1.tick_params(axis="y", labelsize=8); fig.suptitle("Each anomaly label has its own amount and duration profile", fontsize=11, fontfamily="Bahnschrift")
    save(fig, "anomaly_profile", SRC + " · normal = grey reference")


def fp_uniform():
    F_ = json.loads((EVIDENCE / "forensics.json").read_text())
    rows = [("Second of minute", F_["second_uniform"]["cohen_w"]), ("Minute of hour", F_["minute_uniform"]["cohen_w"]),
            ("Duration last digit", F_["duration_last_digit"]["cohen_w"]), ("First digit vs Benford", F_["benford"]["cohen_w"]),
            ("Cents 00–99", F_["cents_uniform"]["cohen_w"])]
    fig, ax = plt.subplots(figsize=(6.0, 3.7)); y = np.arange(len(rows))
    ax.barh(y, [r[1] for r in rows], color=[S1, S1, S1, YELLOW, RISK], height=.6); ax.set_xscale("log")
    for i, (_, v) in enumerate(rows): ax.text(v * 1.15, i, f"w = {v:.4f}" if v < .1 else f"w = {v:.2f}", va="center", fontsize=8.5)
    ax.axvline(.1, color=INK, ls="--", lw=1); ax.text(.105, -.55, "small effect (w = 0.1)", fontsize=7.5)
    ax.set_yticks(y, [r[0] for r in rows]); ax.set_xlim(.001, 3); ax.set_xlabel("Cohen's w vs the uniform / Benford expectation (log)")
    ax.set_title("Timestamps are uniform; cents are not (Cohen's w)")
    save(fig, "fp_uniform", SRC)


def mule():
    m = V["X4"]["metrics"]["full"]; order = ["CEO_SCAM", "ACCOUNT_REPLACEMENT_SCAM", "FAT_FINGER_MISTAKE", "CUSTOMER_RECALL"]
    fig, ax = plt.subplots(figsize=(5, 3.2)); v = [m[k] for k in order]
    ax.bar(["CEO", "Account\nreplacement", "Fat finger", "Recall"], v, color=[RISK, RISK, S2, MUTED], width=.6)
    for i, x in enumerate(v): ax.text(i, x + .01, f"{x:.0%}", ha="center", fontsize=9)
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_title("Scam money lands in mule accounts that receive nothing else")
    ax.set_ylabel("Beneficiary accounts with only\nanomalous inflows")
    save(fig, "mule", SRC)


def recall():
    x = V["X5"]["metrics"]; k = [a for a in x if "z" in x[a]]; z = [x[a]["z"] for a in k]
    fig, ax = plt.subplots(figsize=(5, 3.2)); ax.barh(k, z, color=MUTED, height=.6)
    from scipy.stats import norm
    zc = norm.isf(.05 / 2 / (len(k) + 1)); ax.axvline(zc, color=RISK, ls="--", lw=1); ax.axvline(-zc, color=RISK, ls="--", lw=1)
    ax.set_xlabel("z vs normal traffic (dashed = Bonferroni 5% limit)"); ax.set_title("CUSTOMER_RECALL has no detectable signature"); ax.tick_params(axis="y", labelsize=8)
    save(fig, "recall", SRC)


GR = json.loads((EVIDENCE / "graph.json").read_text())
ST = json.loads((EVIDENCE / "stats.json").read_text())


def graph_loops():
    l = pd.DataFrame(GR["G3_loops"]); fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.bar(l.pc, l.obs_inter_repeat, color=S1, width=.6, label="Observed")
    ax.plot(l.pc, l.pred_iid, "o--", color=S2, lw=1.8, label="Predicted: i.i.d. draws, weight = bank size")
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("Participant count"); ax.set_ylabel("Paths revisiting an intermediary"); ax.legend()
    ax.set_title(f"Loops follow from size-weighted draws\n(max error {V['G3']['metrics']['full']['max_rel_err']:.1%}, β = {V['G3']['metrics']['full']['beta']:.2f})")
    save(fig, "graph_loops", SRC)


def graph_pairs():
    sc = pd.DataFrame(GR["G1_scatter"]); fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.scatter(sc.E, sc.n + .5, s=5, alpha=.35, color=S1, edgecolors="none"); lim = [sc.E.min(), sc.E.max()]
    ax.plot(lim, lim, "--", color=S2, lw=1.6, label="Independent pairing (O = E)")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("Expected payments if banks paired independently"); ax.set_ylabel("Observed payments")
    g = GR["G1_pairing"]; ax.set_title(f"Bank pairing is NOT independent (χ²/dof = {g['chi2_per_dof']:.0f})"); ax.legend(loc="upper left")
    save(fig, "graph_pairs", SRC + " · bank pairs with ≥2,000 payments per side, 2,500-pair sample")


def graph_hubs():
    h = pd.DataFrame(GR["hub_stp"]); fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.bar(h.pr_decile, h.slow_bank_share, color=[S1 if d == 10 else "#cfd8e3" for d in h.pr_decile], width=.7)
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xticks(h.pr_decile); ax.set_xlabel("PageRank decile (10 = top hubs)"); ax.set_ylabel("Manual (non-STP) banks")
    c = GR["concentration"]; ax.set_title(f"Top PageRank hubs are mostly automated (STP)")
    save(fig, "graph_hubs", SRC)


def stat_qq():
    q = pd.DataFrame(ST["amount_residual"]["qq"]); fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.plot([-3.3, 3.3], [-3.3, 3.3], "--", color=S2, lw=1.4); ax.plot(q.normal, q.empirical, "o", color=S1, ms=7, mec=INK)
    ax.set_xlabel("Normal quantile"); ax.set_ylabel("Empirical quantile (σ)")
    ax.set_title(f"Log-amount residual is Normal\n(KS D = {ST['amount_residual']['ks_D_vs_normal']:.4f}, skew {ST['amount_residual']['skew']:+.3f})")
    save(fig, "stat_qq", "Source: 400,000-row sample, within-country residual")


def stat_hill():
    h = pd.DataFrame(ST["hill"]); e = pd.DataFrame(ST["exceedance"]); fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.2))
    ax[0].plot(h.k, h.alpha, "o-", color=S2, lw=2); ax[0].set_xscale("log"); ax[0].set_xlabel("top-k order statistics"); ax[0].set_ylabel("Hill α")
    ax[0].set_title("Tail index drifts: not a power law")
    ax[1].bar(range(len(e)), e.ratio, color=S1, width=.6); ax[1].axhline(1, color=S2, ls="--", lw=1.4)
    ax[1].set_xticks(range(len(e)), [f"${t/1e6:.1f}M" if t < 1e9 else "$1B" for t in e.threshold], fontsize=8); ax[1].set_ylim(0, 1.2)
    ax[1].set_title("Observed ÷ model exceedances")
    save(fig, "stat_hill", SRC)


def detectors():
    d = pd.DataFrame(ST["detectors"]); lab = ["Duplicate\n(exact key)", "Romance\n(burst rule)", "Fat finger\n(amount only)", "CEO\n(heuristic)"]
    fig, ax = plt.subplots(figsize=(5.6, 3.2)); x = np.arange(len(d)); w = .26
    for i, (col, c) in enumerate([("precision", S1), ("recall", YELLOW), ("f1", S2)]):
        ax.bar(x + (i - 1) * w, d[col], width=w, color=c, label=col.upper() if col != "f1" else "F1")
    for xi, v in zip(x, d.f1): ax.text(xi + w, v + .03, f"{v:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x, lab, fontsize=8.5); ax.set_ylim(0, 1.15); ax.legend(ncol=3, loc="upper right")
    ax.set_title("Signatures, evaluated per class (no accuracy)")
    save(fig, "detectors", SRC + " · base rates 0.003–0.025%")


DI = json.loads((EVIDENCE / "discovery.json").read_text(encoding="utf-8"))
FO = json.loads((EVIDENCE / "forensics.json").read_text(encoding="utf-8"))
AT = json.loads((EVIDENCE / "atlas.json").read_text(encoding="utf-8"))


def discovery_heatmap():
    pr = pd.DataFrame(DI["pairs"]); feats = DI["features"]; ix = {f_: i for i, f_ in enumerate(feats)}
    M = np.zeros((len(feats), len(feats)))
    for r in pr.itertuples():
        M[ix[r.a], ix[r.b]] = M[ix[r.b], ix[r.a]] = r.v_dev
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("lab", ["#ffffff", YELLOW, S1, INK])
    fig, ax = plt.subplots(figsize=(6.4, 5.2)); im = ax.imshow(M, cmap=cm, vmin=0, vmax=.6); ax.grid(False)
    short = [f_.replace("_", " ")[:18] for f_ in feats]
    ax.set_xticks(range(len(feats)), short, rotation=70, fontsize=6.5, ha="right"); ax.set_yticks(range(len(feats)), short, fontsize=6.5)
    strong = pr[pr.v_dev >= .05]; ne = strong.explained_by.notna().sum(); nm = strong.verdict.fillna("").str.startswith("mediated").sum()
    ax.set_title(f"{len(pr)} feature pairs scanned · {len(strong)} strong\n{ne} explained by rules · {nm} mediated · {len(strong) - ne - nm} open")
    fig.colorbar(im, ax=ax, fraction=.035, pad=.02, label="Cramér's V (dev half)")
    save(fig, "discovery_heatmap", f"Source: {DI['sample']:,}-row random sample; dev / validation halves by hash(row id)")


def atlas_static():
    nodes = {n["id"]: n for n in AT["nodes"]}; OX, OY = 95, 34
    sty = {"deterministic": (INK, 2.6, "-"), "stochastic": (S1, 1.8, "-"), "unresolved": (S1, 1.8, "--"), "independent": (MUTED, 1.2, ":"), "confounded": ("#9a7b00", 1.2, "-.")}
    fig, ax = plt.subplots(figsize=(11, 4.8)); ax.set_xlim(0, 1380); ax.set_ylim(590, 0); ax.axis("off")
    for e in AT["edges"]:
        a, b = nodes[e["source"]], nodes[e["target"]]; c, w, ls = sty[e["kind"]]
        arrow = "-|>" if e["kind"] in ("deterministic", "stochastic", "unresolved") else "-"
        ax.annotate("", xy=(b["x"] + OX, b["y"] + OY), xytext=(a["x"] + OX, a["y"] + OY),
                    arrowprops=dict(arrowstyle=arrow, color=c, lw=w, ls=ls, shrinkA=16, shrinkB=18, mutation_scale=11))
    for n in nodes.values():
        ax.text(n["x"] + OX, n["y"] + OY, n["label"], ha="center", va="center", fontsize=7.2, fontweight="bold", color=INK,
                bbox=dict(boxstyle="square,pad=0.45", fc=("#ffffff" if n["kind"] == "field" else "#F5F0E6"), ec=INK, lw=1.6, ls=("-" if n["kind"] == "field" else "--")))
    for i, (k, (c, w, ls)) in enumerate(sty.items()):
        ax.plot([20 + i * 270, 60 + i * 270], [575, 575], color=c, lw=w + .4, ls=ls); ax.text(68 + i * 270, 575, k, va="center", fontsize=8)
    ax.set_title("Rule Dependency Atlas: reconstructed generation dependencies (not causal claims)")
    save(fig, "atlas", "Edges link to validated rules; dashed boxes = latent generator entities")


def f1_cents():
    c = pd.DataFrame(FO["cents00_by_currency"]).sort_values("cents00"); fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ax.barh(c.cur, c.cents00, color=[YELLOW if x == "USD" else S1 for x in c.cur], height=.7)
    ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("Share of amounts ending .00")
    u = {r["usd_denominated"]: r for r in FO["usd_roundness"]}
    ax.set_title(f"Fingerprint F1: USD keeps round amounts ({u[True]['whole_units']:.0%}),\nconverted currencies do not ({u[False]['whole_units']:.1%})")
    save(fig, "f1_cents", SRC + " · normal rows")


def change_points():
    cp = FO["change_points"]; d = pd.DataFrame(cp["daily"]); d["d"] = pd.to_datetime(d.d); fig, ax = plt.subplots(figsize=(7, 3.0))
    ax.plot(d.d, d.y, "o-", color=MUTED, ms=3, lw=1)
    for sgm in cp["segments"]:
        a, b = pd.to_datetime(sgm["start"]), pd.to_datetime(sgm["end"]) + pd.Timedelta(days=1); ax.hlines(np.log(sgm["level"]), a, b, color=S1, lw=3.5)
    for c_ in cp["change_points"]:
        ax.axvline(pd.to_datetime(c_), color=INK, ls=":", lw=1)
    ax.set_ylabel("log daily volume (weekday-adjusted)")
    ax.set_title(f"Rule T4b: {len(cp['change_points'])} change points, all on Mondays (residual sd {cp['residual_sd_log']:.3f})")
    save(fig, "change_points", SRC + " · binary segmentation, BIC penalty")


# ---------------------------------------------------------------- dashboard v2: additional evidence charts (all from existing evidence files)
FO = json.loads((EVIDENCE / "forensics.json").read_text(encoding="utf-8"))
ST = json.loads((EVIDENCE / "stats.json").read_text(encoding="utf-8"))
GR = json.loads((EVIDENCE / "graph.json").read_text(encoding="utf-8"))
FS = (6.0, 3.7)


def benford():
    b = FO["benford"]; d = pd.DataFrame(b["digits"]); fig, ax = plt.subplots(figsize=FS)
    ax.bar(d.d - .2, d.observed, width=.4, color=S1, label="Observed first digit"); ax.bar(d.d + .2, d.benford, width=.4, color=YELLOW, label="Benford's law")
    ax.set_xticks(d.d); ax.set_xlabel("Leading digit of USD amount"); ax.set_ylabel("Share of payments"); ax.yaxis.set_major_formatter(PercentFormatter(1, 0))
    ax.set_title(f"Amounts are close to Benford (Nigrini MAD {b['nigrini_mad']:.4f})"); ax.legend()
    save(fig, "benford", SRC + f" · {b['n']:,} non-anomalous amounts")


def cents_segment():
    d = pd.DataFrame(FO["cents_by_segment"]); fig, ax = plt.subplots(figsize=FS); x = np.arange(len(d))
    for i, (k, lab, c) in enumerate((("cents00", ".00 ending", S1), ("mult100", "multiple of 100", YELLOW), ("mult1000", "multiple of 1,000", S2))):
        ax.bar(x + (i - 1) * .27, d[k], width=.27, color=c, label=lab)
    ax.set_xticks(x); ax.set_xticklabels([f"{s_[0]}→{s_[1]}" for s_ in d.seg]); ax.set_xlabel("Sender → receiver type (B business, C consumer)")
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_ylabel("Share of payments"); ax.set_title("Round amounts by segment"); ax.legend()
    save(fig, "cents_segment", SRC)


def h38_vehicle():
    f = EVIDENCE / "h38_vehicle.json"
    if not f.exists(): return
    h = json.loads(f.read_text()); d = pd.DataFrame(h["by_pc"]); fig, ax = plt.subplots(figsize=FS)
    ax.plot(d.pc, d.eur, "o-", color=S1, lw=2, label="EUR"); ax.plot(d.pc, d.usd, "s-", color=S2, lw=2, label="USD")
    ax.set_ylim(0, max(d.eur.max(), d.usd.max()) * 1.6); ax.yaxis.set_major_formatter(PercentFormatter(1, 1)); ax.set_xticks(d.pc); ax.set_xticklabels([f"{k}{'+' if k == d.pc.max() else ''}" for k in d.pc])
    ax.set_xlabel("Participants on the route"); ax.set_ylabel("Share paid in EUR / USD")
    ax.set_title("H38: on routes with no EUR/USD bank, the vehicle\nshare is flat across route length"); ax.legend()
    save(fig, "h38_vehicle", f"{SRC} · routes with no EUR or USD bank, n = {int(d.n.sum()):,}")


def r1_country():
    d = pd.DataFrame(ST["R1_by_country"]).sort_values("q"); fig, ax = plt.subplots(figsize=FS)
    ax.bar(d.cc, d.q, color=S1); ax.axhline(math.exp(-1), color=RISK, ls="--", lw=1.6, label="1/e = 0.3679")
    ax.set_ylim(.355, .375); ax.set_ylabel("Continuation probability q"); ax.set_xlabel("Sending country (20 largest)"); ax.tick_params(axis="x", labelsize=8)
    ax.set_title("R1: the same q ≈ 1/e in every sending country"); ax.legend(loc="lower right")
    save(fig, "r1_country", SRC + " · q = mean K / (1 + mean K)")


def r2_classes():
    m = V["R2"]["metrics"]["full"]; fig, ax = plt.subplots(figsize=FS)
    lab = ["Cover-prone banks\n(out of sample)", "Other banks\n(out of sample)", "Pooled\n(all non-direct)", "Lowest\ncountry", "Highest\ncountry"]
    val = [m["oos_cover_banks_share"], m["oos_other_banks_share"], m["pooled_covered_share"], m["country_share_min"], m["country_share_max"]]
    bars = ax.bar(lab, val, color=[S1, S2, YELLOW, MUTED, MUTED])
    for b_, v in zip(bars, val): ax.text(b_.get_x() + b_.get_width() / 2, v + .01, f"{v:.1%}", ha="center", fontsize=9)
    ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_ylabel("Covered share of non-direct payments"); ax.tick_params(axis="x", labelsize=8.5)
    ax.set_title(f"R2: cover is a bank habit, not one constant rate\n({int(m['cover_banks'])} cover-prone of {int(m['cover_banks'] + m['other_banks']):,} classed banks)")
    save(fig, "r2_classes", SRC + " · classes fitted on half_0, measured on half_1")


def r5b_roles():
    m = V["R5b"]["metrics"]["full"]; fig, ax = plt.subplots(figsize=FS)
    lab = ["Currency = home ccy\nof path[1] bank", "Currency = home ccy\nof ORDERING_BIC8", "IBAN prefix =\nORDERING_BIC8 country"]
    val = [m["ccy_follows_path_first"], m["ccy_follows_obic"], m["iban_follows_obic"]]
    bars = ax.barh(lab[::-1], val[::-1], color=[S2, MUTED, S1][::-1])
    for b_, v in zip(bars, val[::-1]): ax.text(v + .01, b_.get_y() + b_.get_height() / 2, f"{v:.0%}", va="center", fontsize=10)
    ax.set_xlim(0, 1.12); ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("Share of mismatched payments")
    ax.set_title("R5b: when the two banks differ, fields follow\ndifferent roles")
    save(fig, "r5b_roles", SRC + f" · payments where path[1] ≠ ORDERING_BIC8")


def r3_scatter():
    d = pd.DataFrame(E["intermediary_scatter"]); d = d[(d.ni > 0) & (d.nsend > 0)]; fig, ax = plt.subplots(figsize=FS)
    ax.scatter(d.nsend, d.ni, s=6, alpha=.35, color=S1, edgecolors="none"); ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Payments the bank sends (log)"); ax.set_ylabel("Times used as intermediary (log)")
    ax.set_title(f"R3: intermediaries are chosen by bank size\n(corr of logs = {V['R3']['metrics']['full']['corr_log']:.2f})")
    save(fig, "r3_scatter", SRC + f" · random sample of {len(d):,} banks")


def stp_size():
    d = pd.DataFrame(E["stp_by_size"]); fig, ax = plt.subplots(figsize=FS)
    bars = ax.bar(d.sz, d.slow_bank_share, color=[MUTED, MUTED, S1, S2])
    for b_, v, n in zip(bars, d.slow_bank_share, d.banks): ax.text(b_.get_x() + b_.get_width() / 2, v + .01, f"{v:.0%}\n({n:,} banks)", ha="center", fontsize=8.5)
    ax.set_ylim(0, .75); ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_xlabel("Payments the bank sends (2-party routes)"); ax.set_ylabel("Share of banks classed manual")
    ax.set_title("D2: large banks are almost never manual")
    save(fig, "stp_size", SRC + " · bank manual if > 90% of its 2-party payments take > 120 s")


def strength_ccdf():
    d = pd.DataFrame(GR["strength_ccdf"]); fig, ax = plt.subplots(figsize=FS)
    ax.loglog(d.s, d.p, color=S1, lw=2); c = GR["concentration"]
    ax.set_xlabel("Bank strength (hops handled, log)"); ax.set_ylabel("P(strength ≥ x)")
    ax.set_title(f"Network concentration: Gini {c['gini_strength']:.2f};\ntop 1% of banks carry {c['top1pct_share']:.0%} of hops")
    save(fig, "strength_ccdf", SRC + f" · {int(GR['network']['nodes']):,} banks")


def param_ci():
    ci = ST["ci"]; k = list(ci)[:8]; fig, ax = plt.subplots(figsize=(6.4, 3.9)); y = np.arange(len(k))[::-1]
    for yi, kk in zip(y, k):
        v = ci[kk]; ax.errorbar(v["p"], yi, xerr=[[v["p"] - v["lo"]], [v["hi"] - v["p"]]], fmt="o", color=S1, ecolor=S2, capsize=4, ms=5)
        ax.text(1.02, yi, f"{v['p']:.4f}  [{v['lo']:.4f}, {v['hi']:.4f}]", va="center", fontsize=7.5, transform=ax.get_yaxis_transform())
    ax.set_yticks(y); ax.set_yticklabels([kk.split(" [")[0] for kk in k], fontsize=7.5); ax.set_xlim(0, 1); ax.xaxis.set_major_formatter(PercentFormatter(1, 0))
    ax.set_xlabel("Estimate with 95% CI (Wilson / Fisher; bars narrower than the dots at n = 10M)"); ax.set_title("Parameters are pinned down to ±0.03 points")
    fig.subplots_adjust(right=.62); save(fig, "param_ci", SRC)


def exceedance():
    d = pd.DataFrame(ST["exceedance"]); fig, ax = plt.subplots(figsize=FS); x = np.arange(len(d))
    ax.bar(x - .2, d.observed, width=.4, color=S1, label="Observed"); ax.bar(x + .2, d.predicted, width=.4, color=YELLOW, label="Lognormal model")
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels([f"${t/1e6:g}M" if t >= 1e6 else f"${t/1e3:g}k" for t in d.threshold]); ax.set_xlabel("Amount threshold (USD)")
    ax.set_ylabel("Payments above threshold (log)"); ax.set_title("A3: the lognormal model predicts the tail\n(ratios " + ", ".join(f"{r:.2f}" for r in d.ratio) + ")"); ax.legend()
    save(fig, "exceedance", SRC + " · no amount capped (max $15.7bn kept)")


def amt_variance():
    v = E["amt_variance"]; parts = [("Sending country", v["country"]), ("Bank", v["bank"]), ("Account", v["account"]), ("Residual noise", v["noise"])]
    fig, ax = plt.subplots(figsize=FS); left = 0
    for (lab, val), c in zip(parts, (S1, S3, YELLOW, MUTED)):
        ax.barh([0], [val], left=left, color=c, label=f"{lab} {val:.2f} ({val / v['total']:.0%})"); left += val
    ax.set_yticks([]); ax.set_xlim(0, v["total"] * 1.02); ax.set_xlabel(f"Variance of ln(amount) after party-type effects (total {v['total']:.2f})")
    ax.set_title("A2: the sending country is the largest structured\nsource of amount variation"); ax.legend(loc="upper center", bbox_to_anchor=(.5, -.35), ncol=2, fontsize=8.5)
    save(fig, "amt_variance", SRC + " · nested variance decomposition")


def iban_country():
    d = pd.DataFrame(E["iban_by_country"]).sort_values("iban"); fig, ax = plt.subplots(figsize=FS)
    ax.bar(range(len(d)), d.iban, color=[S1 if v > .5 else MUTED for v in d.iban], width=1)
    ax.set_xticks([]); ax.set_xlabel(f"Bank countries ({len(d)}), sorted"); ax.set_ylabel("Accounts in IBAN format"); ax.yaxis.set_major_formatter(PercentFormatter(1, 0))
    ax.set_title("P2: IBAN use is all-or-nothing by bank country")
    save(fig, "iban_country", SRC + " · countries with ≥ 20k payments")


def ob_share():
    d = pd.DataFrame(E["ob_share_by_country"]).sort_values("ob"); fig, ax = plt.subplots(figsize=FS)
    ax.bar(range(len(d)), d.ob, color=S1, width=1, label="sender is business"); ax.plot(range(len(d)), d.bb, color=S2, lw=1.6, label="receiver is business")
    ax.set_xticks([]); ax.set_xlabel(f"Bank countries ({len(d)}), sorted by sender share"); ax.yaxis.set_major_formatter(PercentFormatter(1, 0)); ax.set_ylabel("Business share")
    ax.set_title("P5: customer mix varies by bank (aggregated to country)"); ax.legend()
    save(fig, "ob_share", SRC)


def anomaly_rates():
    d = pd.DataFrame(ST["anomaly_rates"]).sort_values("per_10k"); fig, ax = plt.subplots(figsize=FS)
    ax.barh(d.anom.str.replace("_", " ").str.lower(), d.per_10k, xerr=[d.per_10k - d.lo, d.hi - d.per_10k], color=RISK, ecolor=INK, capsize=3)
    for i, (v, n) in enumerate(zip(d.per_10k, d.n)): ax.text(v + .12, i, f"{n:,}", va="center", fontsize=8.5)
    ax.set_xlabel("Labelled payments per 10,000 (95% CI)"); ax.set_title(f"Six anomaly labels, {int(d.n.sum()):,} payments in total")
    save(fig, "anomaly_rates", SRC)


def dup_groups():
    d = pd.DataFrame(E["dup_groups"]); fig, ax = plt.subplots(figsize=FS)
    bars = ax.bar(d.n.astype(str), d.ngroups, color=S1)
    for b_, g, sp in zip(bars, d.ngroups, d.med_span): ax.text(b_.get_x() + b_.get_width() / 2, g + .5, f"{g} groups\nmedian span {sp:,.0f} s", ha="center", fontsize=8)
    ax.set_xlabel("Copies in the duplicate group"); ax.set_ylabel("Groups"); ax.set_ylim(0, d.ngroups.max() * 1.3)
    ax.set_title("X2: duplicates come in groups of 2–5 identical copies")
    save(fig, "dup_groups", SRC + " · same amount, path and duration")


def ff_pr():
    d = pd.DataFrame(ST["fat_finger_pr_curve"]); fig, ax = plt.subplots(figsize=FS)
    ax.plot(d.recall, d.precision, color=RISK, lw=2); ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.xaxis.set_major_formatter(PercentFormatter(1, 0)); ax.yaxis.set_major_formatter(PercentFormatter(1, 0))
    ax.set_title(f"X3: an amount-only detector is weak\n(PR-AUC {ST['fat_finger_pr_auc']:.3f}; base rate 0.02%)")
    save(fig, "ff_pr", SRC + " · |z| of amount vs A1/A2 expectation")


def main():
    for f in (time_daily, time_localhour, time_weekday, ccy_mix, fx_heat, hops, gaps, endpoint_swap, dur_hist, dur_class, simpson,
              amt_segments, amt_country, tokens, country_compare, romance, fatfinger, anomaly_profile, fp_uniform, mule, recall,
              graph_loops, graph_pairs, graph_hubs, stat_qq, stat_hill, detectors,
              discovery_heatmap, atlas_static, f1_cents, change_points,
              benford, cents_segment, h38_vehicle, r1_country, r2_classes, r5b_roles, r3_scatter, stp_size, strength_ccdf,
              param_ci, exceedance, amt_variance, iban_country, ob_share, anomaly_rates, dup_groups, ff_pr):
        f()
    print("charts:", len(list(CHARTS.glob("*.png"))))


if __name__ == "__main__":
    main()
