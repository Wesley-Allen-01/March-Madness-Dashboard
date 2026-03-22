"""March Madness Dashboard — Flask application."""

import json
import os
import time

import click
from flask import Flask, jsonify, render_template, request

from config import (
    ADVANCED_STAT_DEFINITIONS,
    BASIC_STAT_DEFINITIONS,
    REQUEST_DELAY,
    SOS_DEFINITIONS,
    TOURNAMENT_TEAMS_PATH,
)
from db import (
    db_session,
    get_all_teams,
    get_best_three_pt_shooter,
    get_draft_prospects,
    get_leading_scorer,
    get_players,
    get_team,
    has_players,
    init_db,
    search_teams,
    upsert_players,
    upsert_team,
)
from scrapers.sportsref import (
    merge_team_data,
    scrape_advanced_team_stats,
    scrape_basic_team_stats,
    scrape_team_players,
)
from scrapers.draft_prospects import apply_draft_prospects, apply_player_flags
from services.comparison import compare_teams
from services.presentation import build_stat_definitions, format_stat_value, sign_class

app = Flask(__name__)
app.add_template_filter(format_stat_value, "stat_value")
app.add_template_filter(sign_class, "sign_class")


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@app.cli.command("fetch-data")
@click.option("--players", is_flag=True, help="Also fetch player stats for all teams (slow)")
def fetch_data(players):
    """Scrape team data from sports-reference and populate the database."""
    init_db()
    with db_session() as conn:
        # Step 1: Basic team stats (1 HTTP request)
        basic = scrape_basic_team_stats()

        # Step 2: Advanced team stats (1 HTTP request)
        advanced = scrape_advanced_team_stats()

        # Step 3: Merge
        merged = merge_team_data(basic, advanced)

        # Step 4: Save to DB
        print(f"Saving {len(merged)} teams to database...")
        for team in merged:
            upsert_team(conn, team)
        conn.commit()
        print("Team data saved.")

        # Step 5: Optionally fetch all player stats
        if players:
            print("Fetching player stats for all teams (this will take a while)...")
            for i, team in enumerate(merged):
                slug = team["slug"]
                print(f"  [{i+1}/{len(merged)}] {slug}")
                try:
                    player_list = scrape_team_players(slug)
                    if player_list:
                        upsert_players(conn, slug, player_list)
                        conn.commit()
                except Exception as e:
                    print(f"    Error fetching {slug}: {e}")
                time.sleep(REQUEST_DELAY)

            # Apply draft prospect flags
            print("Applying draft prospect flags...")
            apply_draft_prospects(conn)
            apply_player_flags(conn)

    print("Done!")


# ---------------------------------------------------------------------------
# Helper to lazy-load player data for a team
# ---------------------------------------------------------------------------

def ensure_players(conn, slug):
    """Fetch and cache player data for a team if not already in DB."""
    if has_players(conn, slug):
        return
    try:
        player_list = scrape_team_players(slug)
        if player_list:
            upsert_players(conn, slug, player_list)
            conn.commit()
            apply_draft_prospects(conn)
            apply_player_flags(conn)
    except Exception as e:
        print(f"Error fetching players for {slug}: {e}")


def serialize_team_brief(team):
    """Return the small team payload used by the JSON endpoints."""
    return {
        "slug": team["slug"],
        "name": team["name"],
        "conference": team["conference"],
    }


def fetch_team_list():
    """Load the global team list for index and compare views."""
    with db_session() as conn:
        return get_all_teams(conn)


def load_tournament_team_slugs():
    """Load the curated list of tournament teams for the current season."""
    if not os.path.exists(TOURNAMENT_TEAMS_PATH):
        return set()
    with open(TOURNAMENT_TEAMS_PATH) as f:
        return set(json.load(f))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    teams = fetch_team_list()
    return render_template("index.html", teams=teams)


@app.route("/team/<slug>")
def team_detail(slug):
    with db_session() as conn:
        team = get_team(conn, slug)
        if not team:
            return "Team not found", 404

        ensure_players(conn, slug)

        players = get_players(conn, slug)
        scorer = get_leading_scorer(conn, slug)
        shooter = get_best_three_pt_shooter(conn, slug)
        prospects = get_draft_prospects(conn, slug)

    return render_template(
        "team.html",
        team=team,
        players=players,
        scorer=scorer,
        shooter=shooter,
        prospects=prospects,
        basic_stats=BASIC_STAT_DEFINITIONS,
        advanced_stats=ADVANCED_STAT_DEFINITIONS,
        sos_stats=SOS_DEFINITIONS,
    )


@app.route("/compare")
def comparison():
    slug1 = request.args.get("team1", "")
    slug2 = request.args.get("team2", "")
    with db_session() as conn:
        teams = get_all_teams(conn)
        data = None

        if slug1 and slug2:
            ensure_players(conn, slug1)
            ensure_players(conn, slug2)
            data = compare_teams(conn, slug1, slug2)

    return render_template(
        "comparison.html",
        teams=teams,
        data=data,
        team1_slug=slug1,
        team2_slug=slug2,
        basic_stats=BASIC_STAT_DEFINITIONS,
        advanced_stats=ADVANCED_STAT_DEFINITIONS,
        sos_stats=SOS_DEFINITIONS,
    )


@app.route("/data")
def raw_data():
    tournament_team_slugs = load_tournament_team_slugs()
    teams = [
        {
            **dict(team),
            "made_tournament": team["slug"] in tournament_team_slugs,
        }
        for team in fetch_team_list()
    ]
    stat_definitions = build_stat_definitions()
    columns = [
        {"key": "name", "label": "Team", "tooltip": "Team name", "is_numeric": False},
        {"key": "conference", "label": "Conference", "tooltip": "Conference name", "is_numeric": False},
        {"key": "made_tournament", "label": "Tournament", "tooltip": "Made the NCAA tournament field", "is_numeric": False},
    ]
    columns.extend(
        {
            "key": key,
            "label": label,
            "tooltip": tooltip,
            "is_numeric": True,
        }
        for key, (label, tooltip, _) in stat_definitions.items()
    )
    return render_template("data.html", teams=teams, columns=columns)


@app.route("/api/teams")
def api_teams():
    teams = fetch_team_list()
    return jsonify([serialize_team_brief(team) for team in teams])


@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])
    with db_session() as conn:
        results = search_teams(conn, query)
    return jsonify([serialize_team_brief(team) for team in results])


if __name__ == "__main__":
    app.run(debug=True)
