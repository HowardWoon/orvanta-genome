
# ================================================================== LAB PAGES (appended into app.py by the build patch; not imported)
elif page == "Lab Overview":
    st.markdown("<div class='mono'>The Synthetic Rule Intelligence Lab · independent competition prototype</div>", unsafe_allow_html=True)
    st.title("Decode the rules behind 10 million synthetic payments")
    tri = pd.DataFrame(DI["triage"]); pr = pd.DataFrame(DI["pairs"]); strong = pr[pr.v_dev >= .05]
    n_expl = int(strong.explained_by.notna().sum()); n_med = int((tri.verdict.str.startswith("mediated")).sum()) if len(tri) else 0
    st.markdown(f"""<div class='flow4'>
      <div class='on'><span>01 · Discover</span><b>{len(pr)} feature pairs scanned</b><span>{len(strong)} strong · {len(DI['trees'])} decision-tree searches</span></div>
      <div><span>02 · Reconstruct</span><b>{len(REG)} explicit rules</b><span>typed A–E · formula + logic each</span></div>
      <div><span>03 · Validate</span><b>{n_pass}/{len(REG)} pass 5 splits</b><span>random halves · periods · out-of-sample</span></div>
      <div><span>04 · Explain</span><b>{len(AT['edges'])} atlas edges</b><span>economic reading · limits · lineage</span></div></div>""", unsafe_allow_html=True)
    c2 = RULES["C2"]["metrics"]["full"]; conf = pd.Series([r["confidence"] for r in REG]).value_counts()
    kpis([("10,000,000", "payments · 0 dropped"), (f"{n_expl}+{n_med}/{len(strong)}", "strong dependencies explained (rule + mediated)"),
          (f"{conf.get('High', 0)}·{conf.get('Medium', 0)}·{conf.get('Low', 0)}", "high · medium · low confidence"),
          (f"{(c2['n'] - c2['exceptions']) / c2['n']:.5%}", "FX rule exact match"), ("100%", "SQL vs independent Python")])
    st.markdown(f"""<div class='lablog'><b>LAB LOG</b> <span class='dim'>— what changed our mind</span><br>
      &gt; discovery engine flagged <b>routing_type × sender_country</b> (V = .095, no rule) → <b>R2 revised</b>: Covered is a per-bank propensity, not a constant 11.3%<br>
      &gt; flagged <b>routing_type × home_currency</b> → <b>C3 discovered</b>: currency is drawn from the route ({RULES['C3']['metrics']['full']['in_route_share']:.1%} in a route currency)<br>
      &gt; flagged <b>receiver_type × receiver_bank_country</b> → <b>P5 discovered</b>: customer mix is a bank attribute (split-half r = {RULES['P5']['metrics']['full']['receiver_split_half_r']:.3f})<br>
      &gt; change-point search on weekly levels → <b>T4b</b>: {RULES['T4b']['metrics']['full']['change_points']} change points, <b>all on Mondays</b><br>
      &gt; cents forensics → <b>F1</b>: USD amounts {RULES['F1']['metrics']['full']['usd_whole_share']:.0%} whole-dollar vs {RULES['F1']['metrics']['full']['non_usd_whole_share']:.1%} for converted currencies<br>
      &gt; open: bank-pair affinity mechanism (G1) · weekly level values (T4) · CUSTOMER_RECALL has no signature (X5)</div>""", unsafe_allow_html=True)
    st.subheader("Headline rules")
    cols = st.columns(3)
    for i, rid in enumerate(["C2", "C3", "R1", "G3", "D2", "A1"]):
        r = RULES[rid]
        with cols[i % 3]:
            card(f"<span class='tag {r['confidence']}'>{rid}</span><span class='mono'>{r['group']}</span><h4 style='font-family:{DISPLAY};margin:.4rem 0'>{r['title']}</h4>"
                 f"<div class='formula'>{r['formulation']}</div><div class='mono'>{r['effect_size']}</div>")
            st.button(f"Open {rid} in Rule Explorer", key=f"ov_{rid}", on_click=goto, args=("Rule Explorer", rid))

