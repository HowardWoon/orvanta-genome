# Competitive benchmark (14 Nov 2026)

## What we tried to verify
Public web searches (standard mode, 14 Nov 2026) for the UMDAC Datathon champions named in the brief: *Later Eat What* (2025), *Hokkien Mee is Red* (2024), *VenturaVenti* (2023).

| Claim | Verified? | What the public record shows |
|---|---|---|
| UMDAC (Universiti Malaya Data Analytics Club) runs an annual Datathon | **Yes** | USM School of Computer Sciences news: its students placed 2nd runner-up at the UMDAC Datathon 2024 (27 Dec 2024), theme *cryptocurrency analytics* — [cs.usm.my](https://cs.usm.my/index.php/news/news-cs/832-congratulations-datathon-2024-organized-by-universiti-malaya-data-analytics-club-umdac) |
| UMDAC also runs a Data Science Digital Race | Yes | UM news on the first Digital Race (RM10,000 prizes) — [um.edu.my](https://www.um.edu.my/news/umdac-successfully-concludes-first-ever-digital-race-with-overall-rm10-000-in-prizes-and-certifications) |
| *Later Eat What* won 2025 | **Not verified** | no indexed source found |
| *Hokkien Mee is Red* won 2024 | **Not verified** | a team of that name appears at Monash Varsity Hackathon 2025 — [monash.edu.my](https://www.monash.edu.my/IT/news-and-events/articles/2025/varsity-hackathon-2025) — a different event; no source ties it to the UMDAC 2024 title |
| *VenturaVenti* won 2023 | **Not verified** | no indexed source found |
| Content of any winning solution | **Not available** | no public write-ups, decks or repositories were found |

We therefore do **not** describe what those teams built. The team can ask the organisers or check UMDAC's own channels (Instagram/LinkedIn) for the official results.

## Lessons we can defend (from the official rubric and case, not from rumoured winners)
| Rubric weight | What wins points | How ORVANTA answers it |
|---|---|---|
| Insight 45% | specific, quantified, conditional rules with scope and exceptions | 34 rules with formula, scope, effect size and counterexamples; exact rules (C2 9,999,998/10M; R6/R7/P2 zero violations) next to probabilistic ones with fitted parameters |
| Evidence 23% | traceable claims, independent validation, data integrity | 5-split validation, SQL ↔ Python ↔ JS rule parity, 459-record evidence ledger with artefact SHA-256, Forensic Replay of real records |
| Communication 20% | a dashboard that stands alone; clear narrative | 15-page dashboard PDF + 20 slides + research report; web platform opens on the headline finding and the six-stage journey |
| Economics 12% | plausible mechanisms, observation kept separate from interpretation | labelled economic readings per rule; synthetic-data caveats on every surface |

## Where we differentiate
1. **Generator reconstruction, not description** — a blueprint of the generator by generation stage, with unresolved parts left open.
2. **Falsification built in** — rejected hypotheses kept (29), genealogy from the logged hypothesis order, counterexample records one click away.
3. **Runnable reconstruction** — the Scenario Studio simulates the reconstructed rules and measures the fit (KS) against observation.
4. **Discipline over volume** — per-family BH, out-of-sample bank classes, Simpson checks, sensitivity sweeps.

## Risks relative to strong competitors
- A team that recovers the vehicle-currency mechanism (C3's 1.3% outside-route share) or the bank-pair affinity (G1) would out-score us on those two points.
- Teams with a polished narrative deck may communicate faster; our slides are content-complete but the pitch team owns visual polish.
