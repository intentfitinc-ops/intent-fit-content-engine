import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.taxonomy import (
    EmotionalDriver,
    Format,
    display_case,
)


def test_fear_of_regret():
    assert display_case("fear_of_regret") == "Fear of Regret"


def test_b_roll_voiceover():
    assert display_case("b_roll_voiceover") == "B Roll Voiceover"


def test_day_in_the_life():
    assert display_case("day_in_the_life") == "Day in the Life"


def test_ugc_testimonial():
    assert display_case("ugc_testimonial") == "UGC Testimonial"


def test_simple_single_word():
    assert display_case("belonging") == "Belonging"


def test_simple_two_words():
    assert display_case("talking_head") == "Talking Head"


def test_leading_preposition_word_is_still_capitalized():
    # "of" as the first word should still be capitalized (edge case: no
    # taxonomy value starts with a preposition today, but the rule must
    # hold for first/last position regardless of word choice).
    assert display_case("of_control_reclaim") == "Of Control Reclaim"


def test_accepts_enum_member():
    assert display_case(EmotionalDriver.FEAR_OF_REGRET) == "Fear of Regret"
    assert display_case(Format.UGC_TESTIMONIAL) == "UGC Testimonial"


def test_all_emotional_drivers_render():
    expected = {
        "shame_release": "Shame Release",
        "identity_aspiration": "Identity Aspiration",
        "fear_of_regret": "Fear of Regret",
        "proof_of_progress": "Proof of Progress",
        "discipline_pride": "Discipline Pride",
        "control_reclaim": "Control Reclaim",
        "belonging": "Belonging",
        "urgency": "Urgency",
        "permission": "Permission",
        "authority": "Authority",
        "transformation": "Transformation",
    }
    for driver in EmotionalDriver:
        assert display_case(driver.value) == expected[driver.value]


def test_all_formats_render():
    expected = {
        "talking_head": "Talking Head",
        "text_on_screen_only": "Text on Screen Only",
        "b_roll_voiceover": "B Roll Voiceover",
        "split_screen_reaction": "Split Screen Reaction",
        "transformation_reveal": "Transformation Reveal",
        "day_in_the_life": "Day in the Life",
        "tutorial_howto": "Tutorial Howto",
        "ugc_testimonial": "UGC Testimonial",
        "meme_relatable": "Meme Relatable",
        "data_visualization": "Data Visualization",
    }
    for fmt in Format:
        assert display_case(fmt.value) == expected[fmt.value]
