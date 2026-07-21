"""Writes scraped and classified content to the three Notion databases.

The Notion architecture (databases, data sources, properties) already
exists and is not modified here — this module only reads (for idempotency
checks) and creates pages.
"""

import logging
from datetime import date, timedelta

from notion_client import Client

from src import config
from src.taxonomy import display_case
from src.youtube_adapter import Observation

logger = logging.getLogger(__name__)

BLUE_BACKGROUND = "blue_background"


def get_client() -> Client:
    return Client(auth=config.NOTION_TOKEN)


def _rich_text(text: str) -> list[dict]:
    return [{"type": "text", "text": {"content": text}}]


def _paragraph_block(text: str, color: str = "default") -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": _rich_text(text),
            "color": color,
        },
    }


def _heading_1_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": text},
                    "annotations": {"bold": True},
                }
            ]
        },
    }


def _table_row(cells: list[str]) -> dict:
    return {
        "object": "block",
        "type": "table_row",
        "table_row": {"cells": [_rich_text(cell) for cell in cells]},
    }


def _table_block(headers: list[str], rows: list[list[str]]) -> dict:
    return {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": len(headers),
            "has_column_header": True,
            "has_row_header": False,
            "children": [_table_row(headers)] + [_table_row(row) for row in rows],
        },
    }


def _fmt_number(value: int | None) -> str:
    if value is None:
        return "—"
    return f"{value:,}"


def get_current_monday(today: date | None = None) -> date:
    """Compute the Monday of the current run week.

    If today is Sunday, use tomorrow's date (the upcoming Monday). For any
    other day, use this week's Monday.
    """
    today = today or date.today()
    if today.weekday() == 6:  # Sunday
        return today + timedelta(days=1)
    return today - timedelta(days=today.weekday())


# --- 1. Observations DB ------------------------------------------------------


def _observation_exists(client: Client, source_id: str) -> bool:
    resp = client.data_sources.query(
        data_source_id=config.NOTION_OBSERVATIONS_DATASOURCE_ID,
        filter={"property": "Source ID", "rich_text": {"equals": source_id}},
        page_size=1,
    )
    return len(resp.get("results", [])) > 0


def _observation_properties(obs: Observation) -> dict:
    properties = {
        "Source": {"select": {"name": obs.source}},
        "Title": {"title": _rich_text(obs.title)},
        "URL": {"url": obs.url},
        "Handle": {"rich_text": _rich_text(obs.handle or "")},
        "Hook Text": {"rich_text": _rich_text(obs.hook_text)},
        "Views": {"number": obs.views},
        "Posted At": {"date": {"start": obs.posted_at}},
        "Observed At": {"date": {"start": obs.observed_at}},
        "Outlier Score": {"number": round(obs.outlier_score, 4)},
        "Proven Winner": {"checkbox": obs.proven_winner},
        "Source ID": {"rich_text": _rich_text(obs.source_id)},
    }
    if obs.tier is not None:
        properties["Tier"] = {"number": obs.tier}
    if obs.format:
        properties["Format"] = {"select": {"name": display_case(obs.format)}}
    if obs.hook_type:
        properties["Hook Type"] = {"select": {"name": display_case(obs.hook_type)}}
    if obs.emotional_driver:
        properties["Emotional Driver"] = {
            "select": {"name": display_case(obs.emotional_driver)}
        }
    if obs.segment_target:
        properties["Segment Target"] = {
            "select": {"name": display_case(obs.segment_target)}
        }
    if obs.funnel_stage:
        properties["Funnel Stage"] = {
            "select": {"name": display_case(obs.funnel_stage)}
        }
    return properties


def write_observations(client: Client, observations: list[Observation]) -> int:
    """Bulk create observation pages, skipping any that already exist."""
    written = 0
    for obs in observations:
        if _observation_exists(client, obs.source_id):
            logger.info("Observation %s already exists — skipping", obs.source_id)
            continue
        client.pages.create(
            parent={
                "type": "data_source_id",
                "data_source_id": config.NOTION_OBSERVATIONS_DATASOURCE_ID,
            },
            properties=_observation_properties(obs),
        )
        written += 1
    return written