elif page == "Discovery Engine":
    section("DISCOVER · automated", "Rule discovery engine",
            f"Every pair of {len(DI['features'])} discretised features scored on a development half and re-scored on an independent validation half "
            f"({DI['dev_rows']:,} + {DI['val_rows']:,} rows); strong pairs are mapped to the rule that explains them or tested for mediation.")
    pr = pd.DataFrame(DI["pairs"]); strong = pr[pr.v_dev >= .05].copy()
    strong["status"] = np.where(strong.explained_by.notna(), "explained by rule", strong.verdict.fillna("open"))
    kpis([(fmt(len(pr)), "feature pairs scanned"), (fmt(len(strong)), "strong (Cramér's V ≥ 0.05)"), (fmt((strong.status == "explained by rule").sum()), "explained by a reconstructed rule"),
          (fmt(strong.status.str.startswith("mediated").sum()), "mediated (composite of rules)"), (fmt(strong.status.str.startswith("open").sum()), "open candidates")])
    hm = pd.concat([pr[["a", "b", "v_dev"]], pr[["b", "a", "v_dev"]].rename(columns={"b": "a", "a": "b"})])
    chart(alt.Chart(hm, title="Dependency map: Cramér's V between features (development half)").mark_rect(stroke=WHITE, strokeWidth=.5).encode(
        x=alt.X("a:N", title=None, axis=alt.Axis(labelAngle=-50, labelFontSize=9)), y=alt.Y("b:N", title=None, axis=alt.Axis(labelFontSize=9)),
        color=alt.Color("v_dev:Q", scale=alt.Scale(range=[WHITE, YELLOW, BLUE, INK], domain=[0, .05, .3, 1]), title="V"),
        tooltip=["a", "b", alt.Tooltip("v_dev:Q", format=".3f")]), 520)
    st.subheader("Strong dependencies and how each is explained")
    st.dataframe(strong[["a", "b", "v_dev", "v_val", "status", "explained_by", "best_mediator", "residual_v"]].rename(columns={
        "a": "Feature A", "b": "Feature B", "v_dev": "V (dev)", "v_val": "V (validation)", "status": "Verdict", "explained_by": "Rule",
        "best_mediator": "Best mediator", "residual_v": "Residual V | mediator"}).round(4), hide_index=True, width="stretch", height=360)
    st.subheader("Decision-tree rule search (depth 3, holdout-scored)")
    tsel = st.selectbox("Target field", [t_["target"] for t_ in DI["trees"]], key="de_target")
    tr = next(t_ for t_ in DI["trees"] if t_["target"] == tsel)
    if "holdout_accuracy" in tr:
        kpis([(f"{tr['holdout_accuracy']:.3f}", "holdout accuracy"), (f"{tr['majority_baseline']:.3f}", "majority baseline"),
              (f"{tr['holdout_accuracy'] - tr['majority_baseline']:+.3f}", "gain over baseline"), (str(len(tr["leaves"])), "candidate rules (leaves)"),
              (tr["top_splits"][0]["feature"] if tr["top_splits"] else "—", "strongest split")])
    else:
        kpis([(f"{tr['holdout_r2']:.3f}", "holdout R²"), (str(len(tr["leaves"])), "candidate rules"), (tr["top_splits"][0]["feature"], "strongest split"), ("A1 / A2", "rules rediscovered"), ("σ ≈ 2.08", "irreducible noise")])
    st.dataframe(pd.DataFrame(tr["leaves"]).round(4), hide_index=True, width="stretch")
    card("Trees are used as a <b>search device</b>, not a predictive model: a candidate counts only if its holdout purity confirms it, and every confirmed leaf is compared with the hand-reconstructed rules "
         "(e.g. <i>participants = 2 ⇒ Direct</i> = R1; the routing ceiling of 0.958 = R1 + R2's coin flip between Covered and Indirect).", "y")

