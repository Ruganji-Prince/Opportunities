# Deployment and dynamic-system verification — 7 November 2026

Live dashboard: **https://ruganji-prince.github.io/Opportunities/**

The existing repository and history are preserved. GitHub CLI authentication as `Ruganji-Prince` had admin/push permissions. The Pages REST API successfully enabled `build_type: workflow`; the existing deployment workflow completed successfully. No restriction was bypassed and no new repository was created.

The [first production collection](https://github.com/Ruganji-Prince/Opportunities/actions/runs/42392157865) succeeded, discovered four new source IDs, exported 480 unique active records after deduplication, committed the changes, and invoked the reusable Pages deployment successfully. The live feed matched its refresh timestamp and record count.

Expanded local release snapshot: 538 active records and 17 archived records, including 34 doctoral opportunities and 3 with explicit funding evidence. These are source-backed records, not a claim of confirmed eligibility or guaranteed continued acceptance. Counts change with each collection. Research/industry/innovation and geographic eligibility remain separate attributes.

Verification completed locally:

- **56 backend tests** pass, including real-source-shaped feed/detail extraction, encodings, Atom, robots denial handling, source outages, updated deadlines and salaries, repeated ingestion without duplicate IDs, incomplete-institution duplicate safety, expiry/archival, timezones/DST, CV matching and alert deduplication.
- **11 frontend tests** pass, including deadline/relevance ordering, changes to published deadlines, approaching-deadline warning transitions, date-only uncertainty, empty filters, URL safety and tracker import/export.
- TypeScript and the production Vite build succeed using the existing pinned lockfile.
- Real Chrome loads production-format feeds, checks counts and unique IDs, confirms deadline order, persists bookmarks/notes across reload, handles empty searches and source health, and fits a 390px viewport without overflow.
- Advancing only the test browser clock through a real opportunity's closing time and its 30-second timer removes that card without reloading; it becomes searchable in Archive. Published records and real deadlines are not modified by this test.

There are **16 enabled integrations** across 12 publishers, including EURAXESS, DAAD, institutional university feeds, regional scholarship/competition feeds and Job in Rwanda. Southampton's funded-PhD feed and Oxford's studentship feed were empty and remain empty; no placeholders are added. Zindi remains discovery-only because its terms restrict republication. See [source policies and limitations](SOURCES.md).

Collection remains scheduled at `17 */6 * * *` UTC (02:17, 08:17, 14:17, 20:17 CAT) with manual dispatch. Data commits explicitly call the reusable deployment workflow, so token-created commits do not depend on a push event. [GitHub Actions](https://github.com/Ruganji-Prince/Opportunities/actions) records production runs and their current outcomes. The browser reloads published feeds every 15 minutes and recomputes clocks, expiry, counts and order every 30 seconds.

No required manual hosting step remains. External GitHub Issue/email alerts remain optional and disabled until configured. Raw CV, personal contact details, private application records, credentials and local tools are excluded from the public repository.
