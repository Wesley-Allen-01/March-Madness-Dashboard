import db


def test_upsert_team_and_queries_return_expected_rows(isolated_db):
    with db.db_session() as conn:
        db.upsert_team(
            conn,
            {
                "slug": "gamma",
                "name": "Gamma Tech",
                "conference": "Future",
                "wins": 20,
                "losses": 10,
            },
        )
        conn.commit()

        team = db.get_team(conn, "gamma")
        all_teams = db.get_all_teams(conn)
        search_results = db.search_teams(conn, "Gamma")

    assert team["name"] == "Gamma Tech"
    assert [row["slug"] for row in all_teams] == ["gamma"]
    assert [row["slug"] for row in search_results] == ["gamma"]


def test_upsert_players_replaces_existing_team_roster(isolated_db):
    with db.db_session() as conn:
        db.upsert_team(conn, {"slug": "alpha", "name": "Alpha University", "conference": "Big Test"})
        db.upsert_players(
            conn,
            "alpha",
            [
                {"name": "First Player", "ppg": 8.0},
                {"name": "Second Player", "ppg": 12.0},
            ],
        )
        conn.commit()

        assert db.has_players(conn, "alpha") is True
        assert db.get_leading_scorer(conn, "alpha")["name"] == "Second Player"

        db.upsert_players(conn, "alpha", [{"name": "Replacement", "ppg": 15.5, "three_pt_attempts_pg": 2.5, "three_pt_pct": 0.4}])
        conn.commit()

        players = db.get_players(conn, "alpha")

    assert [player["name"] for player in players] == ["Replacement"]


def test_player_queries_return_expected_specialists(seeded_db):
    with db.db_session() as conn:
        scorer = db.get_leading_scorer(conn, "alpha")
        shooter = db.get_best_three_pt_shooter(conn, "alpha")
        prospects = db.get_draft_prospects(conn, "alpha")

    assert scorer["name"] == "Alex Ace"
    assert shooter["name"] == "Blake Bombs"
    assert [player["name"] for player in prospects] == ["Alex Ace"]
