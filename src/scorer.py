"""Outlier scoring for scraped observations.

Account-backed observations are scored against that account's own rolling
median performance (views per hour), so a channel that always gets huge
numbers isn't flagged just for being big. Hashtag observations have no
account context, so they're scored on absolute view count instead.
"""

import statistics
from collections import defaultdict
from datetime import datetime, timezone

from src.youtube_adapter import Observation

MIN_HOURS_SINCE_POSTED = 1.0
ACCOUNT_OUTLIER_THRESHOLD = 3.0
HASHTAG_PROVEN_WINNER_VIEWS = 500_000


def _hours_since_posted(posted_at: str, now: datetime) -> float:
    posted = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    delta_hours = (now - posted).total_seconds() / 3600
    return max(delta_hours, MIN_HOURS_SINCE_POSTED)


def _views_per_hour(observation: Observation, now: datetime) -> float:
    return observation.views / _hours_since_posted(observation.posted_at, now)


def score_observations(
    observations: list[Observation], now: datetime | None = None
) -> list[Observation]:
    now = now or datetime.now(timezone.utc)

    account_obs = [obs for obs in observations if obs.handle]
    hashtag_obs = [obs for obs in observations if not obs.handle]

    views_per_hour_by_id = {
        obs.source_id: _views_per_hour(obs, now) for obs in account_obs
    }

    by_handle = defaultdict(list)
    for obs in account_obs:
        by_handle[obs.handle].append(obs)

    median_by_handle = {
        handle: statistics.median(views_per_hour_by_id[o.source_id] for o in obs_list)
        for handle, obs_list in by_handle.items()
    }

    for obs in account_obs:
        median = median_by_handle[obs.handle]
        vph = views_per_hour_by_id[obs.source_id]
        obs.outlier_score = vph / median if median > 0 else 0.0
        obs.proven_winner = obs.outlier_score >= ACCOUNT_OUTLIER_THRESHOLD

    for obs in hashtag_obs:
        obs.outlier_score = float(obs.views)
        obs.proven_winner = obs.views > HASHTAG_PROVEN_WINNER_VIEWS

    return sorted(observations, key=lambda o: o.outlier_score, reverse=True)
