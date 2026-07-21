"""YouTube Data API v3 adapter.

Fetches recent uploads from the watchlist accounts and recent top videos
for each tracked hashtag, normalizing everything into `Observation`
objects ready for scoring and writing to Notion.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from googleapiclient.discovery import build

from src import config

logger = logging.getLogger(__name__)

UPLOADS_PER_ACCOUNT = 20
RESULTS_PER_HASHTAG = 10
HASHTAG_LOOKBACK_DAYS = 7


@dataclass
class Observation:
    source: str
    title: str
    url: str
    handle: Optional[str]
    hook_text: str
    views: int
    likes: int
    comments: int
    posted_at: str
    observed_at: str
    tier: Optional[int]
    source_id: str
    hashtag: Optional[str] = None

    # Populated later by the scorer.
    outlier_score: float = 0.0
    proven_winner: bool = False

    # Populated later by the classifier (for the top 3 only).
    format: Optional[str] = None
    hook_type: Optional[str] = None
    emotional_driver: Optional[str] = None
    segment_target: Optional[str] = None
    funnel_stage: Optional[str] = None
    why_it_worked: Optional[str] = None
    intent_fit_script: Optional[str] = None


def _client():
    return build("youtube", "v3", developerKey=config.YOUTUBE_API_KEY)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _handle_to_channel(youtube, handle: str) -> Optional[dict]:
    """Resolve a @handle to its channel id and uploads playlist id."""
    clean_handle = handle.lstrip("@")
    resp = (
        youtube.channels()
        .list(part="snippet,contentDetails", forHandle=clean_handle)
        .execute()
    )
    items = resp.get("items", [])
    if not items:
        logger.warning("Could not resolve channel for handle %s", handle)
        return None
    channel = items[0]
    uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    return {"channel_id": channel["id"], "uploads_playlist_id": uploads_playlist_id}


def _video_ids_from_playlist(youtube, playlist_id: str, max_results: int) -> list[str]:
    resp = (
        youtube.playlistItems()
        .list(part="contentDetails", playlistId=playlist_id, maxResults=max_results)
        .execute()
    )
    return [item["contentDetails"]["videoId"] for item in resp.get("items", [])]


def _videos_details(youtube, video_ids: list[str]) -> dict[str, dict]:
    """Batch-fetch snippet + statistics for up to 50 video ids at a time."""
    details = {}
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        resp = (
            youtube.videos()
            .list(part="snippet,statistics", id=",".join(batch))
            .execute()
        )
        for item in resp.get("items", []):
            details[item["id"]] = item
    return details


def _to_observation(
    video_id: str,
    video: dict,
    handle: Optional[str],
    tier: Optional[int],
    hashtag: Optional[str],
    observed_at: str,
) -> Observation:
    snippet = video["snippet"]
    stats = video.get("statistics", {})
    return Observation(
        source="youtube",
        title=snippet["title"],
        url=f"https://www.youtube.com/watch?v={video_id}",
        handle=handle,
        hook_text=snippet["title"][:100],
        views=int(stats.get("viewCount", 0)),
        likes=int(stats.get("likeCount", 0)),
        comments=int(stats.get("commentCount", 0)),
        posted_at=snippet["publishedAt"],
        observed_at=observed_at,
        tier=tier,
        source_id=video_id,
        hashtag=hashtag,
    )


def fetch_account_observations(youtube=None) -> list[Observation]:
    """Fetch the last 20 uploads for every account in the watchlist."""
    youtube = youtube or _client()
    observed_at = _now_utc_iso()
    observations = []

    for tier, accounts in config.WATCHLIST_TIERS.items():
        for handle in accounts:
            channel = _handle_to_channel(youtube, handle)
            if not channel:
                continue
            video_ids = _video_ids_from_playlist(
                youtube, channel["uploads_playlist_id"], UPLOADS_PER_ACCOUNT
            )
            details = _videos_details(youtube, video_ids)
            for video_id in video_ids:
                video = details.get(video_id)
                if not video:
                    continue
                observations.append(
                    _to_observation(video_id, video, handle, tier, None, observed_at)
                )

    return observations


def fetch_hashtag_observations(youtube=None) -> list[Observation]:
    """Search the last 7 days per hashtag, sorted by view count, top 10 each."""
    youtube = youtube or _client()
    observed_at = _now_utc_iso()
    published_after = (
        datetime.now(timezone.utc) - timedelta(days=HASHTAG_LOOKBACK_DAYS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    observations = []
    for hashtag in config.HASHTAGS:
        search_resp = (
            youtube.search()
            .list(
                part="snippet",
                q=f"#{hashtag}",
                type="video",
                order="viewCount",
                publishedAfter=published_after,
                maxResults=RESULTS_PER_HASHTAG,
            )
            .execute()
        )
        video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
        details = _videos_details(youtube, video_ids)
        for video_id in video_ids:
            video = details.get(video_id)
            if not video:
                continue
            observations.append(
                _to_observation(video_id, video, None, None, hashtag, observed_at)
            )

    return observations


def deduplicate(observations: list[Observation]) -> list[Observation]:
    """Deduplicate observations by video id, keeping the first occurrence."""
    seen = set()
    deduped = []
    for obs in observations:
        if obs.source_id in seen:
            continue
        seen.add(obs.source_id)
        deduped.append(obs)
    return deduped


def fetch_all_observations() -> list[Observation]:
    youtube = _client()
    account_obs = fetch_account_observations(youtube)
    hashtag_obs = fetch_hashtag_observations(youtube)
    return deduplicate(account_obs + hashtag_obs)
