# Sources and extension guide

Configured live integrations:

| Source | Adapter | Coverage | Policy / contract |
| --- | --- | --- | --- |
| Anthropic | Greenhouse | AI research and engineering | [Public Job Board API](https://docs.greenhouse.io/job-board.html) |
| Recursion Pharmaceuticals | Greenhouse | AI for scientific discovery and health | Same public API |
| Cohere | Ashby | LLM research, internships and engineering | [Public posting API](https://developers.ashbyhq.com/docs/public-job-posting-api) |
| CERN | SmartRecruiters | Technical students, graduates and research engineering | [Posting API](https://developers.smartrecruiters.com/docs/posting-api) |
| Opportunities for Africans | RSS | Africa-focused scholarships, grants, development and competitions | Public syndication feed, checked against robots.txt, publisher attribution retained |
| Remotive | Public API | Remote engineering careers | [API rules](https://github.com/remotive-com/remote-jobs-api); links point to Remotive, source attribution shown |

Expanded research and regional integrations:

| Publisher / feed | Method | Verified scope |
| --- | --- | --- |
| EURAXESS | Public RSS and robots-permitted detail pages | Research and doctoral announcements, source-labeled timestamp deadlines and host countries |
| DAAD PhDGermany | Official structured RSS | Doctoral positions including AI, computing, materials and engineering; explicit applicationDeadline and location fields |
| University of Bath | Official vacancy RSS | Research, scientific and engineering roles; source-published closing dates |
| Oxford Computer Science | Official research and studentship RSS | Research announcements; the studentship feed was empty during verification |
| University of Southampton | Official funded-PhD RSS | Funded doctoral category; feed was empty during verification |
| Opportunities for Africans PhD/fellowship/contest feeds | Publisher RSS and public articles | African audiences, scholarships and innovation competitions; confirm eligibility per organizer |
| One Acre Fund and Zipline | Original employers' public Greenhouse APIs | Technical, research and analytics roles with explicitly listed Rwanda/East Africa/Africa locations |
| Job in Rwanda | Discovery link only; collection disabled | Terms prohibit automated extraction and republication without prior written permission |

There are 17 enabled integrations across 13 publishers. Each integration's actual status, last success, count and detail failures are in `data/refresh_status.json` and the Sources view. A successful empty feed remains empty. Funding availability does not establish coverage of international tuition, travel or every nationality. OFA and DAAD are aggregators: follow the announcement to the organizer and verify conditions.

The official feed directories are [Oxford](https://www.cs.ox.ac.uk/rssfeeds.html), [Bath](https://www.bath.ac.uk/jobs/rss/), [Southampton](https://jobs.soton.ac.uk/RSS/) and [DAAD](https://www.daad.de/en/studying-in-germany/phd-studies-research/phd-germany/). EURAXESS exposes its public `/job-feed`. Robots rules are checked for feed and detail URLs. A missing robots.txt (404) is treated as absence of a policy file; explicit 401/403 access denials and 429 rate limits are not ignored.

Zindi remains discovery-only: its [terms](https://zindi.world/terms) restrict monitoring and republication. No datasets, authenticated content or competition listings are scraped. Job in Rwanda's `/rss.xml` contains FAQs, not vacancies. Its [terms](https://www.jobinrwanda.com/page/terms-use) explicitly prohibit automated extraction and republication without written permission, overriding robots allowance. The initially attempted adapter was disabled, its current-feed records were removed, and a regression test now prevents requests to permission-gated sources. Regional collection uses original-employer public APIs instead. AIMS was reviewed but no stable structured opportunity feed was verified. Surrey's doctoral RSS was empty. Nottingham's certificate validation failed; certificate verification was not disabled. Other suggested sites require separate policy and schema review. No anti-bot bypass is implemented.

HTML enrichment is bounded per source and retains feed evidence when an optional detail page fails. RSS declaration encodings and Atom namespaces are supported. Unknown deadlines and funding remain unknown; no placeholder opportunities are published.

To add a source:

1. Review its official API/feed documentation, access restrictions, terms, robots rules and rate limits.
2. Add an entry in `config/sources.yaml` with a stable ID, public URL, adapter, organization, policy link and enabled flag.
3. Reuse a supported public API adapter where possible. Otherwise implement an adapter in `src/collectors.py` yielding title, original URL, description and any verified optional fields. Never guess deadline years, funding, nationality coverage or application URLs.
4. Add offline extraction fixtures and tests. Run `python -m src.pipeline --sources ID`, inspect source health and original announcements, then `python -m src.pipeline --validate`.
5. If its maximum frequency is below four per day, add a dedicated schedule or per-source interval guard before enabling it in the shared six-hour workflow.

Remotive permits a maximum of four API requests per day. A six-hour minimum interval uses the last successful feed when manual runs occur earlier; automatic retries are disabled for this source. Use `--sources` to test other sources without fetching Remotive. An HTTP 429 should be treated as a signal to pause that source, never evade it. Repeated unsuccessful manual runs still require operator care to avoid exceeding the provider limit.

URL validation distinguishes an API-provided URL from a successful individual HTTP check. `python -m src.pipeline --verify-links 15` checks a bounded set of highly relevant records. A failure is recorded without declaring closure.
