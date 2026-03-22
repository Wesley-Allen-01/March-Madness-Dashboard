"""Presentation helpers shared by Flask views and Jinja templates."""

from config import ADVANCED_STAT_DEFINITIONS, BASIC_STAT_DEFINITIONS, SOS_DEFINITIONS

PERCENT_FROM_RATIO_KEYS = {
    "fg_pct",
    "three_pt_pct",
    "ft_pct",
    "efg_pct",
    "ts_pct",
    "ft_rate",
    "three_pt_rate",
}
PERCENT_FROM_WHOLE_KEYS = {"tov_pct", "orb_pct", "drb_pct"}
SIGNED_TWO_DECIMAL_KEYS = {"srs", "sos"}


def build_stat_definitions():
    """Return stat metadata in display order for comparison views."""
    definitions = {}
    definitions.update(BASIC_STAT_DEFINITIONS)
    definitions.update(ADVANCED_STAT_DEFINITIONS)
    definitions.update(SOS_DEFINITIONS)
    return definitions


def row_to_dict(row):
    """Convert sqlite rows to plain dicts while preserving None inputs."""
    if row is None:
        return None
    return dict(row)


def sign_class(value):
    """Return a CSS class for signed numbers."""
    if value is None:
        return ""
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return ""


def format_stat_value(value, key):
    """Format a stat value using the conventions already present in the UI."""
    if value is None:
        return "\u2014"

    if key in PERCENT_FROM_RATIO_KEYS:
        display_value = value * 100 if value < 1 else value
        return f"{display_value:.1f}%"

    if key in PERCENT_FROM_WHOLE_KEYS:
        return f"{value:.1f}%"

    if key in SIGNED_TWO_DECIMAL_KEYS:
        return f"{value:+.2f}"

    if isinstance(value, float) and not value.is_integer():
        return f"{value:.1f}"

    return str(value)
