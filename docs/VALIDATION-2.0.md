# OpportunityRadar 2.0 validation

Existing repository and GitHub Pages history retained. Public browsing is independent of CV matching; the optional personal dashboard includes dynamic doctoral, research, regional, internship and innovation collections. Existing localStorage key, stages, import/export, calendar export and notes are preserved.

Local verification: 68 backend tests, 23 frontend tests, TypeScript and production Vite build pass. Chrome acceptance covers 12-card pagination, category filters, earliest deadlines, publisher diversity, share links and reload, private notes, personal funding views, keyboard dismissal, 390px mobile layout and 200% text scaling on phone/desktop. No browser exceptions observed.

Full source collection completed with independent source health. Microsoft Imagine Cup returned HTTP 403; no restriction was bypassed. EURAXESS provided feed records while some detail requests failed; failures remain explicit. Empty Southampton and Oxford studentship feeds were not populated artificially. Discovery-only providers are not counted as successful collectors.

New adapter tests cover Hereon administrative filtering and conflicting dates, numeric application deadlines, funding certainty, graduation cutoffs, German language constraints, stable DAAD identities, and preventing expired cycles from reopening without evidence. Public ranking and personal curation tests cover senior roles, urgency, stale reviews and startup requirements.

Source findings: Max Planck Biomedical AI has a December 2026 deadline and September 2027 intake; final MSc documents before entry remain necessary. Hereon magnesium materials source dates conflict, so the earlier date is retained with a warning. SINTEF requires MSc completion before January 2027. The automated-driving position requires German C1. Anthropic Safety's old cohort is closed despite general rolling language. Research interests are never asserted as CV-demonstrated skills.

Local counts before the next production refresh:

```json
{
  "active": 589,
  "archived": 28,
  "new_active_since_530_baseline": 64,
  "new_with_individual_link_check": 10,
  "recommended": 213,
  "doctoral": 57,
  "fully_funded_verified": 2,
  "rwanda_east_africa": 5,
  "categories": {
    "research": 175,
    "industry": 405,
    "innovation": 9
  },
  "source_status": {
    "ok": 26,
    "failed": 1
  },
  "last_successful_refresh": "2026-11-11T18:25:27.432935+00:00"
}
```

Counts are collection snapshots, not guarantees that every unknown-deadline listing remains open. Source attribution, freshness and conditions remain available in details. Live deployment and production collection outcomes are reported after GitHub Actions finishes.

## Production verification

GitHub Actions collection [43227558124](https://github.com/Ruganji-Prince/Opportunities/actions/runs/43227558124) completed successfully, committed updated data and deployed Pages automatically. Production Chrome checks passed, including real automatic expiry and a browser-isolated simulated manifest refresh without losing search state. Country aliases, archive browsing, and bounded detail-request timeouts received final regression coverage.

Source feed records are source-confirmed; the individual detail verification count is reported separately. Counts relative to the original 530-active historical baseline:

```json
{
  "active": 654,
  "archived": 34,
  "new_active": 129,
  "new_individual_verified": 35,
  "recommended": 225,
  "doctoral": 91,
  "fully_funded_verified": 2,
  "rwanda_east_africa": 5,
  "categories": {
    "research": 227,
    "industry": 416,
    "innovation": 11
  },
  "source_status": {
    "ok": 25,
    "failed": 2
  },
  "last_successful_refresh": "2026-11-12T13:28:12.398743+00:00"
}
```
