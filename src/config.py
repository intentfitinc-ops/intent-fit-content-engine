"""Configuration for the Intent Fit Content Engine.

Loads secrets from environment variables (populated from GitHub Actions
secrets in CI, or a local .env file in development) and hardcodes the
YouTube watchlist and hashtag scan list.
"""

import os

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def _require(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


# --- Secrets / required env vars -------------------------------------------------

YOUTUBE_API_KEY = _require("YOUTUBE_API_KEY")
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
NOTION_TOKEN = _require("NOTION_TOKEN")

NOTION_OBSERVATIONS_DB_ID = _require(
    "NOTION_OBSERVATIONS_DB_ID", "74a13c9d-63bd-4d03-b66e-d486e0c8ac81"
)
NOTION_BREAKDOWNS_DB_ID = _require(
    "NOTION_BREAKDOWNS_DB_ID", "58d5f10b-7ad3-40a4-a073-678a6215cfb0"
)
NOTION_WEEKLY_HUB_DB_ID = _require(
    "NOTION_WEEKLY_HUB_DB_ID", "3a38b5a3-5aa4-8000-8fa8-c02353ffad18"
)

# Data source IDs (not overridable via env — internal to the Notion API layer).
NOTION_OBSERVATIONS_DATASOURCE_ID = "c176d372-fc1d-4de1-ae2b-2044e435b9ca"
NOTION_BREAKDOWNS_DATASOURCE_ID = "303cc540-ee6a-49e5-9b9c-59b9a8ec1f07"
NOTION_WEEKLY_HUB_DATASOURCE_ID = "3a38b5a3-5aa4-8079-81c0-000b3b5f7c9a"

# claude-opus-4-6 does not exist as a released model id; claude-opus-4-8 is
# the latest available Opus model at build time, per the "or latest
# available" instruction.
CLAUDE_MODEL = "claude-opus-4-8"

# --- Watchlist --------------------------------------------------------------

# Tier 1: direct competitors (journal/planner brands).
TIER_1_ACCOUNTS = [
    "@thesuccessfulman._",
    "@officialkaizenchallenge",
    "@intelligentchange",
]

# Tier 2: fitness apps/wearables (future product overlap).
TIER_2_ACCOUNTS = [
    "@strava",
    "@whoop",
    "@hevyapp",
    "@asrv",
]

WATCHLIST_TIERS = {
    1: TIER_1_ACCOUNTS,
    2: TIER_2_ACCOUNTS,
}

HASHTAGS = [
    "Fitness",
    "Motivation",
    "Health",
    "Wellness",
    "Athletics",
    "Sports",
    "Training",
    "Habit",
    "HabitTracker",
    "HybridAthlete",
]