elif page == "Forensics Lab":
    section("DISCOVER · VALIDATE", "Statistical forensics lab", "How were values drawn? Fingerprints, change points, conditional independence, intervals and tails.")
    bf = FO["benford"]; usd = {r["usd_denominated"]: r for r in FO["usd_roundness"]}
    kpis([(f"{bf['nigrini_mad']:.4f}", f"Benford MAD ({bf['conformity']})"), (f"{usd[True]['whole_units']:.1%}", "USD amounts ending .00"),
          (f"{usd[False]['whole_units']:.1%}", "converted currencies ending .00"), (f"w = {FO['second_uniform']['cohen_w']:.4f}", "seconds-of-minute uniform"),
          (f"{FO['bic']['grammar_match']:.0%}", "BIC grammar NNNN·CC·LL")])
    c1, c2 = st.columns(2)
    with c1:
        b = pd.DataFrame(FO["benford"]["digits"]).melt("d", ["observed", "benford"])
        chart(alt.Chart(b, title="First digit of USD_AMOUNT vs Benford").mark_bar(stroke=INK, strokeWidth=1).encode(
            x=alt.X("d:O", title="FIRST DIGIT"), xOffset="variable:N", y=alt.Y("value:Q", axis=alt.Axis(format="%"), title="SHARE"),
            color=alt.Color("variable:N", scale=alt.Scale(domain=["observed", "benford"], range=[BLUE, YELLOW]), title=None)), 260)
    with c2:
        cc = pd.DataFrame(FO["cents00_by_currency"])
        chart(alt.Chart(cc, title="Rule F1: whole-unit share by payment currency").mark_bar(stroke=INK, strokeWidth=1.5).encode(
            y=alt.Y("cur:N", sort="-x", title=None), x=alt.X("cents00:Q", axis=alt.Axis(format="%"), title="AMOUNTS ENDING .00"),
            color=alt.condition("datum.cur == 'USD'", alt.value(YELLOW), alt.value(BLUE)), tooltip=["cur", alt.Tooltip("cents00:Q", format=".2%"), alt.Tooltip("n:Q", format=",")]), 260)
    cp = FO["change_points"]; dly = pd.DataFrame(cp["daily"]); dly["d"] = pd.to_datetime(dly.d)
    segs = pd.DataFrame(cp["segments"]); segs["start"] = pd.to_datetime(segs.start); segs["end"] = pd.to_datetime(segs.end) + pd.Timedelta(days=1); segs["lvl"] = np.log(segs.level)
    chart((alt.Chart(dly, title=f"Rule T4b: {len(cp['change_points'])} change points in weekly volume, all on Mondays (weekday shape removed)").mark_line(color=GREY, point=alt.OverlayMarkDef(size=18, color=INK)).encode(
        x=alt.X("d:T", title=None), y=alt.Y("y:Q", title="LOG DAILY VOLUME (WEEKDAY-ADJUSTED)", scale=alt.Scale(zero=False))) +
           alt.Chart(segs).mark_rule(color=BLUE, strokeWidth=4).encode(x="start:T", x2="end:T", y="lvl:Q", tooltip=["start_weekday", "days", alt.Tooltip("level:Q", format=",.0f")])), 280)
    st.subheader("Conditional-independence tests (feed the Dependency Atlas)")
    st.dataframe(pd.DataFrame(FO["ci_tests"]).round(4), hide_index=True, width="stretch")
    st.subheader("Identifier grammar")
    a, b = st.columns(2)
    with a:
        card(f"<b>BIC8</b>: {FO['bic']['banks']:,} banks in {FO['bic']['countries']} countries; grammar NNNN·CC·LL matches {FO['bic']['grammar_match']:.0%}; "
             f"countries with more than one location code: <b>{FO['bic']['countries_with_multiple_location_codes']}</b>; bank numbers 0–{FO['bic']['max_bank_number']} (sparse).<br>"
             f"<b>IBAN</b>: one length per country in {FO['iban_single_length_share']:.0%} of IBAN countries.")
    with b:
        lt = FO["local_account_templates"]
        card(f"<b>Local account formats</b>: {lt['distinct']:,} character templates; top 10 cover {lt['top10_share']:.0%} → formats are generated per bank/country, not one template.<br>"
             f"<b>Negative result</b>: no fixed FX rate restores round originals for EUR/GBP/CHF (best near-integer share ≈ {max(r['best_near_integer_share'] for r in FO['fixed_rate_search']):.1%} vs ≈1.2% baseline).")
    st.subheader("Intervals, tails and step-time distributions")
    ci = pd.DataFrame([dict(parameter=k, estimate=v["p"], lo95=v["lo"], hi95=v["hi"]) for k, v in ST["ci"].items()])
    st.dataframe(ci.round(5), hide_index=True, width="stretch")
    c3, c4 = st.columns(2)
    with c3:
        qq = pd.DataFrame(ST["amount_residual"]["qq"]); diag = pd.DataFrame({"normal": [-3.2, 3.2], "empirical": [-3.2, 3.2]})
        chart(alt.Chart(qq, title=f"Log-amount residual vs Normal (KS D = {ST['amount_residual']['ks_D_vs_normal']:.4f})").mark_point(size=80, filled=True, color=BLUE, stroke=INK).encode(
            x=alt.X("normal:Q", title="NORMAL QUANTILE"), y=alt.Y("empirical:Q", title="EMPIRICAL (σ)")) + alt.Chart(diag).mark_line(color=INK, strokeDash=[6, 4]).encode(x="normal:Q", y="empirical:Q"), 260)
    with c4:
        hl = pd.DataFrame(ST["hill"])
        chart(alt.Chart(hl, title="Hill tail index drifts → lognormal, not power law").mark_line(point=True, color=INK, strokeWidth=2.5).encode(
            x=alt.X("k:Q", scale=alt.Scale(type="log"), title="TOP-K"), y=alt.Y("alpha:Q", title="HILL α", scale=alt.Scale(zero=False))), 260)
    st.dataframe(pd.DataFrame(ST["sensitivity_D1"]).round(2), hide_index=True, width="stretch")

