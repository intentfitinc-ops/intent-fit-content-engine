"""Taxonomy constants for classifying scraped content.

Every taxonomy value is a snake_case string. Notion select options and the
classifier prompt both use the human-readable form produced by
`display_case`.
"""

from enum import Enum


class HookType(str, Enum):
    QUESTION = "question"
    STAT_SHOCK = "stat_shock"
    CALLOUT = "callout"
    CONTRARIAN = "contrarian"


class EmotionalDriver(str, Enum):
    SHAME_RELEASE = "shame_release"
    IDENTITY_ASPIRATION = "identity_aspiration"
    FEAR_OF_REGRET = "fear_of_regret"
    PROOF_OF_PROGRESS = "proof_of_progress"
    DISCIPLINE_PRIDE = "discipline_pride"
    CONTROL_RECLAIM = "control_reclaim"
    BELONGING = "belonging"
    URGENCY = "urgency"
    PERMISSION = "permission"
    AUTHORITY = "authority"
    TRANSFORMATION = "transformation"


class Segment(str, Enum):
    CHRONIC_RESTARTER = "chronic_restarter"
    MOTIVATION_CHASER = "motivation_chaser"
    OPTIMIZING_ATHLETE = "optimizing_athlete"
    PARALYZED_BEGINNER = "paralyzed_beginner"


class FunnelStage(str, Enum):
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    CONVERSION = "conversion"
    RETENTION = "retention"


class Format(str, Enum):
    TALKING_HEAD = "talking_head"
    TEXT_ON_SCREEN_ONLY = "text_on_screen_only"
    B_ROLL_VOICEOVER = "b_roll_voiceover"
    SPLIT_SCREEN_REACTION = "split_screen_reaction"
    TRANSFORMATION_REVEAL = "transformation_reveal"
    DAY_IN_THE_LIFE = "day_in_the_life"
    TUTORIAL_HOWTO = "tutorial_howto"
    UGC_TESTIMONIAL = "ugc_testimonial"
    MEME_RELATABLE = "meme_relatable"
    DATA_VISUALIZATION = "data_visualization"


# Small words that stay lowercase in display case, unless they are the
# first or last word of the value.
_LOWERCASE_WORDS = {
    "of", "in", "the", "a", "an", "and", "or", "but",
    "nor", "on", "at", "to", "by", "for",
}

# Words with a fixed uppercase rendering regardless of position.
_UPPERCASE_WORDS = {"ugc"}


def display_case(value: str) -> str:
    """Convert a snake_case taxonomy value into a display-friendly string.

    Title-cases each word except small prepositions/articles that aren't
    the first or last word (e.g. "day_in_the_life" -> "Day in the Life"),
    with special-cased acronyms like "ugc" always rendered upper case.
    """
    if isinstance(value, Enum):
        value = value.value

    words = value.split("_")
    last_index = len(words) - 1

    display_words = []
    for i, word in enumerate(words):
        lower_word = word.lower()
        if lower_word in _UPPERCASE_WORDS:
            display_words.append(word.upper())
        elif 0 < i < last_index and lower_word in _LOWERCASE_WORDS:
            display_words.append(lower_word)
        else:
            display_words.append(word.capitalize())

    return " ".join(display_words)
