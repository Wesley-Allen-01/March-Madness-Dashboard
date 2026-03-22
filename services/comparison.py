"""Team comparison logic."""

from config import BASIC_STAT_DEFINITIONS, ADVANCED_STAT_DEFINITIONS, SOS_DEFINITIONS
from db import get_team, get_leading_scorer, get_best_three_pt_shooter, get_draft_prospects


def compare_teams(conn, slug1, slug2):
    """Build comparison data for two teams."""
    team1 = get_team(conn, slug1)
    team2 = get_team(conn, slug2)

    if not team1 or not team2:
        return None

    # Build stat comparisons
    all_stats = {}
    all_stats.update(BASIC_STAT_DEFINITIONS)
    all_stats.update(ADVANCED_STAT_DEFINITIONS)
    all_stats.update(SOS_DEFINITIONS)

    comparisons = []
    for key, (display_name, tooltip, higher_is_better) in all_stats.items():
        v1 = team1[key] if key in team1.keys() else None
        v2 = team2[key] if key in team2.keys() else None

        winner = None
        if v1 is not None and v2 is not None and higher_is_better is not None:
            if higher_is_better:
                winner = 1 if v1 > v2 else (2 if v2 > v1 else 0)
            else:
                winner = 1 if v1 < v2 else (2 if v2 < v1 else 0)

        comparisons.append({
            "key": key,
            "label": display_name,
            "tooltip": tooltip,
            "team1_val": v1,
            "team2_val": v2,
            "winner": winner,
            "higher_is_better": higher_is_better,
        })

    return {
        "team1": dict(team1),
        "team2": dict(team2),
        "comparisons": comparisons,
        "team1_scorer": _player_dict(get_leading_scorer(conn, slug1)),
        "team2_scorer": _player_dict(get_leading_scorer(conn, slug2)),
        "team1_shooter": _player_dict(get_best_three_pt_shooter(conn, slug1)),
        "team2_shooter": _player_dict(get_best_three_pt_shooter(conn, slug2)),
        "team1_prospects": [_player_dict(p) for p in get_draft_prospects(conn, slug1)],
        "team2_prospects": [_player_dict(p) for p in get_draft_prospects(conn, slug2)],
    }


def _player_dict(row):
    if row is None:
        return None
    return dict(row)
