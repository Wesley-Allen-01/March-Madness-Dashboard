"""SQLite access helpers for the dashboard."""

import os
import sqlite3
from contextlib import contextmanager

from config import DB_PATH

SCHEMA_SQL = """
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        conference TEXT,
        wins INTEGER,
        losses INTEGER,
        -- Basic per-game stats
        ppg REAL,
        opp_ppg REAL,
        rpg REAL,
        apg REAL,
        spg REAL,
        bpg REAL,
        topg REAL,
        fg_pct REAL,
        three_pt_pct REAL,
        ft_pct REAL,
        -- Advanced stats
        offensive_rating REAL,
        defensive_rating REAL,
        net_rating REAL,
        pace REAL,
        efg_pct REAL,
        ts_pct REAL,
        tov_pct REAL,
        orb_pct REAL,
        drb_pct REAL,
        ft_rate REAL,
        three_pt_rate REAL,
        -- Strength of schedule
        sos REAL,
        srs REAL,
        -- Opponent advanced stats
        opp_efg_pct REAL,
        opp_tov_pct REAL,
        opp_orb_pct REAL,
        opp_ft_rate REAL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        team_slug TEXT NOT NULL,
        jersey_number TEXT,
        class_year TEXT,
        position TEXT,
        games_played INTEGER,
        minutes_per_game REAL,
        ppg REAL,
        rpg REAL,
        apg REAL,
        spg REAL,
        bpg REAL,
        topg REAL,
        fg_pct REAL,
        three_pt_pct REAL,
        three_pt_made_pg REAL,
        three_pt_attempts_pg REAL,
        ft_pct REAL,
        -- Advanced
        per REAL,
        ts_pct REAL,
        efg_pct REAL,
        bpm REAL,
        ws REAL,
        usage_rate REAL,
        -- Flags
        is_leading_scorer INTEGER DEFAULT 0,
        is_best_three_pt INTEGER DEFAULT 0,
        is_draft_prospect INTEGER DEFAULT 0,
        draft_projection TEXT,
        FOREIGN KEY (team_slug) REFERENCES teams(slug)
    );

    CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_slug);
"""


def get_connection():
    """Open a sqlite connection with the settings used throughout the app."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def db_session():
    """Yield a connection and always close it when the caller is done."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create tables and indexes if they do not already exist."""
    with db_session() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def upsert_team(conn, team_data):
    """Insert or update a team record."""
    cols = [k for k in team_data.keys()]
    placeholders = ", ".join(f":{c}" for c in cols)
    updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c != "slug")
    sql = f"""
        INSERT INTO teams ({', '.join(cols)})
        VALUES ({placeholders})
        ON CONFLICT(slug) DO UPDATE SET {updates}, last_updated = CURRENT_TIMESTAMP
    """
    conn.execute(sql, team_data)


def upsert_players(conn, team_slug, players):
    """Replace all players for a team."""
    conn.execute("DELETE FROM players WHERE team_slug = ?", (team_slug,))
    for p in players:
        p["team_slug"] = team_slug
        cols = list(p.keys())
        placeholders = ", ".join(f":{c}" for c in cols)
        sql = f"INSERT INTO players ({', '.join(cols)}) VALUES ({placeholders})"
        conn.execute(sql, p)


def get_all_teams(conn):
    return conn.execute("SELECT * FROM teams ORDER BY name").fetchall()


def get_team(conn, slug):
    return conn.execute(
        "SELECT * FROM teams WHERE slug = ?", (slug,)
    ).fetchone()


def get_players(conn, team_slug):
    return conn.execute(
        "SELECT * FROM players WHERE team_slug = ? ORDER BY ppg DESC",
        (team_slug,),
    ).fetchall()


def get_leading_scorer(conn, team_slug):
    return conn.execute(
        "SELECT * FROM players WHERE team_slug = ? ORDER BY ppg DESC LIMIT 1",
        (team_slug,),
    ).fetchone()


def get_best_three_pt_shooter(conn, team_slug):
    return conn.execute(
        """SELECT * FROM players WHERE team_slug = ?
           AND three_pt_attempts_pg >= 2.0
           ORDER BY three_pt_pct DESC LIMIT 1""",
        (team_slug,),
    ).fetchone()


def get_draft_prospects(conn, team_slug):
    return conn.execute(
        "SELECT * FROM players WHERE team_slug = ? AND is_draft_prospect = 1 ORDER BY ppg DESC",
        (team_slug,),
    ).fetchall()


def search_teams(conn, query):
    return conn.execute(
        "SELECT slug, name, conference FROM teams WHERE name LIKE ? ORDER BY name LIMIT 20",
        (f"%{query}%",),
    ).fetchall()


def has_players(conn, team_slug):
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM players WHERE team_slug = ?", (team_slug,)
    ).fetchone()
    return row["cnt"] > 0