elif page == "Rule Explorer":
    section("RECONSTRUCT · signature", "Rule explorer", "Search the registry, open a rule, and inspect every piece of evidence behind it.")
    reg = pd.DataFrame(REG)
    q = st.text_input("Search rules (id, title, field, keyword)", key="rx_q", placeholder="e.g. currency, Gamma, C3, mule")
    f1, f2, f3, f4 = st.columns(4)
    lay = f1.multiselect("Feature group", sorted(reg.group.unique()), key="rx_group")
    con_ = f2.multiselect("Confidence", ["High", "Medium", "Low"], key="rx_conf")
    typ = f3.multiselect("Rule type", sorted(reg.type.unique()), key="rx_type", help="A deterministic · B probabilistic · C conditional · D template · E composite")
    stt = f4.multiselect("Status", sorted(reg.status.unique()), key="rx_status")
    v = reg.copy()
    if q:
        ql = q.lower(); v = v[v.apply(lambda r: ql in " ".join(str(r[c]) for c in ("id", "title", "fields", "hypothesis", "formulation", "group")).lower(), axis=1)]
    for col, sel in (("group", lay), ("confidence", con_), ("type", typ), ("status", stt)):
        if sel:
            v = v[v[col].isin(sel)]
    if v.empty:
        card("No rule matches. Clear the search or filters.", "y")
        st.stop()
    st.dataframe(v[["id", "group", "type", "confidence", "status", "title"]], hide_index=True, width="stretch", height=250)
    opts = v.id.tolist()
    if st.session_state.get("rx_pick") not in opts:
        st.session_state["rx_pick"] = opts[0]
    rid = st.selectbox("Open rule", opts, format_func=lambda i: f"{i} · {RULES[i]['title']}", key="rx_pick")
    r = RULES[rid]
    a, b = st.columns([3, 2])
    with a:
        card(f"<span class='tag {r['status']}'>{r['status']}</span><span class='tag {r['confidence']}'>{r['confidence'].upper()} CONFIDENCE</span>"
             f"<span class='mono'>{rid} · TYPE {r['type']} · {r['group']}</span><h2 style='margin:.4rem 0'>{r['title']}</h2>"
             f"<p><b>Hypothesis.</b> {r['hypothesis']}</p><div class='mono'>Explicit rule</div><div class='formula'>{r['formulation']}</div>"
             f"<div class='mono'>Mathematical / computational logic</div><div class='formula'>{r['logic']}</div>"
             f"<p><b>Fields.</b> {r['fields']}</p><p><b>Method.</b> {r['method']}</p><div class='formula'>ACCEPT IF · {r['criterion']}</div>")
        card(f"<p><b>Counterexamples / exceptions.</b> {r['counterexamples']}</p><p><b>Limitations.</b> {r['limitations']}</p>"
             f"<p><b>Economic interpretation</b> <span class='mono'>(interpretation, not proven by data)</span>. {r['economic']}</p>")
    with b:
        kp = [("Sample size", r["sample_size"]), ("Effect size", r["effect_size"]), ("Validation", r["validation"]), ("Confidence", r["confidence"])]
        card("".join(f"<div class='mono'>{k}</div><div style='font-weight:600;margin-bottom:8px'>{v_}</div>" for k, v_ in kp))
        mtr = r["metrics"]
        if isinstance(mtr, dict) and mtr and all(isinstance(v_, dict) for v_ in mtr.values()):
            md = pd.DataFrame(mtr).T
            st.markdown("<div class='mono'>Statistical results by split</div>", unsafe_allow_html=True)
            st.dataframe(md, width="stretch")
            num = [c for c in md.columns if pd.api.types.is_numeric_dtype(md[c]) and md[c].notna().sum() >= 3 and c not in ("n", "n_sample")]
            if num:
                col = st.selectbox("Plot metric across splits", num, key=f"rx_metric_{rid}")
                pdf = md[[col]].dropna().reset_index().rename(columns={"index": "split"})
                chart(alt.Chart(pdf, title=f"{col}: stability across independent splits").mark_bar(stroke=INK, strokeWidth=1.5, color=CONF_COL[r["confidence"]]).encode(
                    x=alt.X("split:N", title=None), y=alt.Y(f"{col}:Q", title=col.upper(), scale=alt.Scale(zero=False)), tooltip=["split", alt.Tooltip(f"{col}:Q", format=".5g")]), 220)
        rep = EVD / "reports" / f"{rid}.md"
        if rep.exists():
            st.download_button("Download evidence report (.md)", rep.read_text(encoding="utf-8"), file_name=f"{rid}_evidence_report.md", mime="text/markdown", key=f"dl_{rid}")
        rel = [e for e in AT["edges"] if rid in e["rules"]]
        if rel:
            nm = {n_["id"]: n_["label"] for n_ in AT["nodes"]}
            card("<div class='mono'>Atlas edges supported by this rule</div>" + "".join(f"<div>{nm[e['source']]} → {nm[e['target']]} <span class='tag'>{e['kind']}</span></div>" for e in rel))
        card(f"<div class='mono' style='color:{YELLOW}'>Trace</div>validator <b>src/rules.py · {rid}</b><br>report findings/validation_report.md<br>run {VA['generated']}", "ink")

