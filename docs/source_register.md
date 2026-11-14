# Source register

**Primary evidence:** only the Swift-provided dataset (10,000,000 rows). No external dataset enters rule discovery, validation or any number in the deliverables.

Official competition sources: see `competition_requirements.md` (CS, SF, RR, JC, HB, BR).

## External references — verification status (checked 14 Nov 2026)
Used **only** to support economic interpretation, never as data. Each URL was opened (WebFetch or the in-app browser) and the title, publisher, date and relevant content were read.

| # | Reference (APA 7) | Status | Actual publication details | Relevant content | Supports | In deliverables? |
|---|---|---|---|---|---|---|
| 1 | Committee on Payments and Market Infrastructures. (2016, July). *Correspondent banking*. Bank for International Settlements. https://www.bis.org/cpmi/publ/d147.htm | **Verified** | CPMI final report "Correspondent banking", July 2016, BIS website | defines correspondent banking and its arrangement types; recommendations on KYC, LEI, payment messages. The landing page does **not** discuss cover payments or declining relationships | reading of R1/R3 as correspondent chains (definition only). The cover-method reading of R2 is our interpretation, not attributed to this source | Yes (slide 20) |
| 2 | Financial Stability Board. (2020, October 13). *Enhancing cross-border payments: Stage 3 roadmap*. https://www.fsb.org/2020/10/enhancing-cross-border-payments-stage-3-roadmap/ | **Verified** | FSB, 13 Oct 2020 | cross-border payments are expensive, slow, hard to access and opaque | D1/D2 (manual processing as the speed friction), R4 (transparency) | Yes |
| 3 | Swift. (n.d.). *Swift GPI*. Retrieved November 14, 2026, from https://www.swift.com/products/swift-gpi | **Verified** (old URL `/our-solutions/swift-gpi` redirects here) | Swift product page, undated | end-to-end tracking, transparency on deductions and processing times; "nearly 60% … credited within 30 minutes" | reading of hidden hops (R4) and delays | Yes (added, corrected URL) |
| 4 | Bank for International Settlements. (2022, October 27). *OTC foreign exchange turnover in April 2022* [Triennial Central Bank Survey]. https://www.bis.org/statistics/rpfx22.htm | **Verified** (title corrected from the generic survey name) | BIS, 27 Oct 2022 | USD on one side of 88% of trades; EUR 30.5% | C1/C3 and H38: EUR and USD as vehicle currencies | Yes (added) |
| 5 | Swift. (n.d.). *International Bank Account Number (IBAN)*. Retrieved November 14, 2026, from https://www.swift.com/standards/data-standards/iban-international-bank-account-number | **Verified** (title corrected from "IBAN registry") | Swift standards page, undated | ISO 13616; national IBAN formats; Swift is registration authority and publishes the IBAN Registry | P2 (IBAN formats per country) | Yes |
| 6 | UK Finance. (2024). *Annual fraud report 2024*. https://www.ukfinance.org.uk/policy-and-guidance/reports-and-publications/annual-fraud-report-2024 | **Not verified** | URL redirects to a members' login page; the report content could not be opened from the primary source (secondary summaries disagree on figures) | — | was intended for X1/X4 interpretation | **Removed** (never cited in the PDFs) |

The X1/X4 readings (romance and CEO scams as authorised push-payment fraud) remain labelled as general interpretation without a citation.

Tools: Python 3.12.3, DuckDB 1.5.2, pandas 3.1, NumPy, SciPy 1.17, scikit-learn 1.8 (GaussianMixture for X3 only), matplotlib 3.10, Streamlit 1.57 + Altair 6.1, pytest 9.1, pypdf 6.19, Playwright 1.55 with Microsoft Edge (PDF rendering and browser tests). AI assistance (Claude) was used for code and drafting, as RR 3.6 permits; every number was recomputed by the scripts in `src/`.
