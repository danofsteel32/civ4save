"""Typed team state and relationships between teams."""

from __future__ import annotations

from typing import Any

import attrs

from civ4save.vanilla import enums as e


@attrs.define(slots=True)
class TeamRelation:
    """A team's relationship with another team, keyed by the other team's ID."""

    has_met: bool
    at_war: bool
    open_borders: bool
    defensive_pact: bool
    force_peace: bool
    war_weariness: int
    espionage_points: int

    @classmethod
    def from_struct(cls, data: Any, other_team: int) -> TeamRelation:
        """Read the relationship from the source team's per-team arrays."""
        return cls(
            has_met=data.has_met[other_team],
            at_war=data.at_war[other_team],
            open_borders=data.open_borders[other_team],
            defensive_pact=data.defensive_pact[other_team],
            force_peace=data.force_peace[other_team],
            war_weariness=data.war_weariness[other_team],
            espionage_points=data.espionage_points_against_team[other_team],
        )


@attrs.define(slots=True)
class Team:
    """Current serialized team state, including inactive and barbarian teams.

    Technology lists use enum order. Research and project mappings include zero
    values. Relations are directional and include every team slot, including self.
    """

    idx: int
    num_members: int
    alive_count: int
    ever_alive_count: int
    num_cities: int
    population: int
    land: int
    nuke_interception: int
    vassal_power: int
    master_power: int
    capitulated: bool
    techs: list[e.TechType]
    no_trade_techs: list[e.TechType]
    research_progress: dict[e.TechType, int]
    projects: dict[e.ProjectType, int]
    relations: dict[int, TeamRelation]

    @classmethod
    def from_struct(cls, data: Any) -> Team:
        """Create a team from a parsed CvTeam or CvTeamAI record."""
        return cls(
            idx=data.id,
            num_members=data.num_members,
            alive_count=data.alive_count,
            ever_alive_count=data.ever_alive_count,
            num_cities=data.num_cities,
            population=data.total_population,
            land=data.total_land,
            nuke_interception=data.nuke_interception,
            vassal_power=data.vassal_power,
            master_power=data.master_power,
            capitulated=data.capitulated,
            techs=[e.TechType(i) for i, known in enumerate(data.has_tech) if known],
            no_trade_techs=[
                e.TechType(i) for i, blocked in enumerate(data.no_trade_tech) if blocked
            ],
            research_progress={
                e.TechType(i): progress
                for i, progress in enumerate(data.research_progress)
            },
            projects={
                e.ProjectType(i): count for i, count in enumerate(data.project_count)
            },
            relations={
                i: TeamRelation.from_struct(data, i) for i in range(len(data.has_met))
            },
        )
