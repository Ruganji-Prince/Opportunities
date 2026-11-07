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

Each source's actual current collection result, last success, count and failure message is in `data/refresh_status.json` and the dashboard Sources view. A working API does not imply every record is relevant or eligible. OFA is an aggregator; follow its article to the organizer and confirm requirements. Research coverage currently relies on employer and regional feeds; broad university PhD admissions coverage needs additional reviewed adapters.

EURAXESS, Zindi and Job in Rwanda are visible manual discovery entries. They are not claimed as connected or scraped. Other suggested sites (FindAPhD, Academic Positions, jobs.ac.uk, Kaggle, Devpost, F6S, MIFOTRA, AIMS, AU and university sites) require individual access-policy and extraction reviews before integration. No anti-bot bypass is implemented. Earlier candidate boards for DeepMind and Hugging Face were unavailable and are not included as working integrations.

To add a source:

1. Review its official API/feed documentation, access restrictions, terms, robots rules and rate limits.
2. Add an entry in `config/sources.yaml` with a stable ID, public URL, adapter, organization, policy link and enabled flag.
3. Reuse a supported public API adapter where possible. Otherwise implement an adapter in `src/collectors.py` yielding title, original URL, description and any verified optional fields. Never guess deadline years, funding, nationality coverage or application URLs.
4. Add offline extraction fixtures and tests. Run `python -m src.pipeline --sources ID`, inspect source health and original announcements, then `python -m src.pipeline --validate`.
5. If its maximum frequency is below four per day, add a dedicated schedule or per-source interval guard before enabling it in the shared six-hour workflow.

Remotive permits a maximum of four API requests per day. A six-hour minimum interval uses the last successful feed when manual runs occur earlier; automatic retries are disabled for this source. Use `--sources` to test other sources without fetching Remotive. An HTTP 429 should be treated as a signal to pause that source, never evade it. Repeated unsuccessful manual runs still require operator care to avoid exceeding the provider limit.

URL validation distinguishes an API-provided URL from a successful individual HTTP check. `python -m src.pipeline --verify-links 15` checks a bounded set of highly relevant records. A failure is recorded without declaring closure.
