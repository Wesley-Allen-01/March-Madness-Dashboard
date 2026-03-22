"""Load and match NBA draft prospect data."""

import json
import os
from config import DRAFT_PROSPECTS_PATH


def load_curated_prospects():
    """Load curated draft prospects from JSON file."""
    if not os.path.exists(DRAFT_PROSPECTS_PATH):
        print("  No draft prospects JSON found, skipping curated list.")
        return []
    with open(DRAFT_PROSPECTS_PATH) as f:
        return json.load(f)


def apply_draft_prospects(conn):
    """Mark players as draft prospects using curated list + stat heuristics."""
    # Reset all draft flags
    conn.execute("UPDATE players SET is_draft_prospect = 0, draft_projection = NULL")

    # Apply curated prospects
    prospects = load_curated_prospects()
    for p in prospects:
        name = p["name"]
        team_slug = p["team"]
        projection = p.get("projection", "Prospect")
        conn.execute(
            """UPDATE players SET is_draft_prospect = 1, draft_projection = ?
               WHERE team_slug = ? AND name LIKE ?""",
            (projection, team_slug, f"%{name}%"),
        )

    # Statistical heuristic: flag players with outstanding stats
    # Freshmen/Sophomores with high PER and scoring
    conn.execute("""
        UPDATE players SET is_draft_prospect = 1,
            draft_projection = COALESCE(draft_projection, 'Statistical Prospect')
        WHERE is_draft_prospect = 0
        AND class_year IN ('FR', 'SO')
        AND per IS NOT NULL AND per >= 20.0
        AND ppg >= 15.0
    """)

    # Any player with elite BPM
    conn.execute("""
        UPDATE players SET is_draft_prospect = 1,
            draft_projection = COALESCE(draft_projection, 'Statistical Prospect')
        WHERE is_draft_prospect = 0
        AND bpm IS NOT NULL AND bpm >= 8.0
    """)

    # High usage + efficiency combo
    conn.execute("""
        UPDATE players SET is_draft_prospect = 1,
            draft_projection = COALESCE(draft_projection, 'Statistical Prospect')
        WHERE is_draft_prospect = 0
        AND usage_rate IS NOT NULL AND usage_rate >= 28.0
        AND ts_pct IS NOT NULL AND ts_pct >= 0.58
        AND ppg >= 16.0
    """)

    conn.commit()
    count = conn.execute("SELECT COUNT(*) as cnt FROM players WHERE is_draft_prospect = 1").fetchone()["cnt"]
    print(f"  Marked {count} players as draft prospects")


def apply_player_flags(conn):
    """Set leading scorer and best 3pt shooter flags per team."""
    # Reset flags
    conn.execute("UPDATE players SET is_leading_scorer = 0, is_best_three_pt = 0")

    # Get all team slugs that have players
    teams = conn.execute("SELECT DISTINCT team_slug FROM players").fetchall()

    for team_row in teams:
        slug = team_row["team_slug"]

        # Leading scorer
        leader = conn.execute(
            "SELECT id FROM players WHERE team_slug = ? ORDER BY ppg DESC LIMIT 1",
            (slug,),
        ).fetchone()
        if leader:
            conn.execute(
                "UPDATE players SET is_leading_scorer = 1 WHERE id = ?", (leader["id"],)
            )

        # Best 3pt shooter (min 2 attempts per game)
        shooter = conn.execute(
            """SELECT id FROM players WHERE team_slug = ?
               AND three_pt_attempts_pg >= 2.0
               ORDER BY three_pt_pct DESC LIMIT 1""",
            (slug,),
        ).fetchone()
        if shooter:
            conn.execute(
                "UPDATE players SET is_best_three_pt = 1 WHERE id = ?", (shooter["id"],)
            )

    conn.commit()
