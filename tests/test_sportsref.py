from scrapers import sportsref


BASIC_HTML = """
<table id="basic_school_stats">
  <tbody>
    <tr>
      <td data-stat="school_name"><a href="/cbb/schools/alpha/men/2026.html">Alpha University NCAA</a></td>
      <td data-stat="g">10</td>
      <td data-stat="wins">8</td>
      <td data-stat="losses">2</td>
      <td data-stat="pts">800</td>
      <td data-stat="opp_pts">650</td>
      <td data-stat="trb">350</td>
      <td data-stat="ast">180</td>
      <td data-stat="stl">70</td>
      <td data-stat="blk">40</td>
      <td data-stat="tov">110</td>
      <td data-stat="fg_pct">0.500</td>
      <td data-stat="fg3_pct">0.390</td>
      <td data-stat="ft_pct">0.780</td>
      <td data-stat="srs">14.2</td>
      <td data-stat="sos">5.8</td>
    </tr>
    <tr class="thead"><th scope="col">Header</th></tr>
  </tbody>
</table>
"""

ADVANCED_HTML = """
<table id="adv_school_stats">
  <tbody>
    <tr>
      <td data-stat="school_name"><a href="/cbb/schools/alpha/men/2026.html">Alpha University</a></td>
      <td data-stat="off_rtg">120.0</td>
      <td data-stat="pts">800</td>
      <td data-stat="opp_pts">650</td>
      <td data-stat="pace">69.1</td>
      <td data-stat="efg_pct">0.560</td>
      <td data-stat="tov_pct">15.1</td>
      <td data-stat="orb_pct">30.2</td>
      <td data-stat="ft_rate">0.340</td>
      <td data-stat="fg3a_per_fga_pct">0.410</td>
      <td data-stat="ts_pct">0.605</td>
    </tr>
  </tbody>
</table>
"""

TEAM_HTML = """
<table id="roster">
  <tbody>
    <tr>
      <td data-stat="number">1</td>
      <td data-stat="name_display">Alex Ace</td>
      <td data-stat="class">FR</td>
    </tr>
  </tbody>
</table>
<table id="players_per_game">
  <tbody>
    <tr>
      <td data-stat="name_display">Alex Ace</td>
      <td data-stat="pos">G</td>
      <td data-stat="games">30</td>
      <td data-stat="mp_per_g">32.4</td>
      <td data-stat="pts_per_g">18.2</td>
      <td data-stat="trb_per_g">5.1</td>
      <td data-stat="ast_per_g">4.6</td>
      <td data-stat="stl_per_g">1.9</td>
      <td data-stat="blk_per_g">0.3</td>
      <td data-stat="tov_per_g">2.1</td>
      <td data-stat="fg_pct">0.492</td>
      <td data-stat="fg3_pct">0.411</td>
      <td data-stat="fg3_per_g">2.8</td>
      <td data-stat="fg3a_per_g">6.1</td>
      <td data-stat="ft_pct">0.824</td>
    </tr>
  </tbody>
</table>
<!--
<table id="players_advanced">
  <tbody>
    <tr>
      <td data-stat="name_display">Alex Ace</td>
      <td data-stat="per">24.1</td>
      <td data-stat="ts_pct">0.622</td>
      <td data-stat="efg_pct">0.583</td>
      <td data-stat="bpm">9.1</td>
      <td data-stat="ws">5.8</td>
      <td data-stat="usg_pct">29.5</td>
    </tr>
  </tbody>
</table>
-->
"""


def test_parse_helpers_cover_invalid_input():
    assert sportsref._parse_float(None) is None
    assert sportsref._parse_float("-") is None
    assert sportsref._parse_float("3.4") == 3.4
    assert sportsref._parse_int(None) is None
    assert sportsref._parse_int("-") is None
    assert sportsref._parse_int("7") == 7
    assert sportsref._extract_slug("/cbb/schools/alpha/men/2026.html") == "alpha"
    assert sportsref._extract_slug("/other/path") is None
    assert sportsref._per_game(90, 0) is None
    assert sportsref._per_game(90, 3) == 30.0


def test_find_table_can_read_comment_wrapped_markup():
    table = sportsref._find_table(TEAM_HTML, "players_advanced")

    assert table is not None
    assert table["id"] == "players_advanced"


def test_scrape_basic_team_stats_uses_per_game_conversion(monkeypatch):
    monkeypatch.setattr(sportsref, "_fetch", lambda url: BASIC_HTML)

    teams = sportsref.scrape_basic_team_stats()

    assert teams == [
        {
            "slug": "alpha",
            "name": "Alpha University",
            "wins": 8,
            "losses": 2,
            "fg_pct": 0.5,
            "three_pt_pct": 0.39,
            "ft_pct": 0.78,
            "srs": 14.2,
            "sos": 5.8,
            "ppg": 80.0,
            "opp_ppg": 65.0,
            "rpg": 35.0,
            "apg": 18.0,
            "spg": 7.0,
            "bpg": 4.0,
            "topg": 11.0,
        }
    ]


def test_scrape_advanced_team_stats_calculates_defensive_and_net_rating(monkeypatch):
    monkeypatch.setattr(sportsref, "_fetch", lambda url: ADVANCED_HTML)

    advanced = sportsref.scrape_advanced_team_stats()

    assert advanced["alpha"]["offensive_rating"] == 120.0
    assert advanced["alpha"]["defensive_rating"] == 97.5
    assert advanced["alpha"]["net_rating"] == 22.5
    assert advanced["alpha"]["three_pt_rate"] == 0.41


def test_scrape_team_players_merges_roster_and_advanced_stats(monkeypatch):
    monkeypatch.setattr(sportsref, "_fetch", lambda url: TEAM_HTML)

    players = sportsref.scrape_team_players("alpha")

    assert players == [
        {
            "name": "Alex Ace",
            "position": "G",
            "games_played": 30,
            "jersey_number": "1",
            "class_year": "FR",
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
        }
    ]
