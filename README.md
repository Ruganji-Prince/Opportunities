# OpportunityRadar 2.0

[Open the public website](https://ruganji-prince.github.io/Opportunities/).
A free React/TypeScript opportunity search website deployed to GitHub Pages, with Python collectors running on GitHub Actions. No account or paid service is needed to browse.

The public homepage offers search, five category filters, geographic/funding/deadline filters, publisher-diverse recommendations and 12 results at a time. Cards show essential facts; accessible dialogs load details on demand. `?opportunity=<stable-id>` links open a specific announcement. Search includes country, organization and field, with case/punctuation normalization.

Your optional MSc AI recommendations are available through Top Opportunities for You and More Filters. Dynamic collections include doctoral funding, Fall 2027 intake, research, internships and regional opportunities. Archive browsing remains under More Filters, with explicit Expired/Closed labels. Public browsing never uses the owner's personal eligibility or CV score as a gate. Personal notes and application stages stay in the existing browser-only tracker, with import/export and no registration.

## Updates and truthful data

Collection runs at `17 */6 * * *` UTC (02:17, 08:17, 14:17, 20:17 Africa/Kigali), subject to GitHub scheduling delays. Each source has independent health, robots/permission checks and timeout handling. Detail requests use a separate bounded timeout so source outages cannot consume the whole collection window. Expired and explicitly closed calls are archived. Unknown dates remain unknown, network failures retain previous data, and date conflicts use the earlier disclosed deadline with a warning. The frontend updates its clock every 30 seconds and checks a versioned manifest every 15 minutes without clearing search/filter state.

Material updates trigger the existing Pages deployment. Timestamp-only commits are suppressed; a successful health refresh may publish after 24 hours to prevent stale freshness labels. Last updated reports actual collection time, not visitor time.

The browser initially loads compact listings; full descriptions are not included. Detail JSON contains short factual summaries and bounded source evidence. Original announcements remain the authority for application instructions, eligibility and funding. Funding badges require explicit reviewed evidence; paid employment is separate from verified full scholarship coverage. Remote does not imply worldwide work authorization.

## Sources and restrictions

Enabled integrations cover official employer APIs, EURAXESS, DAAD, university and institute feeds, and attributed opportunity directories. Added research coverage includes Hereon, UFZ, DFG, Sussex and Nottingham, with original-announcement watchers for Max Planck Biomedical AI, SINTEF, Sussex QIST, MoveNow and Imagine Cup. See the About page for actual operational status and last success, including empty feeds and unavailable detail pages.

Zindi and Job in Rwanda remain discovery-only pending permission. Additional CMU-Africa, AIMS Rwanda, University of Rwanda, AU, Kaggle, Devpost and academic directory links are discovery-only; they are not counted as functioning collectors. No login, robots or anti-bot restriction is bypassed.

## Development and checks

```sh
pip install -r requirements.txt
python scripts/check.py
python scripts/refresh.py
python -m src.pipeline --validate
cd frontend
npm ci
npm test
npm run build
```

`node scripts/browser_qa.mjs` from the repository root tests the production build with installed Chrome; set `CHROME_BINARY` on non-Windows systems. `RADAR_QA_URL` targets the deployed site. Tests cover sharing, bookmarks, private notes, source visibility, mobile layout and 200% text scaling. Screenshots are local ignored artifacts.

The public site uses free static hosting and scheduled repository workflows within GitHub's free-tier limits. It is periodic discovery, not exhaustive or real-time internet coverage. No raw CV, private notes or credentials belong in this repository.