elif page == "Dependency Atlas":
    section("RECONSTRUCT · EXPLAIN · signature", "Rule dependency atlas",
            "The reconstructed generator as a dependency map. Edges are generation dependencies consistent with the data — never causal claims. Select a field to trace its rules.")
    nodes = {n_["id"]: n_ for n_ in AT["nodes"]}
    k1, k2 = st.columns([2, 3])
    focus = k1.selectbox("Focus on field", ["(all)"] + [n_["label"] for n_ in AT["nodes"]], key="at_focus")
    kinds = k2.multiselect("Edge kinds", list(AT["legend"]), default=list(AT["legend"]), key="at_kinds")
    fid = next((i for i, n_ in nodes.items() if n_["label"] == focus), None)
    STY = {"deterministic": (INK, 3.2, "none"), "stochastic": (BLUE, 2.2, "none"), "unresolved": (BLUE, 2.2, "8 5"),
           "independent": (GREY, 1.6, "4 4"), "confounded": ("#9a7b00", 1.8, "1 4")}
    OX, OY, W_, H_ = 95, 34, 178, 36
    svg = [f"<svg viewBox='0 0 1380 590' width='100%' style='min-width:900px;font-family:Segoe UI, sans-serif'><defs>"]
    for k_, (c_, w_, _) in STY.items():
        svg.append(f"<marker id='ar_{k_}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='7' markerHeight='7' orient='auto-start-reverse'><path d='M0,0 L10,5 L0,10 z' fill='{c_}'/></marker>")
    svg.append("</defs>")
    for e in AT["edges"]:
        if e["kind"] not in kinds:
            continue
        a_, b_ = nodes[e["source"]], nodes[e["target"]]
        x1, y1, x2, y2 = a_["x"] + OX, a_["y"] + OY, b_["x"] + OX, b_["y"] + OY
        dx, dy = x2 - x1, y2 - y1; L = max((dx * dx + dy * dy) ** .5, 1)
        x2s, y2s = x2 - dx / L * 24, y2 - dy / L * 22
        c_, w_, da = STY[e["kind"]]; on = fid is None or fid in (e["source"], e["target"])
        mk = "" if e["kind"] in ("independent", "confounded") else f"marker-end='url(#ar_{e['kind']})'"
        svg.append(f"<line x1='{x1}' y1='{y1}' x2='{x2s:.0f}' y2='{y2s:.0f}' stroke='{c_}' stroke-width='{w_}' stroke-dasharray='{da}' {mk} opacity='{1 if on else .1}'>"
                   f"<title>{a_['label']} → {b_['label']} · {e['kind']} · {', '.join(e['rules'])}: {e['evidence']}</title></line>")
        if e["kind"] in ("independent", "confounded", "unresolved") and on:
            sym = {"independent": "⟂", "confounded": "≈", "unresolved": "?"}[e["kind"]]
            svg.append(f"<text x='{(x1 + x2) / 2:.0f}' y='{(y1 + y2) / 2 - 4:.0f}' font-size='15' font-weight='700' fill='{c_}' text-anchor='middle'>{sym}</text>")
    for i, n_ in nodes.items():
        x, y = n_["x"] + OX, n_["y"] + OY; on = fid is None or fid == i or any(fid in (e["source"], e["target"]) and i in (e["source"], e["target"]) for e in AT["edges"] if e["kind"] in kinds)
        fill = YELLOW if i == fid else (WHITE if n_["kind"] == "field" else PAPER)
        svg.append(f"<g opacity='{1 if on else .25}'><rect x='{x - W_ / 2}' y='{y - H_ / 2}' width='{W_}' height='{H_}' fill='{fill}' stroke='{INK}' stroke-width='2.2' "
                   f"stroke-dasharray='{'5 3' if n_['kind'] == 'latent' else 'none'}'/><text x='{x}' y='{y + 4}' font-size='11' font-weight='600' text-anchor='middle' fill='{INK}'>{n_['label']}</text></g>")
    svg.append("</svg>")
    st.markdown(f"<div class='atlas'>{''.join(svg)}</div>", unsafe_allow_html=True)
    st.markdown(" · ".join(f"<span class='tag' style='border-color:{STY[k_][0]}'>{k_}</span> {AT['legend'][k_]}" for k_ in AT["legend"]) +
                "<br><span class='mono'>Solid box = dataset field · dashed box = latent generator entity · ⟂ tested independent · ≈ confounded · ? mechanism open</span>", unsafe_allow_html=True)
    ed = pd.DataFrame(AT["edges"]); ed = ed[ed.kind.isin(kinds)]
    if fid:
        ed = ed[(ed.source == fid) | (ed.target == fid)]
    nm = {i: n_["label"] for i, n_ in nodes.items()}
    ed = ed.assign(source=ed.source.map(nm), target=ed.target.map(nm), rules=ed.rules.map(", ".join))
    st.dataframe(ed[["source", "target", "kind", "rules", "status", "evidence"]], hide_index=True, width="stretch")
    if len(ed):
        rr = sorted({x.strip() for s_ in ed.rules for x in s_.split(",") if x.strip() in RULES})
        c1, c2 = st.columns([3, 1])
        pick = c1.selectbox("Open a supporting rule", rr, format_func=lambda i: f"{i} · {RULES[i]['title']}", key="at_rule")
        c2.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        c2.button("Open in Rule Explorer", key="at_go", on_click=goto, args=("Rule Explorer", pick))
    card(AT["note"], "y")

