# CI/CD Setup Guide

This repository now includes a starter workflow at:

- `.github/workflows/ci-cd.yml`

## What it does

- Runs CI on pull requests to `main`
- Runs CI on pushes to `main`
- Runs Deploy job only for pushes to `main` after CI passes

## CI behavior

- If a `package.json` exists, it runs:
  - `npm ci` (or `npm install` fallback)
  - `npm run lint --if-present`
  - `npm test --if-present`
  - `npm run build --if-present`
- If `requirements.txt` or `pyproject.toml` exists, it runs:
  - dependency install
  - `pytest -q`

## Deploy setup required

1. Go to GitHub repository settings.
2. Add secrets:
   - `DEPLOY_API_TOKEN`
   - `DEPLOY_WEBHOOK_URL`
3. Deployment is executed by `scripts/deploy.sh` and sends a `POST` request to `DEPLOY_WEBHOOK_URL` with bearer auth.

Example:

```sh
curl -X POST -H "Authorization: Bearer <token>" https://your-deploy-endpoint
```

## Optional hardening

- Protect `main` branch and require CI checks before merge.
- Use GitHub Environments with required reviewers for `production`.
