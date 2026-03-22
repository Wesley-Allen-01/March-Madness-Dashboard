"""Scraper for sports-reference.com college basketball stats."""

import re

import requests
from bs4 import BeautifulSoup, Comment

from config import (
    SEASON,
    SPORTSREF_BASE,
    USER_AGENT,
)

HEADERS = {"User-Agent": USER_AGENT}

BASIC_URL = f"{SPORTSREF_BASE}/seasons/{SEASON}-school-stats.html"
ADVANCED_URL = f"{SPORTSREF_BASE}/seasons/{SEASON}-advanced-school-stats.html"
TEAM_PAGE_URL = f"{SPORTSREF_BASE}/schools/{{team_slug}}/men/{SEASON}.html"

BASIC_TEAM_STAT_MAP = {
    "wins": "wins",
    "losses": "losses",
    "fg_pct": "fg_pct",
    "three_pt_pct": "fg3_pct",
    "ft_pct": "ft_pct",
    "srs": "srs",
    "sos": "sos",
}
PER_GAME_TEAM_STAT_MAP = {
    "ppg": "pts",
    "opp_ppg": "opp_pts",
    "rpg": "trb",
    "apg": "ast",
    "spg": "stl",
    "bpg": "blk",
    "topg": "tov",
}
ADVANCED_TEAM_STAT_MAP = {
    "pace": "pace",
    "efg_pct": "efg_pct",
    "tov_pct": "tov_pct",
    "orb_pct": "orb_pct",
    "ft_rate": "ft_rate",
    "three_pt_rate": "fg3a_per_fga_pct",
    "ts_pct": "ts_pct",
}
PLAYER_STAT_MAP = {
    "minutes_per_game": "mp_per_g",
    "ppg": "pts_per_g",
    "rpg": "trb_per_g",
    "apg": "ast_per_g",
    "spg": "stl_per_g",
    "bpg": "blk_per_g",
    "topg": "tov_per_g",
    "fg_pct": "fg_pct",
    "three_pt_pct": "fg3_pct",
    "three_pt_made_pg": "fg3_per_g",
    "three_pt_attempts_pg": "fg3a_per_g",
    "ft_pct": "ft_pct",
}
ADVANCED_PLAYER_STAT_MAP = {
    "per": "per",
    "ts_pct": "ts_pct",
    "efg_pct": "efg_pct",
    "bpm": "bpm",
    "ws": "ws",
    "usage_rate": "usg_pct",
}


def _fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def _parse_float(val):
    if val is None:
        return None
    val = val.strip()
    if val == "" or val == "-":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _parse_int(val):
    if val is None:
        return None
    val = val.strip()
    if val == "" or val == "-":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _extract_slug(href):
    """Extract team slug from href like /cbb/schools/houston/men/2026.html"""
    if not href:
        return None
    m = re.search(r"/cbb/schools/([^/]+)/", href)
    return m.group(1) if m else None