elif page == "Validation Centre":
    section("VALIDATE", "Validation centre", "Every rule's acceptance test on five independent splits, the two-implementation check, detector evaluation and data lineage.")
    xc = VA["cross_check"]
    kpis([(f"{n_pass}/{len(REG)}", "validators pass"), ("5", "splits: full · 2 halves · 2 periods"), (f"{xc['C2_python_match']:.0%}", "SQL vs Python (C2)"),
          (f"{VA['runtime_s']:.0f}s", "validation runtime"), ("OK" if LI["contract_ok"] else "FAIL", "schema contract")])
    rows = []
    for r in REG:
        m_ = r["metrics"]; key = r["effect_size"].split(" = ")[0]
        row = dict(id=r["id"], group=r["group"], confidence=r["confidence"], status=r["status"], metric=key)
        if isinstance(m_, dict):
            for sp in ("full", "half_0", "half_1", "P1", "P2"):
                vv = m_.get(sp, {}).get(key) if isinstance(m_.get(sp), dict) else None
                row[sp] = vv
        rows.append(row)
    st.subheader("Validation matrix: headline metric on each split")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=420,
                 column_config={sp: st.column_config.NumberColumn(sp, format="%.4g") for sp in ("full", "half_0", "half_1", "P1", "P2")})
    st.subheader("Signature detectors, per class (no accuracy reported)")
    st.dataframe(pd.DataFrame(ST["detectors"])[["label", "detector", "precision", "recall", "f1", "tp", "fp", "fn"]].round(4), hide_index=True, width="stretch")
    st.subheader("Data lineage: dashboard number → artefact → producer → input")
    la = pd.DataFrame(LI["artefacts"]); la["sha256"] = la.sha256.str[:16] + "…"
    st.dataframe(la[["path", "producer", "inputs", "rows", "bytes", "sha256", "modified"]], hide_index=True, width="stretch")
    st.dataframe(pd.DataFrame(LI["schema_contract"]), hide_index=True, width="stretch")

