# intent-fit-content-engine
Scrap existing content to provide winning scrips for affiliates

## What this repo does

Runs the Intent Fit Content Engine every Monday at 2am MST. Scrapes YouTube
for viral content, classifies with AI, writes 3 breakdown cards to Notion
for weekly review.

## Setup

### 1. GitHub Secrets

Settings → Secrets and variables → Actions → New repository secret.

Add these 6 secrets:

| Secret Name | Where to find |
|---|---|
| `YOUTUBE_API_KEY` | Google Cloud Console → APIs & Services → Credentials → "My First Project" API key |
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |
| `NOTION_TOKEN` | notion.so/profile/integrations → "Intent Fit Intel Pipeline" → Internal Integration Token |
| `NOTION_OBSERVATIONS_DB_ID` | `74a13c9d-63bd-4d03-b66e-d486e0c8ac81` |
| `NOTION_BREAKDOWNS_DB_ID` | `58d5f10b-7ad3-40a4-a073-678a6215cfb0` |
| `NOTION_WEEKLY_HUB_DB_ID` | `3a38b5a3-5aa4-8000-8fa8-c02353ffad18` |

### 2. Manual test run

After secrets are added, go to the Actions tab → "Weekly Pipeline" workflow
→ "Run workflow" button. Watch the logs.

## Weekly workflow

- Every Monday 2am MST: pipeline runs automatically.
- Quinten reviews the 3 new cards in Notion during the day.
- Sunday night: Quinten opens the Claude Project chat, says "Run this
  week" — Claude finalizes the Weekly Hub filter for the affiliate view.
- Approved cards appear in the affiliate Fresh Content gallery.

## Repo layout

```
intent-fit-content-engine/
├── .github/
│   └── workflows/
│       └── weekly-pipeline.yml
├── scripts/
│   └── run_weekly.py
├── src/
│   ├── __init__.py
│   ├── config.py           # loads env vars from secrets
│   ├── youtube_adapter.py  # scrapes YouTube API
│   ├── scorer.py           # outlier scoring
│   ├── classifier.py       # AI classification via Claude API
│   ├── notion_writer.py    # writes to all 3 Notion DBs
│   └── taxonomy.py         # hook types, drivers, formats, segments
├── tests/
│   └── test_taxonomy.py    # unit tests for display case conversion
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Local dev

```bash
cp .env.example .env  # fill in real values
pip install -r requirements.txt
python scripts/run_weekly.py
```
