"""Scraper for sports-reference.com college basketball stats."""

import re
import time
import requests
from bs4 import BeautifulSoup, Comment
from config import (
    SPORTSREF_BASE,
    SEASON,
    USER_AGENT,
    REQUEST_DELAY,
)

HEADERS = {"User-Agent": USER_AGENT}

BASIC_URL = f"{SPORTSREF_BASE}/seasons/{SEASON}-school-stats.html"
ADVANCED_URL = f"{SPORTSREF_BASE}/seasons/{SEASON}-advanced-school-stats.html"


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


def scrape_basic_team_stats():
    """Scrape basic per-game stats for all D1 teams. Returns list of dicts."""
    print("Fetching basic team stats...")
    html = _fetch(BASIC_URL)
    soup = BeautifulSoup(html, "lxml")

    # The table ID is typically "basic_school_stats"
    table = soup.find("table", id="basic_school_stats")
    if not table:
        # Try in comments
        table = _find_table(html, "basic_school_stats")
    if not table:
        raise RuntimeError("Could not find basic_school_stats table")

    tbody = table.find("tbody")
    teams = []

    for row in tbody.find_all("tr"):
        # Skip header rows that repeat in the middle
        if row.find("th", {"scope": "col"}):
            continue
        if "thead" in row.get("class", []):
            continue

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

        # Stats are season totals — compute per-game values
        pts = _parse_float(_get_stat(row, "pts"))
        opp_pts = _parse_float(_get_stat(row, "opp_pts"))
        trb = _parse_float(_get_stat(row, "trb"))
        ast = _parse_float(_get_stat(row, "ast"))
        stl = _parse_float(_get_stat(row, "stl"))
        blk = _parse_float(_get_stat(row, "blk"))
        tov = _parse_float(_get_stat(row, "tov"))

        def _per_game(val):
            if val is not None and games:
                return round(val / games, 1)
            return None

        team = {
            "slug": slug,
            "name": name,
            "wins": _parse_int(_get_stat(row, "wins")),
            "losses": _parse_int(_get_stat(row, "losses")),
            "ppg": _per_game(pts),
            "opp_ppg": _per_game(opp_pts),
            "fg_pct": _parse_float(_get_stat(row, "fg_pct")),
            "three_pt_pct": _parse_float(_get_stat(row, "fg3_pct")),
            "ft_pct": _parse_float(_get_stat(row, "ft_pct")),
            "rpg": _per_game(trb),
            "apg": _per_game(ast),
            "spg": _per_game(stl),
            "bpg": _per_game(blk),
            "topg": _per_game(tov),
            "srs": _parse_float(_get_stat(row, "srs")),
            "sos": _parse_float(_get_stat(row, "sos")),
        }
        teams.append(team)

    print(f"  Found {len(teams)} teams with basic stats")
    return teams


def scrape_advanced_team_stats():
    """Scrape advanced stats for all D1 teams. Returns dict keyed by slug."""
    print("Fetching advanced team stats...")
    html = _fetch(ADVANCED_URL)
    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id="adv_school_stats")
    if not table:
        table = _find_table(html, "adv_school_stats")
    if not table:
        raise RuntimeError("Could not find adv_school_stats table")

    tbody = table.find("tbody")
    advanced = {}

    for row in tbody.find_all("tr"):
        if row.find("th", {"scope": "col"}):
            continue
        if "thead" in row.get("class", []):
            continue

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
            "pace": _parse_float(_get_stat(row, "pace")),
            "offensive_rating": off_rtg,
            "defensive_rating": def_rtg,
            "net_rating": net_rtg,
            "efg_pct": _parse_float(_get_stat(row, "efg_pct")),
            "tov_pct": _parse_float(_get_stat(row, "tov_pct")),
            "orb_pct": _parse_float(_get_stat(row, "orb_pct")),
            "ft_rate": _parse_float(_get_stat(row, "ft_rate")),
            "three_pt_rate": _parse_float(_get_stat(row, "fg3a_per_fga_pct")),
            "ts_pct": _parse_float(_get_stat(row, "ts_pct")),
        }

    print(f"  Found advanced stats for {len(advanced)} teams")
    return advanced


