import db


def test_index_page_renders_team_cards(client):
    response = client.get("/")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Alpha University" in text
    assert "Beta State" in text
    assert "NCAA Men's Basketball Teams" in text


def test_team_detail_page_renders_existing_team(client, monkeypatch):
    import app as app_module

    calls = []

    def fake_ensure_players(conn, slug):
        calls.append(slug)

    monkeypatch.setattr(app_module, "ensure_players", fake_ensure_players)

    response = client.get("/team/alpha")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert calls == ["alpha"]
    assert "Leading Scorer" in text
    assert "Alex Ace" in text
    assert "Potential NBA Draft Prospects" in text


def test_team_detail_returns_404_for_unknown_team(client):
    response = client.get("/team/missing")

    assert response.status_code == 404
    assert response.get_data(as_text=True) == "Team not found"


def test_comparison_page_renders_empty_state_without_query(client):
    response = client.get("/compare")

    assert response.status_code == 200
    assert "Select two teams above to see a side-by-side comparison." in response.get_data(as_text=True)


def test_comparison_page_renders_comparison_results(client, monkeypatch):
    import app as app_module

    calls = []

    def fake_ensure_players(conn, slug):
        calls.append(slug)

    monkeypatch.setattr(app_module, "ensure_players", fake_ensure_players)

    response = client.get("/compare?team1=alpha&team2=beta")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert calls == ["alpha", "beta"]
    assert "Alpha University" in text
    assert "Beta State" in text
    assert "Draft Prospects" in text


def test_raw_data_page_renders_sortable_team_table(client, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "load_tournament_team_slugs", lambda: {"alpha"})

    response = client.get("/data")

    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Raw Team Data" in text
    assert "Alpha University" in text
    assert "Tournament" in text
    assert 'data-value="yes"' in text
    assert 'data-value="no"' in text
    assert "Conference" in text
    assert "Offensive Rating" in text
    assert "data-raw-data-table" in text


def test_api_teams_returns_brief_payload(client):
    response = client.get("/api/teams")

    assert response.status_code == 200
    assert response.get_json() == [
        {"slug": "alpha", "name": "Alpha University", "conference": "Big Test"},
        {"slug": "beta", "name": "Beta State", "conference": "Metro Test"},
    ]


def test_api_search_requires_two_characters_and_returns_matches(client):
    assert client.get("/api/search?q=a").get_json() == []
    assert client.get("/api/search?q=Beta").get_json() == [
        {"slug": "beta", "name": "Beta State", "conference": "Metro Test"}
    ]


def test_ensure_players_fetches_and_flags_uncached_roster(isolated_db, monkeypatch):
    import app as app_module

    with db.db_session() as conn:
        db.upsert_team(conn, {"slug": "gamma", "name": "Gamma Tech", "conference": "Future"})
        conn.commit()

    monkeypatch.setattr(
        app_module,
        "scrape_team_players",
        lambda slug: [
            {
                "name": "Gamma Guard",
                "class_year": "FR",
                "position": "G",
                "games_played": 30,
                "ppg": 17.0,
                "rpg": 4.0,
                "apg": 5.0,
                "three_pt_pct": 0.41,
                "three_pt_attempts_pg": 4.5,
                "per": 21.0,
                "bpm": 8.6,
                "usage_rate": 29.0,
                "ts_pct": 0.6,
            }
        ],
    )

    draft_calls = []
    flag_calls = []
    monkeypatch.setattr(app_module, "apply_draft_prospects", lambda conn: draft_calls.append("draft"))
    monkeypatch.setattr(app_module, "apply_player_flags", lambda conn: flag_calls.append("flags"))

    with db.db_session() as conn:
        app_module.ensure_players(conn, "gamma")
        players = db.get_players(conn, "gamma")

    assert [player["name"] for player in players] == ["Gamma Guard"]
    assert draft_calls == ["draft"]
    assert flag_calls == ["flags"]


def test_fetch_data_cli_populates_database_and_optional_players(cli_runner, monkeypatch):
    import app as app_module

    monkeypatch.setattr(app_module, "init_db", lambda: None)
    monkeypatch.setattr(app_module, "scrape_basic_team_stats", lambda: [{"slug": "alpha", "name": "Alpha University"}])
    monkeypatch.setattr(app_module, "scrape_advanced_team_stats", lambda: {"alpha": {"pace": 70.0}})
    monkeypatch.setattr(
        app_module,
        "merge_team_data",
        lambda basic, advanced: [{"slug": "alpha", "name": "Alpha University", "pace": 70.0}],
    )
    monkeypatch.setattr(app_module, "time", type("FakeTime", (), {"sleep": staticmethod(lambda seconds: None)}))

    saved_teams = []
    saved_players = []
    monkeypatch.setattr(app_module, "upsert_team", lambda conn, team: saved_teams.append(team.copy()))
    monkeypatch.setattr(app_module, "upsert_players", lambda conn, slug, players: saved_players.append((slug, players)))
    monkeypatch.setattr(app_module, "scrape_team_players", lambda slug: [{"name": "Gamma Guard", "ppg": 17.0}])

    draft_calls = []
    flag_calls = []
    monkeypatch.setattr(app_module, "apply_draft_prospects", lambda conn: draft_calls.append("draft"))
    monkeypatch.setattr(app_module, "apply_player_flags", lambda conn: flag_calls.append("flags"))

    result = cli_runner.invoke(args=["fetch-data", "--players"])

    assert result.exit_code == 0
    assert saved_teams == [{"slug": "alpha", "name": "Alpha University", "pace": 70.0}]
    assert saved_players == [("alpha", [{"name": "Gamma Guard", "ppg": 17.0}])]
    assert draft_calls == ["draft"]
    assert flag_calls == ["flags"]
    assert "Done!" in result.output
