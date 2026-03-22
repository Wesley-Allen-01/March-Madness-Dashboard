import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import db


TEAM_ALPHA = {
    "slug": "alpha",
    "name": "Alpha University",
    "conference": "Big Test",
    "wins": 28,
    "losses": 5,
    "ppg": 82.1,
    "opp_ppg": 66.2,
    "rpg": 38.4,
    "apg": 17.3,
    "spg": 8.1,
    "bpg": 4.6,
    "topg": 10.2,
    "fg_pct": 0.487,
    "three_pt_pct": 0.392,
    "ft_pct": 0.781,
    "offensive_rating": 118.4,
    "defensive_rating": 95.1,
    "net_rating": 23.3,
    "pace": 69.7,
    "efg_pct": 0.561,
    "ts_pct": 0.604,
    "tov_pct": 14.9,
    "orb_pct": 31.2,
    "drb_pct": 73.4,
    "ft_rate": 0.344,
    "three_pt_rate": 0.418,
    "sos": 6.4,
    "srs": 19.2,
    "opp_efg_pct": 0.452,
    "opp_tov_pct": 15.6,
    "opp_orb_pct": 24.8,
    "opp_ft_rate": 0.271,
}

TEAM_BETA = {
    "slug": "beta",
    "name": "Beta State",
    "conference": "Metro Test",
    "wins": 22,
    "losses": 11,
    "ppg": 75.0,
    "opp_ppg": 69.5,
    "rpg": 34.9,
    "apg": 13.2,
    "spg": 6.5,
    "bpg": 3.1,
    "topg": 12.6,
    "fg_pct": 0.451,
    "three_pt_pct": 0.351,
    "ft_pct": 0.744,
    "offensive_rating": 109.2,
    "defensive_rating": 101.7,
    "net_rating": 7.5,
    "pace": 67.0,
    "efg_pct": 0.524,
    "ts_pct": 0.568,
    "tov_pct": 17.1,
    "orb_pct": 28.0,
    "drb_pct": 69.1,
    "ft_rate": 0.289,
    "three_pt_rate": 0.385,
    "sos": 2.1,
    "srs": 10.0,
    "opp_efg_pct": 0.487,
    "opp_tov_pct": 13.4,
    "opp_orb_pct": 29.7,
    "opp_ft_rate": 0.319,
}

PLAYERS_ALPHA = [
    {
        "name": "Alex Ace",
        "jersey_number": "1",
        "class_year": "FR",
        "position": "G",
        "games_played": 33,
        "minutes_per_game": 32.4,
        "ppg": 18.2,
        "rpg": 5.1,
        "apg": 4.6,
        "spg": 1.9,
        "bpg": 0.3,
        "topg": 2.1,
        "fg_pct": 0.492,
        "three_pt_pct": 0.411,
        "three_pt_made_pg": 2.8,
        "three_pt_attempts_pg": 6.1,
        "ft_pct": 0.824,
        "per": 24.1,
        "ts_pct": 0.622,
        "efg_pct": 0.583,
        "bpm": 9.1,
        "ws": 5.8,
        "usage_rate": 29.5,
        "is_leading_scorer": 1,
        "is_best_three_pt": 0,
        "is_draft_prospect": 1,
        "draft_projection": "Lottery",
    },
    {
        "name": "Blake Bombs",
        "jersey_number": "12",
        "class_year": "JR",
        "position": "G",
        "games_played": 33,
        "minutes_per_game": 28.7,
        "ppg": 12.4,
        "rpg": 3.8,
        "apg": 2.0,
        "spg": 1.0,
        "bpg": 0.1,
        "topg": 1.3,
        "fg_pct": 0.455,
        "three_pt_pct": 0.438,
        "three_pt_made_pg": 3.0,
        "three_pt_attempts_pg": 6.5,
        "ft_pct": 0.771,
        "per": 18.0,
        "ts_pct": 0.601,
        "efg_pct": 0.592,
        "bpm": 4.3,
        "ws": 4.0,
        "usage_rate": 21.0,
        "is_leading_scorer": 0,
        "is_best_three_pt": 1,
        "is_draft_prospect": 0,
        "draft_projection": None,
    },
]

PLAYERS_BETA = [
    {
        "name": "Casey Corner",
        "jersey_number": "4",
        "class_year": "SO",
        "position": "F",
        "games_played": 33,
        "minutes_per_game": 31.2,
        "ppg": 16.0,
        "rpg": 7.2,
        "apg": 2.4,
        "spg": 1.1,
        "bpg": 0.8,
        "topg": 2.6,
        "fg_pct": 0.468,
        "three_pt_pct": 0.366,
        "three_pt_made_pg": 1.8,
        "three_pt_attempts_pg": 4.2,
        "ft_pct": 0.789,
        "per": 21.3,
        "ts_pct": 0.593,
        "efg_pct": 0.552,
        "bpm": 6.0,
        "ws": 4.5,
        "usage_rate": 27.9,
        "is_leading_scorer": 1,
        "is_best_three_pt": 0,
        "is_draft_prospect": 0,
        "draft_projection": None,
    },
    {
        "name": "Drew Deep",
        "jersey_number": "9",
        "class_year": "SR",
        "position": "G",
        "games_played": 33,
        "minutes_per_game": 27.0,
        "ppg": 11.2,
        "rpg": 2.7,
        "apg": 3.3,
        "spg": 0.9,
        "bpg": 0.2,
        "topg": 1.8,
        "fg_pct": 0.431,
        "three_pt_pct": 0.401,
        "three_pt_made_pg": 2.6,
        "three_pt_attempts_pg": 6.2,
        "ft_pct": 0.808,
        "per": 16.7,
        "ts_pct": 0.579,
        "efg_pct": 0.548,
        "bpm": 2.7,
        "ws": 3.2,
        "usage_rate": 20.1,
        "is_leading_scorer": 0,
        "is_best_three_pt": 1,
        "is_draft_prospect": 0,
        "draft_projection": None,
    },
]


def seed_sample_data():
    with db.db_session() as conn:
        db.upsert_team(conn, TEAM_ALPHA)
        db.upsert_team(conn, TEAM_BETA)
        db.upsert_players(conn, TEAM_ALPHA["slug"], [player.copy() for player in PLAYERS_ALPHA])
        db.upsert_players(conn, TEAM_BETA["slug"], [player.copy() for player in PLAYERS_BETA])
        conn.commit()


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "dashboard.db"
    monkeypatch.setattr(db, "DB_PATH", str(test_db_path))
    db.init_db()
    return test_db_path


@pytest.fixture
def seeded_db(isolated_db):
    seed_sample_data()
    return isolated_db


@pytest.fixture
def client(seeded_db):
    import app as app_module

    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


@pytest.fixture
def cli_runner(isolated_db):
    import app as app_module

    app_module.app.config.update(TESTING=True)
    return app_module.app.test_cli_runner()
