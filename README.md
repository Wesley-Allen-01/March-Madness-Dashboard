# March Madness Dashboard

A Flask web dashboard for NCAA Men's D1 Basketball. View and compare team stats, advanced metrics, strength of schedule, key players, and NBA draft prospects for all ~365 D1 teams.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the test suite
uv run pytest

# Fetch all team data (takes ~5 seconds — 2 HTTP requests total)
uv run flask --app app.py fetch-data

# Start the dev server
uv run flask --app app.py run --port 5050 --debug
```

Then open `http://localhost:5050`.

Player stats are **lazy-loaded** on first visit to a team page (one HTTP request per team, ~3 seconds). They are cached in SQLite after that. To pre-fetch all player stats at once (slow — ~20 minutes for all 365 teams):

```bash
uv run flask --app app.py fetch-data --players
```

## Features

- **Index page** — searchable grid of all D1 teams with PPG, Opp PPG, Net Rating, SRS
- **Raw Data** (`/data`) — sortable, filterable full-team table across all tracked stat columns, including NCAA tournament participation
- **Team detail** (`/team/<slug>`) — full stats for a single team:
  - Basic stats: PPG, Opp PPG, RPG, APG, SPG, BPG, TOPG, FG%, 3PT%, FT%
  - Advanced stats with tooltip definitions: OffRtg, DefRtg, Net Rating, Pace, eFG%, TS%, TOV%, ORB%, DRB%, FT Rate, 3PT Rate
  - Strength of Schedule: SRS (primary) + traditional SOS
  - Key players: leading scorer and best 3PT shooter (with jersey numbers)
  - NBA draft prospects (curated list + statistical heuristics)
  - Full roster table with jersey numbers
- **Comparison** (`/compare?team1=<slug>&team2=<slug>`) — side-by-side view with green highlighting on the better value per stat
- **API endpoints**: `GET /api/teams`, `GET /api/search?q=<query>`

## Project Structure

```
app.py                      # Flask app, routes, CLI commands
config.py                   # URLs, stat definitions (labels, tooltips, higher_is_better)
db.py                       # SQLite schema, connection helpers, all query functions
main.py                     # uv entry point stub (unused at runtime)

scrapers/
  sportsref.py              # Scrapes sports-reference.com for team and player stats
  draft_prospects.py        # Loads draft_prospects_2026.json + statistical heuristics

services/
  comparison.py             # compare_teams() — builds side-by-side stat data
  presentation.py           # format_stat_value(), sign_class(), build_stat_definitions()
                            # These are registered as Jinja filters in app.py

templates/
  base.html                 # Shared layout (navbar, container)
  index.html                # Team grid with search
  team.html                 # Single team detail
  comparison.html           # Side-by-side comparison

static/
  css/styles.css            # All styles
  js/main.js                # Team search filter + comparison autocomplete

data/
  draft_prospects_2026.json # Curated NBA draft prospect list (hand-maintained)
  dashboard.db              # SQLite database (gitignored, generated at runtime)
```

## Data Sources

All data comes from **sports-reference.com/cbb** (free, no account needed).

| Data | URL | Notes |
|------|-----|-------|
| Basic team stats | `/cbb/seasons/2026-school-stats.html` | Season totals — divided by games to get per-game values |
| Advanced team stats | `/cbb/seasons/2026-advanced-school-stats.html` | OffRtg, Pace, eFG%, etc. |
| Player stats | `/cbb/schools/<slug>/men/2026.html` | Fetched per-team, cached in SQLite |

### Key scraping gotchas (sports-reference.com)

- The basic stats page returns **season totals**, not per-game — divide by `g` (games)
- Player per-game table ID: `players_per_game` (not `per_game`)
- Player advanced stats table (`players_advanced`) is **hidden in an HTML comment** — use `_find_table()` which scans comments
- Player name column: `data-stat="name_display"` as a `<td>`, **not** a `<th>`
- Jersey numbers: `data-stat="number"` in the `roster` table
- Games column on player pages: `data-stat="games"` (not `g`)
- Rate limit: ~20 req/min — use 3.1s delay between per-team requests

## Stat Definitions

All stat metadata lives in `config.py` as dicts of the form:
```python
"stat_key": ("Display Name", "Tooltip text shown on hover", True/False/None)
```
The third value is `higher_is_better` (used for comparison highlighting). `None` means neutral (e.g. Pace).

`services/presentation.py` provides:
- `build_stat_definitions()` — merges basic + advanced + SOS defs for comparison view
- `format_stat_value(value, key)` — formats a value correctly (%, +/-, decimals)
- `sign_class(value)` — returns `"positive"` or `"negative"` CSS class

Both are registered as Jinja filters in `app.py`:
```python
app.add_template_filter(format_stat_value, "stat_value")
app.add_template_filter(sign_class, "sign_class")
```

## Strength of Schedule

Two SOS metrics are shown:
- **SRS** (Simple Rating System) — margin-of-victory adjusted for opponent strength, iteratively converged. This is the primary "advanced" SOS. Sourced directly from sports-reference.
- **SOS** — traditional strength of schedule (opponents' win percentages). Also from sports-reference.

Both are 0-centered; positive = harder schedule / stronger team.

## Draft Prospects

Detection uses two layers (both can flag a player):
1. **Curated list** — `data/draft_prospects_2026.json`. Each entry: `{"name": "...", "team": "<slug>", "projection": "Lottery|1st Round|2nd Round"}`. Names are matched with `LIKE %name%` so minor spelling differences are OK.
2. **Statistical heuristics** — auto-flags players meeting thresholds:
   - FR/SO with PER ≥ 20 and PPG ≥ 15
   - Any player with BPM ≥ 8.0
   - Usage ≥ 28% + TS% ≥ 58% + PPG ≥ 16

Curated entries take precedence (`draft_projection` is set first; heuristic uses `COALESCE` to avoid overwriting).

## Database

SQLite at `data/dashboard.db` (gitignored). Two tables:

- **`teams`** — one row per team, all basic + advanced stats + SOS
- **`players`** — one row per player per team, includes jersey number, class year, per-game stats, and advanced stats (PER, BPM, WS, usage rate)

`db.py` exposes `db_session()` as a context manager — always use it instead of calling `get_connection()` directly in new code, so the connection is always closed:

```python
with db_session() as conn:
    team = get_team(conn, slug)
```

## Development

Run `uv run pytest` after changes to verify the Flask routes, database helpers, presentation helpers, draft prospect logic, scraper parsing, and CLI behavior still work.

The `.claude/launch.json` is configured for the Claude preview panel:
```json
{ "runtimeExecutable": "uv", "runtimeArgs": ["run", "flask", "--app", "app.py", "run", "--port", "5050", "--debug"] }
```

`main.py` is the uv-generated entry point stub — it is not used at runtime.
