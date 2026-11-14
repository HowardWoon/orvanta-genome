# Deploy the Synthetic Rule Intelligence Lab web edition to Vercel (team-only)

The static site is in `web/dist/` (it has no build step on Vercel). Rebuild it with `python -m src.webdata` (browser aggregates → `web/build_data/`) and `python -m src.web` (assembles `web/app/` + data + charts + PDFs into `web/dist/`).

**Why static?** Vercel cannot host Streamlit, which needs a long-running server with websockets. The Streamlit prototype (`dashboard/app.py`) stays the local demo, and this site is the hosted edition. Both read the same evidence files.

## One-time setup
```bash
npm i -g vercel
```
```bash
vercel login
```

## Deploy as a protected preview (recommended until judging is over)
```bash
cd web/dist
```
```bash
vercel deploy
```
`vercel deploy` without `--prod` creates a **preview** deployment. On every Vercel plan, Vercel Authentication (Standard Protection) is on by default for previews, so only signed-in members of your Vercel team can open it. Invite your two teammates to the team so they can view it. Confirm the setting under Project → Settings → Deployment Protection → *Vercel Authentication: Standard Protection*.

Do **not** run `vercel deploy --prod` before 19 Nov 2026 12:00. Under Standard Protection the production `*.vercel.app` domain is public, and Rules 3.3 / 2.2 prohibit sharing solutions or dataset-derived content outside the team. On a Pro plan you can set protection to *All Deployments* instead.

## What ships
- `index.html`, `app.css`, `js/` (vanilla ES modules: router, chart kit, cube engine, simulator, rule port, one module per page group)
- `data/*.json`: aggregates only (explorer cube, route patterns with n ≥ 150, top-600 banks, summary statistics) — lazy-loaded per page
- `charts/*.png`
- `downloads/` (the two PDFs + the validation report)
- `vercel.json`: `noindex`, CSP (`script-src 'self'`), `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`; `robots.txt` disallows crawling

## Current deployment (14 Nov 2026)
- Project: `synthetic-rule-lab` (Vercel scope howardwoonhz06-3573s-projects)
- **Latest preview (14 Nov 2026, dashboard v2):** https://synthetic-rule-6yihwfn14-howardwoonhz06-3573s-projects.vercel.app. Deployment Protection was switched off on 14 Nov at the team's request, so previews are currently **public** until the team re-enables protection.
- Previous preview: https://synthetic-rule-jhltu5z2e-howardwoonhz06-3573s-projects.vercel.app — ORVANTA final (49 routes, research report download) (protected by Vercel Authentication; anonymous requests to every path, including data files, are redirected to sign-in — verified 14 Nov 2026). Earlier previews (j3073i00i, ez1ikg8vs, lijsr3qvp, gdqjr66o8) are superseded.
- Public production domain `synthetic-rule-lab.vercel.app` serves only a "This project is private" placeholder (no data, noindex). Vercel requires a project's first deployment to be production, so a placeholder took that slot.
- Redeploy after `python -m src.web` (the project link and `.vercelignore` are preserved): `cd web/dist` then `vercel deploy --target=preview --yes`. Never use `--prod` before judging ends.
- `.vercelignore` excludes `.env*` (the CLI writes a token there on `vercel link`). Verified that `/.env.local` returns 404 on the deployment.

## After judging: make it public (one command)
Only after the submission deadline (19 Nov 2026, 12:00 PM) **and** once the team agrees the results may be shared:
```bash
cd web/dist && vercel deploy --prod --yes
```
This replaces the private placeholder on `synthetic-rule-lab.vercel.app` with the real site; under Standard Protection the production domain is public. To keep using only the protected preview, never run this command. To roll back to the placeholder, run `vercel rollback` and pick the placeholder deployment.