# --- 2. Breakdowns DB ---------------------------------------------------------


def _breakdowns_exist_for_week(client: Client, week_of: str) -> bool:
    resp = client.data_sources.query(
        data_source_id=config.NOTION_BREAKDOWNS_DATASOURCE_ID,
        filter={"property": "Week Of", "date": {"equals": week_of}},
        page_size=3,
    )
    return len(resp.get("results", [])) >= 3


def _breakdown_children(obs: Observation) -> list[dict]:
    metrics_table = _table_block(
        ["Metric", "Value"],
        [
            ["Views", _fmt_number(obs.views)],
            ["Likes", _fmt_number(obs.likes)],
            ["Shares", "—"],
        ],
    )

    breakdown_table = _table_block(
        ["Format", "Hook Type", "Emotional Driver"],
        [
            [
                display_case(obs.format),
                display_case(obs.hook_type),
                display_case(obs.emotional_driver),
            ]
        ],
    )

    script_paragraphs = [
        _paragraph_block(section.strip(), color=BLUE_BACKGROUND)
        for section in obs.intent_fit_script.strip().split("\n\n")
        if section.strip()
    ]

    return [
        _paragraph_block(obs.url),
        metrics_table,
        _heading_1_block("Video Break Down"),
        breakdown_table,
        _heading_1_block("Why it Worked"),
        _paragraph_block(obs.why_it_worked, color=BLUE_BACKGROUND),
        _heading_1_block("Intent Fit Script"),
        *script_paragraphs,
    ]


def write_breakdowns(
    client: Client, top_observations: list[Observation], week_of: str
) -> int:
    if _breakdowns_exist_for_week(client, week_of):
        logger.info("Breakdowns already exist for this week — skipping.")
        return 0

    written = 0
    for obs in top_observations:
        title = f"@{obs.handle or 'unknown'} — {obs.hook_text[:60]}"
        client.pages.create(
            parent={
                "type": "data_source_id",
                "data_source_id": config.NOTION_BREAKDOWNS_DATASOURCE_ID,
            },
            properties={
                "Title": {"title": _rich_text(title)},
                "Video URL": {"url": obs.url},
                "Status": {"status": {"name": "Not started"}},
                "Week Of": {"date": {"start": week_of}},
            },
            children=_breakdown_children(obs),
        )
        written += 1
    return written


# --- 3. Weekly Content Hub -----------------------------------------------------


def _weekly_hub_page_name(week_of: date) -> str:
    return f"Week of {week_of.strftime('%B')} {week_of.day}, {week_of.year}"


def _weekly_hub_exists(client: Client, name: str) -> bool:
    resp = client.data_sources.query(
        data_source_id=config.NOTION_WEEKLY_HUB_DATASOURCE_ID,
        filter={"property": "Name", "title": {"equals": name}},
        page_size=1,
    )
    return len(resp.get("results", [])) > 0


def write_weekly_hub(client: Client, week_of: date) -> bool:
    name = _weekly_hub_page_name(week_of)
    if _weekly_hub_exists(client, name):
        logger.info("Weekly Hub page '%s' already exists — skipping.", name)
        return False

    week_of_str = week_of.isoformat()
    body = (
        "This week's approved content. Once cards are approved in the review "
        "database, they will appear here as gallery tiles.\n"
        "Manual step: turn the link below into a linked database view, filter "
        f"Status = Accept AND Week Of = {week_of_str}, gallery layout, show "
        "Title + Video URL.\n"
        "Link to Breakdowns database: "
        "https://www.notion.so/58d5f10b7ad340a4a073678a6215cfb0"
    )

    client.pages.create(
        parent={
            "type": "data_source_id",
            "data_source_id": config.NOTION_WEEKLY_HUB_DATASOURCE_ID,
        },
        properties={"Name": {"title": _rich_text(name)}},
        children=[_paragraph_block(body)],
    )
    return True
