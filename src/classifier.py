"""AI classification of top-scoring observations via the Claude API.

Classifies each observation against the Intent Fit taxonomy and generates
brand-voice analysis and a ready-to-shoot script.
"""

import json
import logging

import anthropic

from src import config
from src.taxonomy import EmotionalDriver, Format, FunnelStage, HookType, Segment
from src.youtube_adapter import Observation

logger = logging.getLogger(__name__)

BRAND_VOICE = """\
Intent Fit brand voice:
- Discipline over motivation.
- Systems over hype.
- Proof in writing — the physical Intent Fit Journal is what makes progress undeniable.
- Anti-app, anti-notification, anti-hustle-influencer.
- Speaks to men 25-40 who are exhausted by fitness content and want the truth.
- Never uses phrases like "level up," "grind," "beast mode," "crush it," "unleash," \
or "transform your life."
- Always references the physical journal as the artifact of discipline.
"""

SCRIPT_TEMPLATE = """\
[HOOK — 0-3s]
(Visual direction)
"Spoken line."

[PAIN — 3-10s]
(Visual direction)
[Text overlay: "..."]
"Spoken line."

[SOLUTION — 10-20s]
(Visual direction)
[Text overlay: "..."]
"Spoken line."

[CTA — 20s+]
(Visual direction)
"Spoken line."
"""

CLASSIFY_TOOL = {
    "name": "classify_video",
    "description": (
        "Classify a scraped video against the Intent Fit content taxonomy "
        "and produce brand-voice analysis and a ready-to-shoot script."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": [f.value for f in Format],
            },
            "hook_type": {
                "type": "string",
                "enum": [h.value for h in HookType],
            },
            "emotional_driver": {
                "type": "string",
                "enum": [d.value for d in EmotionalDriver],
            },
            "segment_target": {
                "type": "string",
                "enum": [s.value for s in Segment],
            },
            "funnel_stage": {
                "type": "string",
                "enum": [f.value for f in FunnelStage],
            },
            "why_it_worked": {
                "type": "string",
                "description": (
                    "2-4 sentences, analytical not fluffy, explaining the "
                    "psychological mechanism behind why this video performed."
                ),
            },
            "intent_fit_script": {
                "type": "string",
                "description": (
                    "Full ready-to-shoot script in the Intent Fit voice, "
                    "following the required [HOOK]/[PAIN]/[SOLUTION]/[CTA] "
                    "structure with visual directions and spoken lines."
                ),
            },
        },
        "required": [
            "format",
            "hook_type",
            "emotional_driver",
            "segment_target",
            "funnel_stage",
            "why_it_worked",
            "intent_fit_script",
        ],
    },
}


def _build_prompt(observation: Observation) -> str:
    return f"""\
You are the content strategist for Intent Fit, a DTC brand that sells the \
Intent Fit Journal (a 90-day habit-tracking journal).

{BRAND_VOICE}

Analyze this video and classify it, then write a competing script in the \
Intent Fit voice that could beat it.

Video title: {observation.title}
Channel handle: {observation.handle or "(hashtag discovery, no channel)"}
Views: {observation.views}
Likes: {observation.likes}
Comments: {observation.comments}
Posted at: {observation.posted_at}
Outlier score: {observation.outlier_score:.2f}

Required script structure (follow exactly, one bracketed section per line, \
include the visual direction line, any text overlay line, and the spoken \
line as shown):

{SCRIPT_TEMPLATE}

Call the classify_video tool with your analysis."""


def classify_observation(observation: Observation, client: anthropic.Anthropic) -> Observation:
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2048,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_video"},
        messages=[{"role": "user", "content": _build_prompt(observation)}],
    )

    tool_use = next(
        block for block in response.content if block.type == "tool_use"
    )
    result = tool_use.input

    observation.format = result["format"]
    observation.hook_type = result["hook_type"]
    observation.emotional_driver = result["emotional_driver"]
    observation.segment_target = result["segment_target"]
    observation.funnel_stage = result["funnel_stage"]
    observation.why_it_worked = result["why_it_worked"]
    observation.intent_fit_script = result["intent_fit_script"]

    return observation


def classify_top_observations(
    observations: list[Observation], client: anthropic.Anthropic | None = None
) -> list[Observation]:
    client = client or anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    for obs in observations:
        logger.info("Classifying %s (%s)", obs.title, obs.source_id)
        classify_observation(obs, client)
    return observations