def _find_table(html, table_id):
    """Find a table by ID, checking HTML comments too (SR hides some tables in comments)."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id=table_id)
    if table:
        return table
    # Sports-reference sometimes hides tables inside HTML comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        if table_id in comment:
            comment_soup = BeautifulSoup(comment, "lxml")
            table = comment_soup.find("table", id=table_id)
            if table:
                return table
    return None


def _get_stat(row, stat_name):
    """Get a stat value from a table row by data-stat attribute."""
    td = row.find("td", {"data-stat": stat_name})
    if td is None:
        # Try th too (some columns use th)
        td = row.find("th", {"data-stat": stat_name})
    return td.get_text(strip=True) if td else None


def _find_first_table(html, soup, *table_ids):
    """Return the first matching table from the page, including comment-wrapped tables."""
    for table_id in table_ids:
        table = soup.find("table", id=table_id) or _find_table(html, table_id)
        if table:
            return table
    return None


def _iter_data_rows(table):
    """Yield non-header rows from a sports-reference table body."""
    if table is None:
        return

    tbody = table.find("tbody")
    if tbody is None:
        return

    for row in tbody.find_all("tr"):
        if row.find("th", {"scope": "col"}):
            continue
        if "thead" in row.get("class", []):
            continue
        yield row


def _extract_player_name(row):
    """Read a player name from either the team-page or league-page column layout."""
    player_cell = row.find(["td", "th"], {"data-stat": "name_display"})
    if player_cell is None:
        player_cell = row.find(["td", "th"], {"data-stat": "player"})
    if not player_cell:
        return None
    return player_cell.get_text(strip=True)


def _read_float_stats(row, stat_map):
    return {field: _parse_float(_get_stat(row, source)) for field, source in stat_map.items()}


def _read_int_stats(row, stat_map):
    return {field: _parse_int(_get_stat(row, source)) for field, source in stat_map.items()}


def _per_game(total, games):
    if total is None or not games:
        return None
    return round(total / games, 1)


def scrape_basic_team_stats():
    """Scrape basic per-game stats for all D1 teams. Returns list of dicts."""
    print("Fetching basic team stats...")
    html = _fetch(BASIC_URL)
    soup = BeautifulSoup(html, "lxml")

    table = _find_first_table(html, soup, "basic_school_stats")
    if not table:
        raise RuntimeError("Could not find basic_school_stats table")

    teams = []

    for row in _iter_data_rows(table):
        school_cell = row.find("td", {"data-stat": "school_name"})
        if not school_cell:
            continue

        link = school_cell.find("a")
        if not link:
            continue

        slug = _extract_slug(link.get("href", ""))
        if not slug:
            continue

        name = link.get_text(strip=True)
        # Remove "NCAA" suffix if present
        name = name.replace("NCAA", "").strip()

        games = _parse_int(_get_stat(row, "g"))
        if not games or games == 0:
            continue

        team = {
            "slug": slug,
            "name": name,
            **_read_int_stats(row, {"wins": "wins", "losses": "losses"}),
            **_read_float_stats(row, BASIC_TEAM_STAT_MAP),
        }
        for field, source_stat in PER_GAME_TEAM_STAT_MAP.items():
            team[field] = _per_game(_parse_float(_get_stat(row, source_stat)), games)
        teams.append(team)

    print(f"  Found {len(teams)} teams with basic stats")
    return teams


def scrape_advanced_team_stats():
    """Scrape advanced stats for all D1 teams. Returns dict keyed by slug."""
    print("Fetching advanced team stats...")
    html = _fetch(ADVANCED_URL)
    soup = BeautifulSoup(html, "lxml")

    table = _find_first_table(html, soup, "adv_school_stats")
    if not table:
        raise RuntimeError("Could not find adv_school_stats table")

    advanced = {}

    for row in _iter_data_rows(table):
        school_cell = row.find("td", {"data-stat": "school_name"})
        if not school_cell:
            continue
        link = school_cell.find("a")
        if not link:
            continue

        slug = _extract_slug(link.get("href", ""))
        if not slug:
            continue

        off_rtg = _parse_float(_get_stat(row, "off_rtg"))
        pts = _parse_float(_get_stat(row, "pts"))
        opp_pts = _parse_float(_get_stat(row, "opp_pts"))

        # Compute defensive rating: DefRtg = OffRtg * (OppPts / Pts)
        def_rtg = None
        if off_rtg and pts and opp_pts and pts > 0:
            def_rtg = round(off_rtg * (opp_pts / pts), 1)

        net_rtg = None
        if off_rtg and def_rtg:
            net_rtg = round(off_rtg - def_rtg, 1)

        advanced[slug] = {
            **_read_float_stats(row, ADVANCED_TEAM_STAT_MAP),
            "offensive_rating": off_rtg,
            "defensive_rating": def_rtg,
            "net_rating": net_rtg,
        }

    print(f"  Found advanced stats for {len(advanced)} teams")
    return advanced


def scrape_team_players(team_slug):
    """Scrape player stats for a single team. Returns list of player dicts."""
    url = TEAM_PAGE_URL.format(team_slug=team_slug)
    print(f"  Fetching players for {team_slug}...")
    html = _fetch(url)
    soup = BeautifulSoup(html, "lxml")

    # First get roster for class years and jersey numbers
    class_years = {}
    jersey_numbers = {}
    roster_table = _find_first_table(html, soup, "roster")
    if roster_table:
        for row in _iter_data_rows(roster_table):
            player_name = _extract_player_name(row)
            if not player_name:
                continue
            class_cell = row.find("td", {"data-stat": "class"})
            if class_cell:
                class_years[player_name] = class_cell.get_text(strip=True)
            number_cell = row.find("td", {"data-stat": "number"})
            if number_cell:
                num = number_cell.get_text(strip=True)
                if num:
                    jersey_numbers[player_name] = num

    per_game_table = _find_first_table(html, soup, "players_per_game", "per_game")
    if not per_game_table:
        print(f"    No per_game table found for {team_slug}")
        return []

    adv_table = _find_first_table(html, soup, "players_advanced", "advanced")

    adv_stats = {}
    if adv_table:
        for row in _iter_data_rows(adv_table):
            player_name = _extract_player_name(row)
            if not player_name:
                continue
            adv_stats[player_name] = _read_float_stats(row, ADVANCED_PLAYER_STAT_MAP)

    players = []
    for row in _iter_data_rows(per_game_table):
        player_name = _extract_player_name(row)
        if not player_name:
            continue

        if player_name.lower() in ("team totals", "school totals"):
            continue

        pos = _get_stat(row, "pos") or ""
        games = _parse_int(_get_stat(row, "games"))
        if not games:
            games = _parse_int(_get_stat(row, "g"))
        if not games:
            continue

        player = {
            "name": player_name,
            "jersey_number": jersey_numbers.get(player_name),
            "class_year": class_years.get(player_name),
            "position": pos.strip(),
            "games_played": games,
            **_read_float_stats(row, PLAYER_STAT_MAP),
        }

        if player_name in adv_stats:
            player.update(adv_stats[player_name])

        players.append(player)

    return players


def merge_team_data(basic_list, advanced_dict):
    """Merge basic and advanced stats into unified team dicts."""
    merged = []
    for team in basic_list:
        slug = team["slug"]
        adv = advanced_dict.get(slug, {})
        team.update(adv)

        orb = team.get("orb_pct")
        if orb is not None:
            # Sports Reference does not publish a direct team DRB% column on this page.
            team.setdefault("drb_pct", round(100.0 - orb, 1))
        else:
            team.setdefault("drb_pct", None)

        merged.append(team)

    return merged
