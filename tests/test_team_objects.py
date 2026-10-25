"""Public team API, separate from wire-layout tests."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from civ4save import SaveFile
from civ4save.objects import Team, TeamRelation
from civ4save.vanilla import enums as e


def test_team_conversion():
    tech_count = max(tech.value for tech in e.TechType) + 1
    project_count = max(project.value for project in e.ProjectType) + 1
    raw = SimpleNamespace(
        id=7,
        num_members=2,
        alive_count=1,
        ever_alive_count=2,
        num_cities=3,
        total_population=42,
        total_land=85,
        nuke_interception=50,
        vassal_power=12,
        master_power=34,
        capitulated=True,
        has_tech=[True] + [False] * (tech_count - 2) + [True],
        no_trade_tech=[False] * (tech_count - 1) + [True],
        research_progress=[123] + [0] * (tech_count - 1),
        project_count=[2] + [0] * (project_count - 1),
        has_met=[False, True],
        at_war=[False, True],
        open_borders=[True, False],
        defensive_pact=[False, True],
        force_peace=[True, False],
        war_weariness=[0, 17],
        espionage_points_against_team=[3, 29],
    )
    team = Team.from_struct(raw)

    assert (team.idx, team.num_members, team.alive_count, team.ever_alive_count) == (
        7,
        2,
        1,
        2,
    )
    assert (team.num_cities, team.population, team.land) == (3, 42, 85)
    assert (team.nuke_interception, team.vassal_power, team.master_power) == (
        50,
        12,
        34,
    )
    assert team.capitulated
    assert team.techs == [e.TechType.TECH_MYSTICISM, e.TechType(tech_count - 1)]
    assert team.no_trade_techs == [e.TechType(tech_count - 1)]
    assert team.research_progress[e.TechType.TECH_MYSTICISM] == 123
    assert team.research_progress[e.TechType(tech_count - 1)] == 0
    assert len(team.research_progress) == tech_count
    assert team.projects[e.ProjectType(0)] == 2
    assert team.projects[e.ProjectType(project_count - 1)] == 0
    assert len(team.projects) == project_count
    assert team.relations == {
        0: TeamRelation(False, False, True, False, True, 0, 3),
        1: TeamRelation(True, True, False, True, False, 17, 29),
    }

    # Public models own their collections rather than sharing the parser's lists.
    raw.has_tech[0] = False
    raw.research_progress[0] = 999
    raw.war_weariness[1] = 999
    assert team.techs[0] == e.TechType.TECH_MYSTICISM
    assert team.research_progress[e.TechType.TECH_MYSTICISM] == 123
    assert team.relations[1].war_weariness == 17


@pytest.mark.parametrize(
    "filename",
    [
        "bismark-emperor-turn86.CivBeyondSwordSave",
        "churchill-random-roll.CivBeyondSwordSave",
        "mehmed-epic.CivBeyondSwordSave",
        "Gandhi-culture-win-t331.CivBeyondSwordSave",
    ],
)
def test_save_teams(filename):
    save = SaveFile(Path(__file__).parent / "saves" / filename)
    teams = save.teams

    assert save.teams is teams
    assert set(teams) == set(range(19))
    assert any(team.alive_count == 0 for team in teams.values())
    assert sum(team.population for team in teams.values()) == save.raw.total_population
    assert sum(team.num_cities for team in teams.values()) == save.raw.total_cities
    for idx, team in teams.items():
        assert team.idx == idx
        assert set(team.relations) == set(teams)
        assert all(isinstance(tech, e.TechType) for tech in team.techs)
    for player in save.players.values():
        assert teams[player.team].idx == player.team
