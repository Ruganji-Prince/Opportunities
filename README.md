# OpportunityRadar

Personal research, AI career and innovation intelligence, with automated public-source collection, transparent profile matching and a live deadline dashboard.

Published source: [Ruganji-Prince/Opportunities](https://github.com/Ruganji-Prince/Opportunities). **Live dashboard: https://ruganji-prince.github.io/Opportunities/**. GitHub Pages is enabled with GitHub Actions; collection automatically redeploys meaningful data updates. See [deployment and verification](docs/DEPLOYMENT.md).

Built for an MSc AI candidate at Carnegie Mellon University Africa (expected May 2027), with mechanical engineering, applied ML, scientific computing, energy and materials interests. The sanitized profile combines the supplied brief with locally reviewed CV evidence, including prosthetics research, CAD/CAM training, explainable ML, embedded systems and energy/health projects. The raw CV and contact details are excluded. Nationality and work authorization remain unknown.

## Run locally

Requires Python 3.11+ and Node 22. Install dependencies and collect real records:

```sh
python -m pip install -r requirements.txt
python -m src.pipeline
python -m src.pipeline --validate
python -m unittest discover -s tests -v
cd frontend
npm ci
npm test
npm run build
npm run dev
```

The repository includes genuine collected data; the UI never generates example opportunities. `npm run build` copies only public database/health feeds into the static output. Collection can fail when a source is offline; prior data is retained and failures are visible.

On Windows without Node, `python scripts/bootstrap_tools.py` downloads a checksum-verified portable Node 22 into ignored `.tools/`; `python scripts/run_frontend.py install`, `python scripts/run_frontend.py test` and `python scripts/run_frontend.py run build` use it. This is an optional local convenience, not a production dependency.

## What it does

- Sixteen enabled integrations: the original Anthropic, Recursion, Cohere, CERN, Opportunities for Africans and Remotive sources, plus EURAXESS, DAAD PhDGermany, official Bath/Oxford/Southampton feeds, specialist African PhD/fellowship/competition feeds, and Job in Rwanda. Empty university feeds are reported honestly. The Sources tab shows actual health, counts and last success.
- Stable normalized records, source and date evidence, canonical URL and attribute deduplication, safe text extraction, bounded retries and atomic JSON storage.
- Configurable 0–100 scoring with eligibility restrictions overriding keywords; skills and unverified interests stay separate.
- Deadline-first ranking with relevance tie breaks. Rolling and unknown deadlines follow dated listings. Expired records automatically move out of the active view as the browser clock advances.
- Research, careers, innovation, geographic, remote, funding, eligibility, specialization and deadline filters; multiple sort orders; responsive cards and details.
- Bookmarks, application stages, private notes, preparation deadlines, JSON backup/transfer and deadline ICS exports. Personal tracking stays in this browser's localStorage and does not automatically synchronize.
- Six-hour GitHub Actions collection, manual dispatch, test workflows and Pages deployment. Optional deduplicated GitHub Issue and Resend alerts after successful provider responses.

No external notifications are enabled by default. A configured workflow is not proof that it is running: inspect the GitHub Actions run and Pages deployment before claiming automation or publication.

## Customize and maintain

Configuration uses the JSON subset of YAML. Edit `config/profile.yaml` for verified education/skills and separate interests, `scoring.yaml` for weights, `sources.yaml` for enabled feeds, and `settings.yaml` for retries/timeouts and warning thresholds. Keep all raw CVs under ignored `private/` and manually review any imported claims.

See [architecture and limitations](docs/ARCHITECTURE.md), [sources and adding adapters](docs/SOURCES.md), [scoring and CV import](docs/SCORING.md), [updates and alert setup](docs/AUTOMATION.md), and [GitHub Pages deployment](docs/DEPLOYMENT.md).

## Verification and limits

Tests cover timestamp zones and DST, date-only uncertainty, expiry, rolling/unknown dates, duplicate postings, ineligibility, changed deadlines, outages, relevance ties, empty filters, live reordering, safe imports, URL handling, and notification delivery state. Frontend compilation and production build are required by CI.

Eligibility is frequently unknown: host country and remote status do not establish nationality or work permission. Descriptions and English keyword scoring can miss conditions. Exact dates are only extracted from explicitly labeled source evidence with a year; undisclosed dates/funding stay unknown. Coverage now includes university doctoral/research feeds and Rwanda-specific listings; short feed windows, empty feeds and access restrictions still limit completeness. Zindi remains discovery-only because its terms restrict republication. A successful source download does not guarantee each original listing is still accepting applications; follow the organizer link. Third-party opportunity content retains its original publisher's rights.
