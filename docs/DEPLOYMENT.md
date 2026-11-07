# Existing GitHub Pages deployment

Repository: [Ruganji-Prince/Opportunities](https://github.com/Ruganji-Prince/Opportunities).

Public dashboard: **https://ruganji-prince.github.io/Opportunities/**

GitHub Pages is enabled with `build_type: workflow` (GitHub Actions). The authenticated GitHub CLI account had repository admin access and successfully enabled Pages through the REST API. The original connector-only setup lacked that administration capability; no restriction was bypassed.

The existing `deploy-pages.yml` installs the lockfile, tests and builds React, uploads `frontend/dist`, and deploys through `actions/deploy-pages`. It supports pushes to `main`, manual dispatch, and reuse by the collection workflow. Token-created data commits explicitly invoke the reusable deployment rather than relying on another push event.

```sh
gh auth status
gh workflow run deploy-pages.yml --repo Ruganji-Prince/Opportunities --ref main
gh workflow run collect-opportunities.yml --repo Ruganji-Prince/Opportunities --ref main
gh run list --repo Ruganji-Prince/Opportunities
```

Normal collection runs every six hours at minute 17 UTC: 02:17, 08:17, 14:17 and 20:17 in Africa/Kigali and Africa/Johannesburg. GitHub may delay scheduled runs.

If hosting is disabled later, the owner can select **GitHub Actions** in [Settings → Pages](https://github.com/Ruganji-Prince/Opportunities/settings/pages). With authorized admin-capable CLI credentials, an absent Pages site can be created with `gh api --method POST repos/Ruganji-Prince/Opportunities/pages -f build_type=workflow`. For an existing site use `--method PUT`. If GitHub denies the call, use the owner setting; do not evade access restrictions. Never paste or commit tokens.

Verification checks the public page, assets, data feeds, unique record IDs and refresh timestamps. Real-Chrome QA can target production by setting `RADAR_QA_URL=https://ruganji-prince.github.io/Opportunities/` when running `node scripts/browser_qa.mjs`. It uses an isolated ignored browser profile. The expiry check advances only that test browser's clock, waits through a virtual 30-second update, and checks that a genuine listing leaves the active view and becomes searchable in Archive. Published data and real source deadlines are not changed.
