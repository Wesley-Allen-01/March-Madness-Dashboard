import db
from scrapers import draft_prospects


def test_load_curated_prospects_returns_empty_when_file_missing(monkeypatch):
    monkeypatch.setattr(draft_prospects, "DRAFT_PROSPECTS_PATH", "/tmp/does-not-exist.json")

    assert draft_prospects.load_curated_prospects() == []


def test_apply_draft_prospects_marks_curated_and_statistical_players(isolated_db, monkeypatch):
    with db.db_session() as conn:
        db.upsert_team(conn, {"slug": "alpha", "name": "Alpha University", "conference": "Big Test"})
        db.upsert_players(
            conn,
            "alpha",
            [
                {
                    "name": "Curated Star",
                    "class_year": "JR",
                    "ppg": 14.0,
                    "per": 18.0,
                    "bpm": 3.1,
                    "usage_rate": 24.0,
                    "ts_pct": 0.57,
                },
                {
                    "name": "Freshman Breakout",
                    "class_year": "FR",
                    "ppg": 18.0,
                    "per": 22.5,
                    "bpm": 5.2,
                    "usage_rate": 30.0,
                    "ts_pct": 0.61,
                },
                {
                    "name": "Impact Veteran",
                    "class_year": "SR",
                    "ppg": 12.5,
                    "per": 19.0,
                    "bpm": 8.4,
                    "usage_rate": 22.0,
                    "ts_pct": 0.56,
                },
            ],
        )
        conn.commit()

        monkeypatch.setattr(
            draft_prospects,
            "load_curated_prospects",
            lambda: [{"name": "Curated Star", "team": "alpha", "projection": "1st Round"}],
        )

        draft_prospects.apply_draft_prospects(conn)

        prospects = conn.execute(
            "SELECT name, draft_projection FROM players WHERE is_draft_prospect = 1 ORDER BY name"
        ).fetchall()

    assert [(row["name"], row["draft_projection"]) for row in prospects] == [
        ("Curated Star", "1st Round"),
        ("Freshman Breakout", draft_prospects.STATISTICAL_PROSPECT_LABEL),
        ("Impact Veteran", draft_prospects.STATISTICAL_PROSPECT_LABEL),
    ]


def test_apply_player_flags_marks_leader_and_shooter(seeded_db):
    with db.db_session() as conn:
        conn.execute("UPDATE players SET is_leading_scorer = 0, is_best_three_pt = 0")
        conn.commit()

        draft_prospects.apply_player_flags(conn)

        flagged = conn.execute(
            """
            SELECT name, is_leading_scorer, is_best_three_pt
            FROM players
            WHERE team_slug = 'alpha'
            ORDER BY name
            """
        ).fetchall()

    assert [(row["name"], row["is_leading_scorer"], row["is_best_three_pt"]) for row in flagged] == [
        ("Alex Ace", 1, 0),
        ("Blake Bombs", 0, 1),
    ]
