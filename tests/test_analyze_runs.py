from analyze_runs import parse_line


def test_parse_line_counts_died_to_na_as_win():
    record = parse_line(
        "Commit:abc123, Seed:SEED, Floor:51, Score:900, Strat: REQUESTED_STRIKE, "
        "DiedTo: N/A, Bosses: Guardian,Champ,Awakened One Elites: Nob Relics: Burning Blood,"
    )

    assert record["commit"] == "abc123"
    assert record["win"] is True
    assert record["died_to"] == "N/A"


def test_parse_line_does_not_count_floor_50_death_as_win():
    record = parse_line(
        "Commit:abc123, Seed:SEED, Floor:50, Score:500, Strat: REQUESTED_STRIKE, "
        "DiedTo: AwakenedOne, Bosses: Guardian,Champ Elites: Nob Relics: Burning Blood,"
    )

    assert record["win"] is False
    assert record["died_to"] == "AwakenedOne"
