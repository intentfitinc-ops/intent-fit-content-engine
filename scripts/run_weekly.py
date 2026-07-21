#!/usr/bin/env python3
"""Entry point for the weekly Intent Fit content pipeline.

Scrapes YouTube, scores observations for outlier performance, classifies
the top 3 via Claude, and writes everything to Notion.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import config  # noqa: E402  (validates env vars on import)
from src.classifier import classify_top_observations  # noqa: E402
from src.notion_writer import (  # noqa: E402
    get_client,
    get_current_monday,
    write_breakdowns,
    write_observations,
    write_weekly_hub,
)
from src.scorer import score_observations  # noqa: E402
from src.youtube_adapter import (  # noqa: E402
    deduplicate,
    fetch_account_observations,
    fetch_hashtag_observations,
)

TOP_N = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("run.log"),
    ],
)
logger = logging.getLogger("run_weekly")


def main() -> int:
    week_of = get_current_monday()
    logger.info("Running weekly pipeline for Week Of %s", week_of.isoformat())

    logger.info("Fetching watchlist account observations from YouTube...")
    account_obs = fetch_account_observations()
    logger.info("Fetched %d account observations", len(account_obs))

    logger.info("Fetching hashtag observations from YouTube...")
    hashtag_obs = fetch_hashtag_observations()
    logger.info("Fetched %d hashtag observations", len(hashtag_obs))

    observations = deduplicate(account_obs + hashtag_obs)
    logger.info("%d observations after deduplication", len(observations))

    scored = score_observations(observations)

    notion = get_client()

    written = write_observations(notion, scored)
    logger.info("Wrote %d new observations to the Observations DB", written)

    top_n = scored[:TOP_N]
    logger.info("Classifying top %d observations via Claude...", len(top_n))
    classify_top_observations(top_n)

    breakdowns_written = write_breakdowns(notion, top_n, week_of.isoformat())
    logger.info("Wrote %d new breakdown pages", breakdowns_written)

    try:
        hub_created = write_weekly_hub(notion, week_of)
    except Exception:
        logger.exception(
            "Weekly Hub page creation failed for Week Of %s (Weekly Hub DB %s)",
            week_of.isoformat(),
            config.NOTION_WEEKLY_HUB_DB_ID,
        )
        raise
    logger.info(
        "Weekly Hub page %s", "created" if hub_created else "already existed — skipped"
    )

    logger.info(
        "Summary: %d observations written, %d breakdowns for Week Of %s, "
        "Weekly Hub page %s",
        written,
        breakdowns_written,
        week_of.isoformat(),
        "created" if hub_created else "skipped",
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
