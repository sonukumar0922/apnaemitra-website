# Apna eMitra Version 1 (GitHub-only starter)

## What this version does
- Keeps the existing homepage design.
- Loads public jobs from `data/jobs.json`.
- Runs discovery twice daily (06:00 and 18:00 IST) using GitHub Actions.
- Creates a Pull Request containing discovery leads in `data/pending-jobs.json`.
- Publishes only records manually verified, completed, marked `approved`, and merged to `main`.

## Important limitation
The discovery script uses Google News RSS search results as *leads*, not as official job notifications. It does not claim that a vacancy is genuine, open, or accepting applications. An administrator must open the original recruiting body's website, verify the notification, fill the official HTTPS notification/application URL and all required fields, and only then set `status` to `approved`. Do not publish private-sector jobs unless the employer's own careers page confirms them.

This is a GitHub Pull Request review workflow, not a website password-protected admin dashboard. Do not put passwords, personal data, or access tokens in public files. Do not expose a PAT. The workflow uses the repository-provided `GITHUB_TOKEN`.

## Install
1. Back up your repository.
2. Copy these files/folders into the repository root, preserving paths.
3. Replace `index.html` with this updated version.
4. In GitHub: Settings -> Actions -> General -> Workflow permissions, enable **Allow GitHub Actions to create and approve pull requests** (wording may vary). If unavailable, the discovery workflow cannot create PRs.
5. Ensure Actions are enabled for the repository.
6. Commit to `main`.
7. Open Actions and manually run **Apna eMitra Job Discovery** once to test.
8. Review the PR. For every candidate, verify the official notice, fill required fields, set `status` to `approved`, then merge.
9. The publish workflow moves approved jobs into `data/jobs.json`; the website reads only that public file.

## Approving a candidate
In `data/pending-jobs.json`, update a candidate only after official verification:
- `organization`: exact recruiting organisation
- `officialUrl`: direct official HTTPS notification/application page
- `qualification`, `vacancies`, `ageLimit`, `lastDate`, `fee`, `salary`: accurate details from notification
- `source`: official host, e.g. `ssc.gov.in`
- `status`: `approved`

Never infer missing dates or eligibility. If no official notice is found, leave pending or remove the candidate.

## Schedule
Cron `30 0,12 * * *` is 06:00 and 18:00 India Standard Time (UTC+5:30). GitHub may delay scheduled workflows during high load; use workflow_dispatch for a manual run.

## Private jobs
Private job leads require confirmation on the employer's official careers website. This initial version intentionally does not publish private job candidates automatically.

## Current static sections
The existing homepage still contains static admit-card/result/scheme content and assistance form demo behaviour. These are not connected to a backend in this version and should be reviewed/updated separately.
