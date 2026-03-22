import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "dashboard.db")
DRAFT_PROSPECTS_PATH = os.path.join(BASE_DIR, "data", "draft_prospects_2026.json")
TOURNAMENT_TEAMS_PATH = os.path.join(BASE_DIR, "data", "tournament_teams_2026.json")

SEASON = 2026

SPORTSREF_BASE = "https://www.sports-reference.com/cbb"
SPORTSREF_BASIC_URL = f"{SPORTSREF_BASE}/seasons/{SEASON}-school-stats.html"
SPORTSREF_ADVANCED_URL = f"{SPORTSREF_BASE}/seasons/{SEASON}-advanced-school-stats.html"
SPORTSREF_TEAM_URL = f"{SPORTSREF_BASE}/schools/{{slug}}/{SEASON}.html"

REQUEST_DELAY = 3.1  # seconds between per-team requests (rate limit)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Advanced stat definitions: (display_name, tooltip, higher_is_better)
ADVANCED_STAT_DEFINITIONS = {
    "offensive_rating": (
        "Offensive Rating",
        "Points scored per 100 possessions. Higher means a more efficient offense.",
        True,
    ),
    "defensive_rating": (
        "Defensive Rating",
        "Points allowed per 100 possessions. Lower means a better defense.",
        False,
    ),
    "net_rating": (
        "Net Rating",
        "Offensive Rating minus Defensive Rating. Positive means the team outscores opponents on a per-possession basis.",
        True,
    ),
    "pace": (
        "Pace",
        "Estimated possessions per 40 minutes. Higher means a faster-tempo team.",
        None,  # neutral — neither strictly better
    ),
    "efg_pct": (
        "Effective FG%",
        "Adjusts FG% for the extra value of three-pointers. Formula: (FG + 0.5 × 3FG) / FGA.",
        True,
    ),
    "ts_pct": (
        "True Shooting %",
        "Measures shooting efficiency including free throws. Formula: Points / (2 × (FGA + 0.44 × FTA)).",
        True,
    ),
    "tov_pct": (
        "Turnover Rate",
        "Turnovers per 100 plays. Formula: TOV / (FGA + 0.44 × FTA + TOV). Lower is better.",
        False,
    ),
    "orb_pct": (
        "Offensive Rebound %",
        "Percentage of available offensive rebounds grabbed. Higher means more second-chance opportunities.",
        True,
    ),
    "drb_pct": (
        "Defensive Rebound %",
        "Percentage of available defensive rebounds grabbed. Higher means fewer second chances for opponents.",
        True,
    ),
    "ft_rate": (
        "Free Throw Rate",
        "Free throw attempts per field goal attempt (FTA/FGA). Higher means the team gets to the line more.",
        True,
    ),
    "three_pt_rate": (
        "3-Point Rate",
        "Three-point attempts as a share of all field goal attempts (3PA/FGA).",
        None,
    ),
}

# Basic stat definitions: (display_name, tooltip, higher_is_better)
BASIC_STAT_DEFINITIONS = {
    "wins": ("Wins", "Total wins this season", True),
    "losses": ("Losses", "Total losses this season", False),
    "ppg": ("PPG", "Points per game", True),
    "opp_ppg": ("Opp PPG", "Opponent points per game (points allowed)", False),
    "rpg": ("RPG", "Rebounds per game", True),
    "apg": ("APG", "Assists per game", True),
    "spg": ("SPG", "Steals per game", True),
    "bpg": ("BPG", "Blocks per game", True),
    "topg": ("TOPG", "Turnovers per game. Lower is better.", False),
    "fg_pct": ("FG%", "Field goal percentage", True),
    "three_pt_pct": ("3PT%", "Three-point field goal percentage", True),
    "ft_pct": ("FT%", "Free throw percentage", True),
}

SOS_DEFINITIONS = {
    "srs": (
        "SRS",
        "Simple Rating System: a margin-of-victory metric adjusted for strength of schedule. "
        "Accounts for opponent quality iteratively — beating good teams counts more. "
        "0 is average; positive means above average.",
        True,
    ),
    "sos": (
        "Strength of Schedule",
        "Traditional SOS based on opponents' records. 0 is average; positive means a harder schedule.",
        True,
    ),
}
