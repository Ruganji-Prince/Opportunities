# GitHub and Pages deployment

Create an empty repository named `OpportunityRadar-AI-Research` under your GitHub account. From this project's root:

```sh
git init -b main
git add .
git commit -m "Build OpportunityRadar collection and dashboard"
gh repo create Opportunities --public --source=. --remote=origin --push
```

If the repository already exists, use these instead of the `gh repo create` command:

```sh
git remote add origin https://github.com/Ruganji-Prince/Opportunities.git
git push -u origin main
```

Use a private repository if preferred; GitHub Pages availability for private repositories depends on your plan. This project contains a sanitized profile and public listing records, never your CV or personal tracker.

In repository **Settings → Pages → Build and deployment**, select **GitHub Actions**. Enable Actions, allow workflow write permissions for collection, and run **Deploy dashboard to GitHub Pages**. The workflow builds, tests and uploads `frontend/dist`, then deploys the artifact. The default expected path is `https://Ruganji-Prince.github.io/Opportunities/`; that path is not proof of deployment. Verify it only after the deploy job reports success and the URL loads.

Run **Collect opportunities** manually to check production network access. View source-health results in the job summary and website Sources tab. The scheduled refresh and repository variable/Secrets are described in AUTOMATION.md. No continuously running backend or paid API is required.

If local Git/gh authentication is unavailable, the connected GitHub integration can populate an existing repository, but this environment's available connector cannot create repositories or configure Pages settings. Creating the empty repository and selecting the Pages source are then the only account setup steps. Never paste tokens into chat or commit them.
