from services.comparison import compare_teams, pick_stat_winner


def test_pick_stat_winner_handles_edge_cases():
    assert pick_stat_winner(None, 5, True) is None
    assert pick_stat_winner(5, None, True) is None
    assert pick_stat_winner(5, 5, True) == 0
    assert pick_stat_winner(6, 5, True) == 1
    assert pick_stat_winner(4, 5, True) == 2
    assert pick_stat_winner(4, 5, False) == 1
    assert pick_stat_winner(6, 5, False) == 2


def test_compare_teams_returns_full_comparison_payload(seeded_db):
    import db

    with db.db_session() as conn:
        data = compare_teams(conn, "alpha", "beta")

    assert data["team1"]["name"] == "Alpha University"
    assert data["team2"]["name"] == "Beta State"
    assert data["team1_scorer"]["name"] == "Alex Ace"
    assert data["team2_shooter"]["name"] == "Drew Deep"
    assert data["team1_prospects"][0]["name"] == "Alex Ace"

    wins_row = next(row for row in data["comparisons"] if row["key"] == "wins")
    defensive_row = next(row for row in data["comparisons"] if row["key"] == "defensive_rating")
    pace_row = next(row for row in data["comparisons"] if row["key"] == "pace")

    assert wins_row["winner"] == 1
    assert defensive_row["winner"] == 1
    assert pace_row["winner"] is None


def test_compare_teams_returns_none_for_missing_team(seeded_db):
    import db

    with db.db_session() as conn:
        result = compare_teams(conn, "alpha", "missing")

    assert result is None
