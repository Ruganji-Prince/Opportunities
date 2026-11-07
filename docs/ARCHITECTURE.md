# Architecture and data contract

Python 3.11+ runs offline-testable normalization, matching, deduplication and deadline logic. Public JSON APIs and an RSS feed provide live records. Adapters never bypass authentication, CAPTCHAs or robots restrictions. A source is staged before merge: a partial download or schema failure preserves the last verified records. Missing listings are not automatically declared closed.

The pipeline exports active records, an archive, source-health status and successful alert-delivery IDs under `data/`. Writes use atomic replacement. Canonical URLs determine stable IDs; normalized title, organization and location provide a secondary duplicate check. Existing first-discovered timestamps survive updates. Changed deadlines update the existing record. Unknown application status remains unknown rather than being asserted open.

The React/TypeScript/Vite client reads only the three public dashboard feeds; alert delivery state is not copied into the frontend build. React escapes all extracted text and URL schemes are checked. No raw HTML is injected. Every 30 seconds the client recomputes expiry, status, counts, filters and ordering from its current clock, and every 15 minutes it reloads the published feeds. Expired records move to the browser archive even before the next scheduled collection.

The schema is defined by `frontend/src/types.ts` and constructed in `src/core.py`. Unknown scalar fields use `unknown` or null. Deadline precision is `timestamp`, `date`, `rolling` or `unknown`. Raw source URLs, deadline evidence and source names are retained. Descriptions may include publisher boilerplate and should be checked against the original announcement.

Personal tracker data uses one versioned localStorage key. Notes, preparation deadlines and stages are never sent to the repository, a server or a third party by this app. Export/import validates record IDs and structure and merges only application records. The public profile is intentionally sanitized; raw CVs belong under ignored `private/`.

The `.yaml` configuration files use the JSON subset of YAML so the collector has no YAML dependency. Edit them as valid JSON, using quoted keys and no comments.

Limitations: English keyword matching is heuristic; nationality, visas, completed-MSc timing, startup incorporation, and qualifications often require human confirmation. Remote location does not imply worldwide eligibility. No model API or embedding provider is required. No full-text CV ingestion service or account synchronization is enabled. Funding amount ordering requires disclosed amounts in one selected currency. These sources often publish no exact deadline; unknown deadlines remain visible after dated and rolling records.
