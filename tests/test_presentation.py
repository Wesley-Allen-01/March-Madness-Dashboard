from services import presentation


def test_build_stat_definitions_includes_all_sections():
    definitions = presentation.build_stat_definitions()

    assert "wins" in definitions
    assert "offensive_rating" in definitions
    assert "srs" in definitions


def test_row_to_dict_handles_none_and_row_objects(seeded_db):
    import db

    assert presentation.row_to_dict(None) is None

    with db.db_session() as conn:
        row = db.get_team(conn, "alpha")

    assert presentation.row_to_dict(row)["name"] == "Alpha University"


def test_sign_class_returns_expected_css_class():
    assert presentation.sign_class(None) == ""
    assert presentation.sign_class(3.2) == "positive"
    assert presentation.sign_class(-0.5) == "negative"
    assert presentation.sign_class(0) == ""


def test_format_stat_value_uses_project_conventions():
    assert presentation.format_stat_value(None, "ppg") == "\u2014"
    assert presentation.format_stat_value(0.487, "fg_pct") == "48.7%"
    assert presentation.format_stat_value(48.7, "fg_pct") == "48.7%"
    assert presentation.format_stat_value(14.9, "tov_pct") == "14.9%"
    assert presentation.format_stat_value(6.4, "sos") == "+6.40"
    assert presentation.format_stat_value(69.7, "pace") == "69.7"
    assert presentation.format_stat_value(28.0, "wins") == "28.0"
