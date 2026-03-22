"""March Madness Dashboard — Flask application."""

import time
import click
from flask import Flask, render_template, request, jsonify

from config import BASIC_STAT_DEFINITIONS, ADVANCED_STAT_DEFINITIONS, SOS_DEFINITIONS
from db import (
    init_db, get_connection, get_all_teams, get_team, get_players,
    get_leading_scorer, get_best_three_pt_shooter, get_draft_prospects,
    upsert_team, upsert_players, has_players, search_teams,
)
from scrapers.sportsref import (
    scrape_basic_team_stats, scrape_advanced_team_stats,
    merge_team_data, scrape_team_players,
)
from scrapers.draft_prospects import apply_draft_prospects, apply_player_flags
from services.comparison import compare_teams

app = Flask(__name__)


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@app.cli.command("fetch-data")
@click.option("--players", is_flag=True, help="Also fetch player stats for all teams (slow)")
def fetch_data(players):
    """Scrape team data from sports-reference and populate the database."""
    init_db()
    conn = get_connection()

    try:
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
                time.sleep(3.1)

            # Apply draft prospect flags
            print("Applying draft prospect flags...")
            apply_draft_prospects(conn)
            apply_player_flags(conn)

    finally:
        conn.close()

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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    conn = get_connection()
    teams = get_all_teams(conn)
    conn.close()
    return render_template("index.html", teams=teams)


@app.route("/team/<slug>")
def team_detail(slug):
    conn = get_connection()
    team = get_team(conn, slug)
    if not team:
        conn.close()
        return "Team not found", 404

    # Lazy-load players
    ensure_players(conn, slug)

    players = get_players(conn, slug)
    scorer = get_leading_scorer(conn, slug)
    shooter = get_best_three_pt_shooter(conn, slug)
    prospects = get_draft_prospects(conn, slug)
    conn.close()

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

    conn = get_connection()

    # Get team list for dropdowns
    teams = get_all_teams(conn)

    data = None
    if slug1 and slug2:
        # Lazy-load players for both teams
        ensure_players(conn, slug1)
        ensure_players(conn, slug2)
        data = compare_teams(conn, slug1, slug2)

    conn.close()

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


@app.route("/api/teams")
def api_teams():
    conn = get_connection()
    teams = get_all_teams(conn)
    conn.close()
    return jsonify([{"slug": t["slug"], "name": t["name"], "conference": t["conference"]} for t in teams])


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([])
    conn = get_connection()
    results = search_teams(conn, q)
    conn.close()
    return jsonify([{"slug": r["slug"], "name": r["name"], "conference": r["conference"]} for r in results])


if __name__ == "__main__":
    app.run(debug=True)