def scrape_team_players(team_slug):
    """Scrape player stats for a single team. Returns list of player dicts."""
    url = f"{SPORTSREF_BASE}/schools/{team_slug}/men/{SEASON}.html"
    print(f"  Fetching players for {team_slug}...")
    html = _fetch(url)
    soup = BeautifulSoup(html, "lxml")

    # First get roster for class years and jersey numbers
    class_years = {}
    jersey_numbers = {}
    roster_table = soup.find("table", id="roster")
    if not roster_table:
        roster_table = _find_table(html, "roster")
    if roster_table:
        for row in roster_table.find("tbody").find_all("tr"):
            player_cell = row.find("th", {"data-stat": "player"})
            if player_cell is None:
                player_cell = row.find("td", {"data-stat": "player"})
            if not player_cell:
                continue
            pname = player_cell.get_text(strip=True)
            class_cell = row.find("td", {"data-stat": "class"})
            if class_cell:
                class_years[pname] = class_cell.get_text(strip=True)
            number_cell = row.find("td", {"data-stat": "number"})
            if number_cell:
                num = number_cell.get_text(strip=True)
                if num:
                    jersey_numbers[pname] = num

    # Per-game stats table (players_per_game on team pages)
    per_game_table = soup.find("table", id="players_per_game")
    if not per_game_table:
        per_game_table = _find_table(html, "players_per_game")
    if not per_game_table:
        # Fallback to other possible IDs
        per_game_table = soup.find("table", id="per_game")
        if not per_game_table:
            per_game_table = _find_table(html, "per_game")
    if not per_game_table:
        print(f"    No per_game table found for {team_slug}")
        return []

    # Advanced stats table for PER, BPM, WS, usage (hidden in HTML comment)
    adv_table = soup.find("table", id="players_advanced")
    if not adv_table:
        adv_table = _find_table(html, "players_advanced")
    if not adv_table:
        adv_table = soup.find("table", id="advanced")
        if not adv_table:
            adv_table = _find_table(html, "advanced")

    adv_stats = {}
    if adv_table:
        for row in adv_table.find("tbody").find_all("tr"):
            if row.find("th", {"scope": "col"}):
                continue
            # name_display is a td on team pages, player is a th on some pages
            player_cell = row.find(["td", "th"], {"data-stat": "name_display"})
            if player_cell is None:
                player_cell = row.find(["td", "th"], {"data-stat": "player"})
            if not player_cell:
                continue
            pname = player_cell.get_text(strip=True)
            adv_stats[pname] = {
                "per": _parse_float(_get_stat(row, "per")),
                "ts_pct": _parse_float(_get_stat(row, "ts_pct")),
                "efg_pct": _parse_float(_get_stat(row, "efg_pct")),
                "bpm": _parse_float(_get_stat(row, "bpm")),
                "ws": _parse_float(_get_stat(row, "ws")),
                "usage_rate": _parse_float(_get_stat(row, "usg_pct")),
            }

    players = []
    tbody = per_game_table.find("tbody")

    for row in tbody.find_all("tr"):
        if row.find("th", {"scope": "col"}):
            continue

        # name_display is a td on team pages, player is a th on some pages
        player_cell = row.find(["td", "th"], {"data-stat": "name_display"})
        if player_cell is None:
            player_cell = row.find(["td", "th"], {"data-stat": "player"})
        if not player_cell:
            continue

        pname = player_cell.get_text(strip=True)
        if not pname or pname.lower() in ("team totals", "school totals"):
            continue

        pos = _get_stat(row, "pos") or ""
        games = _parse_int(_get_stat(row, "games"))
        if not games:
            games = _parse_int(_get_stat(row, "g"))
        if not games:
            continue

        player = {
            "name": pname,
            "jersey_number": jersey_numbers.get(pname),
            "class_year": class_years.get(pname),
            "position": pos.strip(),
            "games_played": games,
            "minutes_per_game": _parse_float(_get_stat(row, "mp_per_g")),
            "ppg": _parse_float(_get_stat(row, "pts_per_g")),
            "rpg": _parse_float(_get_stat(row, "trb_per_g")),
            "apg": _parse_float(_get_stat(row, "ast_per_g")),
            "spg": _parse_float(_get_stat(row, "stl_per_g")),
            "bpg": _parse_float(_get_stat(row, "blk_per_g")),
            "topg": _parse_float(_get_stat(row, "tov_per_g")),
            "fg_pct": _parse_float(_get_stat(row, "fg_pct")),
            "three_pt_pct": _parse_float(_get_stat(row, "fg3_pct")),
            "three_pt_made_pg": _parse_float(_get_stat(row, "fg3_per_g")),
            "three_pt_attempts_pg": _parse_float(_get_stat(row, "fg3a_per_g")),
            "ft_pct": _parse_float(_get_stat(row, "ft_pct")),
        }

        # Merge advanced stats if available
        if pname in adv_stats:
            player.update(adv_stats[pname])

        players.append(player)

    return players


def merge_team_data(basic_list, advanced_dict):
    """Merge basic and advanced stats into unified team dicts."""
    merged = []
    for team in basic_list:
        slug = team["slug"]
        adv = advanced_dict.get(slug, {})
        team.update(adv)

        # drb_pct: estimate as 100 - orb_pct (approximate)
        orb = team.get("orb_pct")
        if orb is not None:
            team.setdefault("drb_pct", round(100.0 - orb, 1))
        else:
            team.setdefault("drb_pct", None)

        merged.append(team)

    return merged