elif page == "Methodology & Lineage":
    section("EXPLAIN", "Methodology & lineage", "How every rule was found, tested, challenged and replicated — and what we could not explain.")
    steps = [("01 DISCOVER", "Automated scan of all feature pairs + decision-tree search + forensics (fingerprints, change points); development half only."),
             ("02 RECONSTRUCT", "Each discovery written as an explicit rule with formula and computational logic; typed A deterministic … E composite."),
             ("03 VALIDATE", "Acceptance criteria on effect size; five splits; out-of-sample classes; Simpson checks; Bonferroni; SQL vs Python."),
             ("04 EXPLAIN", "Dependency atlas; economic reading labelled as interpretation; limitations and negative results kept.")]
    cols = st.columns(4)
    for c_, (k_, t_) in zip(cols, steps):
        c_.markdown(f"<div class='card'><div class='mono'>{k_}</div><div style='font-size:.9rem'>{t_}</div></div>", unsafe_allow_html=True)
    st.subheader("Pipeline (each step regenerates its artefact; hashes in the Validation Centre)")
    card("<div class='formula'>" + " → ".join(LI["pipeline"]) + "</div>" + f"Environment: Python {LI['environment']['python']} · " +
         " · ".join(f"{k} {v_}" for k, v_ in LI["environment"]["packages"].items() if v_))
    st.subheader("Known limitations and negative results")
    for lim in ["G1: bank-pair affinities exist, mechanism not identified.", "T4: weekly level values are not explained (their timing is: Mondays, T4b).",
                "F1: no fixed exchange rate restores round originals for EUR/GBP/CHF.", "X5: CUSTOMER_RECALL (undocumented label) shows no signature.",
                "Offsets estimated in whole hours; home-currency map inferred from data (validated indirectly by C2)."]:
        st.markdown(f"- {lim}")
    st.subheader("Disclosure")
    card("Primary data: Swift UMDAC Datathon 2026 fictitious payment dataset (provided); only aggregates are shown. External references are context only and must be verified by the team. "
         "AI assistance was used for coding and drafting (permitted, RR 3.6). Independent student prototype — not affiliated with or endorsed by Swift.")
