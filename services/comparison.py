"""Team comparison logic."""

from db import (
    get_best_three_pt_shooter,
    get_draft_prospects,
    get_leading_scorer,
    get_team,
)
from services.presentation import build_stat_definitions, row_to_dict


def compare_teams(conn, slug1, slug2):
    """Build comparison data for two teams."""
    team1 = get_team(conn, slug1)
    team2 = get_team(conn, slug2)

    if not team1 or not team2:
        return None

    comparisons = []
    for key, (display_name, tooltip, higher_is_better) in build_stat_definitions().items():
        team1_value = team1[key] if key in team1.keys() else None
        team2_value = team2[key] if key in team2.keys() else None

        comparisons.append(
            {
                "key": key,
                "label": display_name,
                "tooltip": tooltip,
                "team1_val": team1_value,
                "team2_val": team2_value,
                "winner": pick_stat_winner(team1_value, team2_value, higher_is_better),
                "higher_is_better": higher_is_better,
            }
        )

    return {
        "team1": dict(team1),
        "team2": dict(team2),
        "comparisons": comparisons,
        "team1_scorer": row_to_dict(get_leading_scorer(conn, slug1)),
        "team2_scorer": row_to_dict(get_leading_scorer(conn, slug2)),
        "team1_shooter": row_to_dict(get_best_three_pt_shooter(conn, slug1)),
        "team2_shooter": row_to_dict(get_best_three_pt_shooter(conn, slug2)),
        "team1_prospects": [row_to_dict(player) for player in get_draft_prospects(conn, slug1)],
        "team2_prospects": [row_to_dict(player) for player in get_draft_prospects(conn, slug2)],
    }


def pick_stat_winner(team1_value, team2_value, higher_is_better):
    """Return 1, 2, 0, or None based on which team wins a stat."""
    if team1_value is None or team2_value is None or higher_is_better is None:
        return None

    if team1_value == team2_value:
        return 0

    if higher_is_better:
        return 1 if team1_value > team2_value else 2

    return 1 if team1_value < team2_value else 2
