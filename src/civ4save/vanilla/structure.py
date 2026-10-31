"""Little-endian Construct schemas for vanilla Beyond the Sword saves.

Named SDK sections can be parsed independently. The root schema flattens their
fields for SaveFile.raw, including teams, players, and their owned records.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from enum import EnumMeta
from typing import Any

from construct import (
    Adapter,
    Array,
    Bytes,
    Check,
    Computed,
    Const,
    ConstructError,
    Enum,
    ExprValidator,
    Flag,
    If,
    IfThenElse,
    Int8sl,
    Int8ul,
    Int16sl,
    Int16ul,
    Int32sl,
    Int32ul,
    PaddedString,
    Padding,
    Pass,
    Struct,
    Subconstruct,
    Switch,
    Tell,
    Terminated,
    ValidationError,
    this,
)
from construct.core import stream_size

from civ4save.utils import get_enum_length

from . import enums as e

MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", "19"))
MAX_TEAMS = MAX_PLAYERS
NUM_YIELD_TYPES = 3
NUM_COMMERCE_TYPES = 4
NUM_DOMAIN_TYPES = 4
NUM_CITY_PLOTS = 21
NUM_FEAT_TYPES = 31
NUM_CONTACT_TYPES = 14
MAX_TRADE_ROUTES = 8

# Type Aliases
INT = Int32sl
UINT = Int32ul
SHORT = Int16sl
USHORT = Int16ul
CHAR = Int8sl
UCHAR = Int8ul
COUNT = ExprValidator(INT, lambda count, ctx: count >= 0)
BYTE_COUNT = ExprValidator(CHAR, lambda count, ctx: count >= 0)

# Windows wide strings count UTF-16 code units; narrow strings count bytes.
WSTRING = Struct("_sz" / COUNT, "string" / PaddedString(this._sz * 2, "utf_16_le"))
STRING = Struct("_sz" / COUNT, "string" / PaddedString(this._sz, "utf_8"))
# corresponds to IDInfo struct
IDINFO = Struct("owner" / INT, "i_id" / INT)
# len prefixed arrays of various types
CHAR_INT_ARRAY = Struct("_sz" / BYTE_COUNT, "arr" / INT[this._sz])
CHAR_SHORT_ARRAY = Struct("_sz" / BYTE_COUNT, "arr" / SHORT[this._sz])
CHAR_CHAR_ARRAY = Struct("_sz" / BYTE_COUNT, "arr" / CHAR[this._sz])
CHAR_FLAG_ARRAY = Struct("_sz" / BYTE_COUNT, "arr" / Flag[this._sz])
INT_SHORT_ARRAY = Struct("_sz" / COUNT, "arr" / SHORT[this._sz])


class StringAdapter(Adapter):
    """Just want the actual string don't care about _sz."""

    def _decode(self, obj: Any, *args: Any) -> str:
        return obj.string


class StringArrayAdapter(Adapter):
    """Expose a sequence of string records as Python strings."""

    def _decode(self, obj: Iterable, *args: Any) -> list[str]:
        return [s.string for s in obj]


class WStringArrayAdapter(StringArrayAdapter):
    """Compatibility name for arrays of wide-string records."""


class EnumArrayAdapter(Adapter):
    """Make Enum arrays more useful.

    Used when an array is of len(Enum) and each element of the array is a value
    member of the Enum.
    """

    def __init__(self, _enum: EnumMeta, *args: Any, **kwargs: Any):
        """Needs the _enum arg in order to cast to correct type."""
        self._enum = _enum
        super().__init__(*args, **kwargs)

    def _decode(self, obj: Iterable, *args: Any) -> dict:
        return {self._enum(n): val for n, val in enumerate(obj)}

    def _encode(self, obj: dict, *args: Any) -> list[int]:
        # TODO: ensure sorted by enum value writing same order as read
        return [v for k, v in list(obj.items())]


class BoundedCountAdapter(Adapter):
    """Reject counts outside the supported vanilla BTS range."""

    def __init__(
        self, subcon: Any, maximum: int, field_name: str, *args: Any, **kwargs: Any
    ):
        self.maximum = maximum
        self.field_name = field_name
        super().__init__(subcon, *args, **kwargs)

    def _validate(self, obj: int) -> int:
        if not 0 <= obj <= self.maximum:
            raise ValidationError(
                f"{self.field_name} count {obj} is outside the vanilla range "
                f"0..{self.maximum}"
            )
        return obj

    def _decode(self, obj: int, *args: Any) -> int:
        return self._validate(obj)

    def _encode(self, obj: int, *args: Any) -> int:
        return self._validate(obj)


class DealsAdapter(Adapter):
    """The traded item could be a BonusType or TradeableItem."""

    def _decode(self, obj: Iterable, *args: Any) -> list:
        def _process_trades(trades: list[Any]) -> list[dict]:
            player_trades = []
            for trade in trades:
                amount = 1
                item: e.BonusType | e.TradeableItem = e.TradeableItem[trade.item]
                if item.name in {"TRADE_GOLD", "TRADE_GOLD_PER_TURN"}:
                    amount = trade.extra_data
                elif item.name == "TRADE_RESOURCES":
                    item = e.BonusType(trade.extra_data)
                player_trades.append({"item": item, "amount": amount})
            return player_trades

        deals = []
        for deal in obj:
            trade_deal = {
                "first_player": deal.first_player,
                "second_player": deal.second_player,
                "initial_game_turn": deal.initial_game_turn,
                "first_trades": _process_trades(deal.first_trades),
                "second_trades": _process_trades(deal.second_trades),
            }
            deals.append(trade_deal)
        return deals


CvPlot = Struct(
    "_plot_start_index" / Tell,
    "plot_flag" / UINT,
    "x" / SHORT,
    "y" / SHORT,
    "area_id" / INT,
    "feature_variety" / SHORT,
    "ownership_duration" / SHORT,
    "improvement_duration" / SHORT,
    "upgrade_progress" / SHORT,
    "force_unowned_timer" / SHORT,
    "city_radius_count" / SHORT,
    "river_id" / INT,
    "min_original_start_distance" / SHORT,
    "recon_count" / SHORT,
    "river_crossing_count" / SHORT,
    "starting_plot" / Flag,
    "hills" / Flag,
    "north_of_river" / Flag,
    "west_of_river" / Flag,
    "irrigated" / Flag,
    "potential_city_work" / Flag,
    "owner" / CHAR,
    "plot_type" / Enum(SHORT, e.PlotType),
    "terrain_type" / Enum(SHORT, e.TerrainType),
    "feature_type" / Enum(SHORT, e.FeatureType),
    "bonus_type" / Enum(SHORT, e.BonusType),
    "improvement_type" / Enum(SHORT, e.ImprovementType),
    "route_type" / SHORT,
    "river_north_south" / CHAR,
    "river_east_west" / CHAR,
    "plot_city_owner" / INT,
    "plot_city_id" / INT,
    "working_city_owner" / INT,
    "working_city_id" / INT,
    "working_city_override_owner" / INT,
    "working_city_override_id" / INT,
    "yields" / SHORT[NUM_YIELD_TYPES],
    "culture" / CHAR_INT_ARRAY,
    "found_value" / CHAR_SHORT_ARRAY,
    "player_city_radius" / CHAR_CHAR_ARRAY,
    "plot_group" / CHAR_INT_ARRAY,
    "visibility" / CHAR_SHORT_ARRAY,
    "stolen_visibility" / CHAR_SHORT_ARRAY,
    "blockaded" / CHAR_SHORT_ARRAY,
    "revealed_owner" / CHAR_CHAR_ARRAY,
    "river_crossings" / CHAR_FLAG_ARRAY,
    "revealed" / CHAR_FLAG_ARRAY,
    "revealed_improvement_type" / CHAR_SHORT_ARRAY,
    "revealed_route_type" / CHAR_SHORT_ARRAY,
    "plot_script_data" / StringAdapter(STRING),
    "build_progress" / INT_SHORT_ARRAY,
    "_sz_culture_range_cities"
    / BoundedCountAdapter(CHAR, MAX_PLAYERS, "culture range cities"),
    "culture_range_cities"
    / IfThenElse(
        this._sz_culture_range_cities > 0,
        Array(
            this._sz_culture_range_cities,
            Struct("_sz_crc" / COUNT, "arr" / Array(this._sz_crc, CHAR)),
        ),
        Pass,
    ),
    "_sz_invisible_visibility"
    / BoundedCountAdapter(CHAR, MAX_TEAMS, "invisible visibility"),
    "invisible_visibles"
    / IfThenElse(
        this._sz_invisible_visibility > 0,
        Array(
            this._sz_invisible_visibility,
            Struct("_sz_iv" / COUNT, "arr" / Array(this._sz_iv, SHORT)),
        ),
        Pass,
    ),
    "_sz_units" / COUNT,
    "units" / Array(this._sz_units, IDINFO),
    "_plot_end_index" / Tell,
    "plot_sizeof" / Computed(this._plot_end_index - this._plot_start_index),
)


class PlotRecord(Subconstruct):
    """Add map coordinates and the record offset to plot parse failures."""

    def _parse(self, stream: Any, context: Any, path: str) -> Any:
        offset = stream.tell()
        index = context._index
        x, y = index % context.grid_width, index // context.grid_width
        try:
            return self.subcon._parsereport(stream, context, path)
        except ConstructError as exc:
            raise ConstructError(
                f"plot ({x}, {y}) at byte {offset}: {exc}", path=path
            ) from exc


# used multiple times in deals struct
TradeData = Struct(
    "item" / Enum(INT, e.TradeableItem),
    "extra_data" / INT,  # could be BonusType or amount of gold/turn
    "offering" / Flag,
    "hidden" / Flag,
    Padding(2),  # TradeData's two adjacent bools precede struct tail padding.
)

# used in vote_selections and votes_triggered structs
VoteOption = Struct(
    "type" / Enum(INT, e.VoteType),
    "player" / INT,
    "city_id" / INT,
    "other_player" / INT,
    "text" / StringAdapter(WSTRING),
)

# CvArea::read/write and ReadStreamableFFreeListTrashArray in the BTS SDK.
CvArea = Struct(
    "_area_start_index" / Tell,
    "_area_flag" / UINT,
    "area_id" / INT,
    "num_tiles" / INT,
    "num_owned_tiles" / INT,
    "num_river_edges" / INT,
    "num_units" / INT,
    "num_cities" / INT,
    "total_population" / INT,
    "num_starting_plots" / INT,
    "water" / Flag,
    "units_per_player" / INT[MAX_PLAYERS],
    "animals_per_player" / INT[MAX_PLAYERS],
    "cities_per_player" / INT[MAX_PLAYERS],
    "pop_per_player" / INT[MAX_PLAYERS],
    "building_good_health_per_player" / INT[MAX_PLAYERS],
    "building_bad_health_per_player" / INT[MAX_PLAYERS],
    "building_happiness_per_player" / INT[MAX_PLAYERS],
    "free_specialist_per_player" / INT[MAX_PLAYERS],
    "power" / INT[MAX_PLAYERS],
    "best_found_value" / INT[MAX_PLAYERS],
    "num_revealed_tiles" / INT[MAX_TEAMS],
    "clean_power_count" / INT[MAX_TEAMS],
    "border_obstacle_count" / INT[MAX_TEAMS],
    "area_ai_type" / Array(MAX_TEAMS, Enum(INT, e.AreaAIType)),
    "target_cities" / Array(MAX_PLAYERS, IDINFO),
    "yield_rate_modifiers" / Array(MAX_PLAYERS, INT[NUM_YIELD_TYPES]),
    "num_train_ai_units" / Array(MAX_PLAYERS, INT[get_enum_length(e.UnitAIType)]),
    "num_ai_units" / Array(MAX_PLAYERS, INT[get_enum_length(e.UnitAIType)]),
    "num_bonuses" / EnumArrayAdapter(e.BonusType, INT[get_enum_length(e.BonusType)]),
    "num_improvements"
    / EnumArrayAdapter(e.ImprovementType, INT[get_enum_length(e.ImprovementType)]),
    "_area_end_index" / Tell,
)


def _free_list_header(prefix: str, count_name: str) -> Any:
    """SDK streamable free-list metadata, followed by the active record count."""
    slots_name = f"_{prefix}_num_slots"
    return Struct(
        # FFreeListTrashArray.h: FLTA_MAX_BUCKETS = 1 << 13.
        slots_name / BoundedCountAdapter(INT, 8192, f"{prefix} slots"),
        f"_{prefix}_last_index" / INT,
        f"_{prefix}_free_list_head" / INT,
        f"_{prefix}_free_list_count" / INT,
        f"_{prefix}_current_id" / INT,
        f"_{prefix}_next_free_index_array" / INT[this[slots_name]],
        count_name
        / ExprValidator(INT, lambda count, ctx: 0 <= count <= ctx[slots_name]),
    )


CvAreaList = Struct(
    *_free_list_header("areas", "sz_areas").subcons,
    "areas" / Array(this.sz_areas, CvArea),
    "_areas_end_index" / Tell,
)

CvDeal = Struct(
    "_flag" / UINT,
    "id" / INT,
    "initial_game_turn" / INT,
    "first_player" / INT,
    "second_player" / INT,
    "_sz_first_trades" / COUNT,
    "first_trades" / Array(this._sz_first_trades, TradeData),
    "_sz_second_trades" / COUNT,
    "second_trades" / Array(this._sz_second_trades, TradeData),
)

VoteSelection = Struct(
    "vote_id" / INT,
    "vote_source" / Enum(INT, e.VoteSourceType),
    "_sz_vote_options" / COUNT,
    "vote_options" / Array(this._sz_vote_options, VoteOption),
)

VoteTriggered = Struct(
    "vote_id" / INT,
    "vote_source" / Enum(INT, e.VoteSourceType),
    "vote_option" / VoteOption,
)

CvReplayMessage = Struct(
    "turn" / INT,
    "type" / Enum(INT, e.ReplayMessageType),
    "plot_x" / INT,
    "plot_y" / INT,
    "player" / INT,
    "text" / StringAdapter(WSTRING),
    "e_color" / Enum(INT, e.ColorValsType),
)

PlotExtraYield = Struct(
    "plot_x" / INT,
    "plot_y" / INT,
    "extra_yields" / INT[NUM_YIELD_TYPES],
)

PlotExtraCost = Struct(
    "plot_x" / INT,
    "plot_y" / INT,
    "extra_costs" / INT,
)

VoteSourceReligion = Struct(
    "vote_source" / Enum(INT, e.VoteSourceType),
    "religion" / Enum(INT, e.ReligionType),
)

CvDealList = Struct(
    *_free_list_header("deals", "_sz_deals").subcons,
    "deals" / DealsAdapter(Array(this._sz_deals, CvDeal)),
)

VoteSelectionList = Struct(
    *_free_list_header("vote_selections", "_sz_vote_selections").subcons,
    "vote_selections" / Array(this._sz_vote_selections, VoteSelection),
)

VoteTriggeredList = Struct(
    *_free_list_header("votes_triggered", "_sz_votes_triggered").subcons,
    "votes_triggered" / Array(this._sz_votes_triggered, VoteTriggered),
)

SaveHeader = Struct(
    "_header_start_index" / Tell,
    "version" / INT,
    "_save_bits" / Array(8, INT),
    "_bytes_to_zlib_magic_number" / INT,
    "_header_end_index" / Tell,
)

CvInitCore = Struct(
    "_init_core_start_index" / Tell,
    "save_flag" / INT,
    "game_type" / Enum(INT, e.GameType),
    "game_name" / StringAdapter(WSTRING),
    "game_password" / StringAdapter(WSTRING),
    "admin_password" / StringAdapter(WSTRING),
    "map_script_name" / StringAdapter(WSTRING),
    "wb_map_no_players" / Flag,
    "world_size" / Enum(INT, e.WorldType),
    "climate" / Enum(INT, e.ClimateType),
    "sea_level" / Enum(INT, e.SeaLevelType),
    "start_era" / Enum(INT, e.EraType),
    "game_speed" / Enum(INT, e.GameSpeedType),
    "turn_timer" / Enum(INT, e.TurnTimerType),
    "calendar" / Enum(INT, e.CalendarType),
    "num_custom_map_options" / COUNT,
    "num_hidden_custom_map_options" / COUNT,
    "custom_map_options" / INT[this.num_custom_map_options],
    "_sz_victories" / COUNT,
    "victories" / EnumArrayAdapter(e.VictoryType, Flag[this._sz_victories]),
    "game_options"
    / EnumArrayAdapter(e.GameOptionType, Flag[get_enum_length(e.GameOptionType)]),
    "mp_game_options"
    / EnumArrayAdapter(
        e.MultiplayerOptionType, Flag[get_enum_length(e.MultiplayerOptionType)]
    ),
    "stat_reporting" / Flag,
    "game_turn" / INT,
    "max_turns" / INT,
    "pitboss_turn_time" / INT,
    "target_score" / INT,
    "max_city_eliminations" / INT,
    "advanced_start_points" / INT,
    "leader_names" / WStringArrayAdapter(WSTRING[MAX_PLAYERS]),
    "civ_descriptions" / WStringArrayAdapter(WSTRING[MAX_PLAYERS]),
    "civ_short_descriptions" / WStringArrayAdapter(WSTRING[MAX_PLAYERS]),
    "civ_adjectives" / WStringArrayAdapter(WSTRING[MAX_PLAYERS]),
    "civ_passwords" / WStringArrayAdapter(WSTRING[MAX_PLAYERS]),
    "emails" / StringArrayAdapter(STRING[MAX_PLAYERS]),
    "smtp_hosts" / StringArrayAdapter(STRING[MAX_PLAYERS]),
    "white_flags" / Flag[MAX_PLAYERS],
    "flag_decals" / WStringArrayAdapter(WSTRING[MAX_PLAYERS]),
    "civs" / Array(MAX_PLAYERS, Enum(INT, e.CivilizationType)),
    "leaders" / Array(MAX_PLAYERS, Enum(INT, e.LeaderHeadType)),
    "teams" / INT[MAX_PLAYERS],
    "handicaps" / Array(MAX_PLAYERS, Enum(INT, e.HandicapType)),
    "colors" / Array(MAX_PLAYERS, Enum(INT, e.PlayerColorType)),
    "art_style" / Array(MAX_PLAYERS, Enum(INT, e.UnitArtStyleType)),  # Wrong type
    "slot_statuses" / INT[MAX_PLAYERS],
    "slot_claims" / INT[MAX_PLAYERS],
    "playable_civs" / Flag[MAX_PLAYERS],
    "minor_nation_civs" / Flag[MAX_PLAYERS],
    "_init_core_end_index" / Tell,
)

# These framing words remain in the decompressed stream returned by SaveFile.
CompressedSectionHeader = Struct(
    "_compressed_section_start_index" / Tell,
    "_compression_flag" / UINT,
    "_first_chunk_size" / UINT,
    "_compressed_section_end_index" / Tell,
)

CvGame = Struct(
    "_game_start_index" / Tell,
    "_game_flag" / UINT,
    "elapsed_game_turns" / INT,
    "start_turn" / INT,
    "start_year" / INT,
    "estimated_end_turn" / INT,
    "turn_slice" / INT,
    "cutoff_slice" / INT,
    "num_game_turn_active" / INT,
    "total_cities" / INT,
    "total_population" / INT,
    "trade_routes" / INT,
    "free_trade_count" / INT,
    "no_nukes_count" / INT,
    "nukes_exploded" / INT,
    "max_population" / INT,
    "max_land" / INT,
    "max_tech" / INT,
    "max_wonders" / INT,
    "init_population" / INT,
    "init_land" / INT,
    "init_tech" / INT,
    "init_wonders" / INT,
    "ai_autoplay" / INT,
    "score_dirty" / Flag,
    "circumnavigated" / Flag,
    "final_initialized" / Flag,
    "hot_pbem_between_turns" / Flag,
    "nukes_valid" / Flag,
    "handicap" / Enum(INT, e.HandicapType),
    "pause_player" / INT,  # -1 = NO_PLAYER, otherwise is index of players array
    "best_land_unit" / Enum(INT, e.UnitType),
    "winner" / INT,  # -1 = NO_TEAM, otherwise is index of teams array
    "victory" / Enum(INT, e.VictoryType),
    "game_state" / Enum(INT, e.GameStateType),
    "script_data" / STRING,
    "ai_rank_player" / INT[MAX_PLAYERS],
    "ai_player_rank" / INT[MAX_PLAYERS],
    "ai_player_score" / INT[MAX_PLAYERS],
    "ai_rank_team" / INT[MAX_TEAMS],
    "ai_team_rank" / INT[MAX_TEAMS],
    "ai_team_score" / INT[MAX_TEAMS],
    "unit_created_counts"
    / EnumArrayAdapter(e.UnitType, INT[get_enum_length(e.UnitType)]),
    "unit_class_created_counts"
    / EnumArrayAdapter(e.UnitClassType, INT[get_enum_length(e.UnitClassType)]),
    "building_class_created_counts"
    / EnumArrayAdapter(e.BuildingClassType, INT[get_enum_length(e.BuildingClassType)]),
    "project_created_counts"
    / EnumArrayAdapter(e.ProjectType, INT[get_enum_length(e.ProjectType)]),
    "force_civic_counts"
    / EnumArrayAdapter(e.CivicType, INT[get_enum_length(e.CivicType)]),
    "vote_outcomes" / EnumArrayAdapter(e.VoteType, INT[get_enum_length(e.VoteType)]),
    "religion_game_turn_founded"
    / EnumArrayAdapter(e.ReligionType, INT[get_enum_length(e.ReligionType)]),
    "corporation_game_turn_founded"
    / EnumArrayAdapter(e.CorporationType, INT[get_enum_length(e.CorporationType)]),
    "secretary_general_timer"
    / EnumArrayAdapter(e.VoteSourceType, INT[get_enum_length(e.VoteSourceType)]),
    "vote_timer"
    / EnumArrayAdapter(e.VoteSourceType, INT[get_enum_length(e.VoteSourceType)]),
    "diplo_vote"
    / EnumArrayAdapter(e.VoteSourceType, INT[get_enum_length(e.VoteSourceType)]),
    "special_unit_valid" / Flag[get_enum_length(e.SpecialUnitType)],
    "special_building_valid" / Flag[get_enum_length(e.SpecialBuildingType)],
    "religion_slot_taken"
    / EnumArrayAdapter(e.ReligionType, Flag[get_enum_length(e.ReligionType)]),
    "holy_cities" / Array(get_enum_length(e.ReligionType), IDINFO),
    "corporation_headquarters" / Array(get_enum_length(e.CorporationType), IDINFO),
    "_sz_cities_destroyed" / COUNT,
    "cities_destroyed" / WStringArrayAdapter(WSTRING[this._sz_cities_destroyed]),
    "_sz_gp_born" / COUNT,
    "great_people_born" / WStringArrayAdapter(WSTRING[this._sz_gp_born]),
    *CvDealList.subcons,
    *VoteSelectionList.subcons,
    *VoteTriggeredList.subcons,
    "map_random_seed" / UINT,
    "soren_random_seed" / UINT,
    "_sz_replay_messages" / COUNT,
    "replay_messages" / Array(this._sz_replay_messages, CvReplayMessage),
    "num_sessions" / INT,
    "_sz_plot_extra_yields" / COUNT,
    "plot_extra_yields" / Array(this._sz_plot_extra_yields, PlotExtraYield),
    "_sz_plot_extra_costs" / COUNT,
    "plot_extra_costs" / Array(this._sz_plot_extra_costs, PlotExtraCost),
    "_sz_vote_source_religions" / COUNT,
    "vote_source_religions" / Array(this._sz_vote_source_religions, VoteSourceReligion),
    "_sz_inactive_triggers" / COUNT,
    "inactive_triggers"
    / Array(
        this._sz_inactive_triggers,
        Enum(INT, e.EventTriggerType),
    ),
    "shrine_building_count" / INT,
    "shrine_buildings"
    / Array(
        get_enum_length(e.BuildingType),
        Enum(INT, e.BuildingType),
    ),
    "shrine_religion"
    / Array(
        get_enum_length(e.BuildingType),
        Enum(INT, e.ReligionType),
    ),
    "num_culture_victory_cities" / INT,
    "culture_victory_level" / Enum(INT, e.CultureLevelType),
    "_game_end_index" / Tell,
)

CvGameAI = Struct(
    *CvGame.subcons,
    "_game_ai_flag" / UINT,
    "_game_ai_pad" / INT,
    "_game_ai_end_index" / Tell,
)

CvMap = Struct(
    "_map_start_index" / Tell,
    "_map_flag" / UINT,
    "grid_width" / COUNT,
    "grid_height" / COUNT,
    "land_plots" / INT,
    "owned_plots" / INT,
    "top_latitude" / INT,
    "bottom_latitude" / INT,
    "next_river_id" / INT,
    "wrap_x" / Flag,
    "wrap_y" / Flag,
    "bonus_counts" / EnumArrayAdapter(e.BonusType, INT[get_enum_length(e.BonusType)]),
    "bonus_counts_on_land"
    / EnumArrayAdapter(e.BonusType, INT[get_enum_length(e.BonusType)]),
    "plots" / Array(this.grid_width * this.grid_height, PlotRecord(CvPlot)),
    # CvMap's streamable area free list; retain the existing flat raw fields.
    *CvAreaList.subcons,
    "_map_end_index" / Tell,
)


class IndexedRecord(Subconstruct):
    """Identify the record index and starting byte when a nested parse fails."""

    def __init__(self, subcon: Any, label: str) -> None:
        super().__init__(subcon)
        self.label = label

    def _parse(self, stream: Any, context: Any, path: str) -> Any:
        offset = stream.tell()
        try:
            return self.subcon._parsereport(stream, context, path)
        except ConstructError as exc:
            raise ConstructError(
                f"{self.label} {context._index} at byte {offset}: {exc}", path=path
            ) from exc


# CvTeam/CvPlayer and owned records, transcribed from the pinned BTS SDK.
# All arrays are eager; counts must never silently truncate a record.
CvTeam = Struct(
    "_team_start_index" / Tell,
    "_team_flag" / UINT,
    "num_members" / INT,
    "alive_count" / INT,
    "ever_alive_count" / INT,
    "num_cities" / INT,
    "total_population" / INT,
    "total_land" / INT,
    "nuke_interception" / INT,
    "extra_water_see_from_count" / INT,
    "map_trading_count" / INT,
    "tech_trading_count" / INT,
    "gold_trading_count" / INT,
    "open_borders_trading_count" / INT,
    "defensive_pact_trading_count" / INT,
    "permanent_alliance_trading_count" / INT,
    "vassal_trading_count" / INT,
    "bridge_building_count" / INT,
    "irrigation_count" / INT,
    "ignore_irrigation_count" / INT,
    "water_work_count" / INT,
    "vassal_power" / INT,
    "master_power" / INT,
    "enemy_war_weariness_modifier" / INT,
    "river_trade_count" / INT,
    "espionage_points_ever" / INT,
    "map_centering" / Flag,
    "capitulated" / Flag,
    "id" / INT,
    "stolen_visibility_timer" / Array(MAX_TEAMS, INT),
    "war_weariness" / Array(MAX_TEAMS, INT),
    "tech_share_count" / Array(MAX_TEAMS, INT),
    "espionage_points_against_team" / Array(MAX_TEAMS, INT),
    "counterespionage_turns_left_against_team" / Array(MAX_TEAMS, INT),
    "counterespionage_mod_against_team" / Array(MAX_TEAMS, INT),
    "commerce_flexible_count" / Array(NUM_COMMERCE_TYPES, INT),
    "extra_moves" / Array(NUM_DOMAIN_TYPES, INT),
    "force_team_vote_eligibility_count" / Array(get_enum_length(e.VoteSourceType), INT),
    "has_met" / Array(MAX_TEAMS, Flag),
    "at_war" / Array(MAX_TEAMS, Flag),
    "permanent_war_peace" / Array(MAX_TEAMS, Flag),
    "open_borders" / Array(MAX_TEAMS, Flag),
    "defensive_pact" / Array(MAX_TEAMS, Flag),
    "force_peace" / Array(MAX_TEAMS, Flag),
    "vassal" / Array(MAX_TEAMS, Flag),
    "can_launch" / Array(get_enum_length(e.VictoryType), Flag),
    "route_change" / Array(get_enum_length(e.RouteType), INT),
    "project_count" / Array(get_enum_length(e.ProjectType), COUNT),
    "project_default_art_types" / Array(get_enum_length(e.ProjectType), INT),
    "project_art_types"
    / Array(
        get_enum_length(e.ProjectType),
        Array(lambda ctx: ctx.project_count[ctx._index], INT),
    ),
    "project_making" / Array(get_enum_length(e.ProjectType), INT),
    "unit_class_count" / Array(get_enum_length(e.UnitClassType), INT),
    "building_class_count" / Array(get_enum_length(e.BuildingClassType), INT),
    "obsolete_building_count" / Array(get_enum_length(e.BuildingType), INT),
    "research_progress" / Array(get_enum_length(e.TechType), INT),
    "tech_count" / Array(get_enum_length(e.TechType), INT),
    "terrain_trade_count" / Array(get_enum_length(e.TerrainType), INT),
    "victory_countdown" / Array(get_enum_length(e.VictoryType), INT),
    "has_tech" / Array(get_enum_length(e.TechType), Flag),
    "no_trade_tech" / Array(get_enum_length(e.TechType), Flag),
    "improvement_yield_change"
    / Array(get_enum_length(e.ImprovementType), INT[NUM_YIELD_TYPES]),
    "_sz_revealed_bonuses" / COUNT,
    "revealed_bonuses" / Array(this._sz_revealed_bonuses, Enum(INT, e.BonusType)),
    "_team_end_index" / Tell,
)

CvTeamAI = Struct(
    *CvTeam.subcons,
    "_team_ai_flag" / UINT,
    "war_plan_state_counter" / Array(MAX_TEAMS, INT),
    "at_war_counter" / Array(MAX_TEAMS, INT),
    "at_peace_counter" / Array(MAX_TEAMS, INT),
    "has_met_counter" / Array(MAX_TEAMS, INT),
    "open_borders_counter" / Array(MAX_TEAMS, INT),
    "defensive_pact_counter" / Array(MAX_TEAMS, INT),
    "share_war_counter" / Array(MAX_TEAMS, INT),
    "war_success" / Array(MAX_TEAMS, INT),
    "enemy_peacetime_trade_value" / Array(MAX_TEAMS, INT),
    "enemy_peacetime_grant_value" / Array(MAX_TEAMS, INT),
    "war_plan" / Array(MAX_TEAMS, INT),
    "worst_enemy" / INT,
    "_team_ai_end_index" / Tell,
)

CvPlotGroup = Struct(
    "_plot_group_start_index" / Tell,
    "_plot_group_flag" / UINT,
    "id" / INT,
    "owner" / INT,
    "num_bonuses" / Array(get_enum_length(e.BonusType), INT),
    "_sz_plots" / COUNT,
    "plots" / Array(this._sz_plots, Struct("x" / INT, "y" / INT)),
    "_plot_group_end_index" / Tell,
)

# CLinkList writes raw Windows structs, including OrderData's tail padding.
OrderData = Struct(
    "order_type" / INT, "data1" / INT, "data2" / INT, "save" / Flag, Padding(3)
)
MissionData = Struct(
    "mission_type" / INT, "data1" / INT, "data2" / INT, "flags" / INT, "push_turn" / INT
)
BuildingYieldChange = Struct("building_class" / INT, "yield_type" / INT, "change" / INT)
BuildingCommerceChange = Struct(
    "building_class" / INT, "commerce_type" / INT, "change" / INT
)
BuildingChange = Struct("building_class" / INT, "change" / INT)

CvCity = Struct(
    "_city_start_index" / Tell,
    "_city_flag" / UINT,
    "id" / INT,
    "x" / INT,
    "y" / INT,
    "rally_x" / INT,
    "rally_y" / INT,
    "game_turn_founded" / INT,
    "game_turn_acquired" / INT,
    "population" / INT,
    "highest_population" / INT,
    "working_population" / INT,
    "specialist_population" / INT,
    "num_great_people" / INT,
    "base_great_people_rate" / INT,
    "great_people_rate_modifier" / INT,
    "great_people_progress" / INT,
    "num_world_wonders" / INT,
    "num_team_wonders" / INT,
    "num_national_wonders" / INT,
    "num_buildings" / INT,
    "government_center_count" / INT,
    "maintenance" / INT,
    "maintenance_modifier" / INT,
    "war_weariness_modifier" / INT,
    "hurry_anger_modifier" / INT,
    "heal_rate" / INT,
    "espionage_health_counter" / INT,
    "espionage_happiness_counter" / INT,
    "fresh_water_good_health" / INT,
    "fresh_water_bad_health" / INT,
    "feature_good_health" / INT,
    "feature_bad_health" / INT,
    "building_good_health" / INT,
    "building_bad_health" / INT,
    "power_good_health" / INT,
    "power_bad_health" / INT,
    "bonus_good_health" / INT,
    "bonus_bad_health" / INT,
    "hurry_anger_timer" / INT,
    "conscript_anger_timer" / INT,
    "defy_resolution_anger_timer" / INT,
    "happiness_timer" / INT,
    "military_happiness_units" / INT,
    "building_good_happiness" / INT,
    "building_bad_happiness" / INT,
    "extra_building_good_happiness" / INT,
    "extra_building_bad_happiness" / INT,
    "extra_building_good_health" / INT,
    "extra_building_bad_health" / INT,
    "feature_good_happiness" / INT,
    "feature_bad_happiness" / INT,
    "bonus_good_happiness" / INT,
    "bonus_bad_happiness" / INT,
    "religion_good_happiness" / INT,
    "religion_bad_happiness" / INT,
    "extra_happiness" / INT,
    "extra_health" / INT,
    "no_unhappiness_count" / INT,
    "no_unhealthy_population_count" / INT,
    "building_only_healthy_count" / INT,
    "food" / INT,
    "food_kept" / INT,
    "max_food_kept_percent" / INT,
    "overflow_production" / INT,
    "feature_production" / INT,
    "military_production_modifier" / INT,
    "space_production_modifier" / INT,
    "extra_trade_routes" / INT,
    "trade_route_modifier" / INT,
    "foreign_trade_route_modifier" / INT,
    "building_defense" / INT,
    "building_bombard_defense" / INT,
    "free_experience" / INT,
    "curr_airlift" / INT,
    "max_airlift" / INT,
    "air_modifier" / INT,
    "air_unit_capacity" / INT,
    "nuke_modifier" / INT,
    "free_specialist" / INT,
    "power_count" / INT,
    "dirty_power_count" / INT,
    "defense_damage" / INT,
    "last_defense_damage" / INT,
    "occupation_timer" / INT,
    "culture_update_timer" / INT,
    "city_size_boost" / INT,
    "specialist_free_experience" / INT,
    "espionage_defense_modifier" / INT,
    "never_lost" / Flag,
    "bombarded" / Flag,
    "drafted" / Flag,
    "airlift_targeted" / Flag,
    "we_love_the_king_day" / Flag,
    "citizens_automated" / Flag,
    "production_automated" / Flag,
    "wall_override" / Flag,
    "plundered" / Flag,
    "owner" / INT,
    "previous_owner" / INT,
    "original_owner" / INT,
    "culture_level" / INT,
    "sea_plot_yield" / Array(NUM_YIELD_TYPES, INT),
    "river_plot_yield" / Array(NUM_YIELD_TYPES, INT),
    "base_yield_rate" / Array(NUM_YIELD_TYPES, INT),
    "yield_rate_modifier" / Array(NUM_YIELD_TYPES, INT),
    "power_yield_rate_modifier" / Array(NUM_YIELD_TYPES, INT),
    "bonus_yield_rate_modifier" / Array(NUM_YIELD_TYPES, INT),
    "trade_yield" / Array(NUM_YIELD_TYPES, INT),
    "corporation_yield" / Array(NUM_YIELD_TYPES, INT),
    "extra_specialist_yield" / Array(NUM_YIELD_TYPES, INT),
    "commerce_rate" / Array(NUM_COMMERCE_TYPES, INT),
    "production_to_commerce_modifier" / Array(NUM_COMMERCE_TYPES, INT),
    "building_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "specialist_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "religion_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "corporation_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_rate_modifier" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_happiness_per" / Array(NUM_COMMERCE_TYPES, INT),
    "domain_free_experience" / Array(NUM_DOMAIN_TYPES, INT),
    "domain_production_modifier" / Array(NUM_DOMAIN_TYPES, INT),
    "culture" / Array(MAX_PLAYERS, INT),
    "num_revolts" / Array(MAX_PLAYERS, INT),
    "ever_owned" / Array(MAX_PLAYERS, Flag),
    "trade_route" / Array(MAX_PLAYERS, Flag),
    "revealed" / Array(MAX_TEAMS, Flag),
    "espionage_visibility" / Array(MAX_TEAMS, Flag),
    "name" / StringAdapter(WSTRING),
    "script_data" / StringAdapter(STRING),
    "no_bonus" / Array(get_enum_length(e.BonusType), INT),
    "free_bonus" / Array(get_enum_length(e.BonusType), INT),
    "num_bonuses" / Array(get_enum_length(e.BonusType), INT),
    "num_corp_produced_bonuses" / Array(get_enum_length(e.BonusType), INT),
    "project_production" / Array(get_enum_length(e.ProjectType), INT),
    "building_production" / Array(get_enum_length(e.BuildingType), INT),
    "building_production_time" / Array(get_enum_length(e.BuildingType), INT),
    "building_original_owner" / Array(get_enum_length(e.BuildingType), INT),
    "building_original_time" / Array(get_enum_length(e.BuildingType), INT),
    "unit_production" / Array(get_enum_length(e.UnitType), INT),
    "unit_production_time" / Array(get_enum_length(e.UnitType), INT),
    "great_people_unit_rate" / Array(get_enum_length(e.UnitType), INT),
    "great_people_unit_progress" / Array(get_enum_length(e.UnitType), INT),
    "specialist_count" / Array(get_enum_length(e.SpecialistType), INT),
    "max_specialist_count" / Array(get_enum_length(e.SpecialistType), INT),
    "force_specialist_count" / Array(get_enum_length(e.SpecialistType), INT),
    "free_specialist_count" / Array(get_enum_length(e.SpecialistType), INT),
    "improvement_free_specialists" / Array(get_enum_length(e.ImprovementType), INT),
    "religion_influence" / Array(get_enum_length(e.ReligionType), INT),
    "state_religion_happiness" / Array(get_enum_length(e.ReligionType), INT),
    "unit_combat_free_experience" / Array(get_enum_length(e.UnitCombatType), INT),
    "free_promotion_count" / Array(get_enum_length(e.PromotionType), INT),
    "num_real_building" / Array(get_enum_length(e.BuildingType), INT),
    "num_free_building" / Array(get_enum_length(e.BuildingType), INT),
    "working_plot" / Array(NUM_CITY_PLOTS, Flag),
    "has_religion" / Array(get_enum_length(e.ReligionType), Flag),
    "has_corporation" / Array(get_enum_length(e.CorporationType), Flag),
    "trade_cities" / Array(MAX_TRADE_ROUTES, IDINFO),
    "_sz_order_queue" / COUNT,
    "order_queue" / Array(this._sz_order_queue, OrderData),
    "population_rank" / INT,
    "population_rank_valid" / Flag,
    "base_yield_rank" / Array(NUM_YIELD_TYPES, INT),
    "base_yield_rank_valid" / Array(NUM_YIELD_TYPES, Flag),
    "yield_rank" / Array(NUM_YIELD_TYPES, INT),
    "yield_rank_valid" / Array(NUM_YIELD_TYPES, Flag),
    "commerce_rank" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_rank_valid" / Array(NUM_COMMERCE_TYPES, Flag),
    "_sz_events_occurred" / COUNT,
    "events_occurred" / Array(this._sz_events_occurred, Enum(INT, e.EventType)),
    "_sz_building_yield_change" / COUNT,
    "building_yield_change"
    / Array(this._sz_building_yield_change, BuildingYieldChange),
    "_sz_building_commerce_change" / COUNT,
    "building_commerce_change"
    / Array(this._sz_building_commerce_change, BuildingCommerceChange),
    "_sz_building_happy_change" / COUNT,
    "building_happy_change" / Array(this._sz_building_happy_change, BuildingChange),
    "_sz_building_health_change" / COUNT,
    "building_health_change" / Array(this._sz_building_health_change, BuildingChange),
    "_city_end_index" / Tell,
)

CvCityAI = Struct(
    *CvCity.subcons,
    "_city_ai_flag" / UINT,
    "emphasize_avoid_growth_count" / INT,
    "emphasize_great_people_count" / INT,
    "assign_work_dirty" / Flag,
    "choose_production_dirty" / Flag,
    "route_to_city_owner" / INT,
    "route_to_city_id" / INT,
    "emphasize_yield_count" / Array(NUM_YIELD_TYPES, INT),
    "emphasize_commerce_count" / Array(NUM_COMMERCE_TYPES, INT),
    "force_emphasize_culture" / Flag,
    "best_build_value" / Array(NUM_CITY_PLOTS, INT),
    "best_build" / Array(NUM_CITY_PLOTS, INT),
    "emphasize" / Array(get_enum_length(e.EmphasizeType), Flag),
    "special_yield_multiplier" / Array(NUM_YIELD_TYPES, INT),
    "cache_player_closeness_turn" / INT,
    "cache_player_closeness_distance" / INT,
    "player_closeness" / Array(MAX_PLAYERS, INT),
    "needed_floating_defenders" / INT,
    "needed_floating_defenders_cache_turn" / INT,
    "workers_needed" / INT,
    "workers_have" / INT,
    "_city_ai_end_index" / Tell,
)

CvUnit = Struct(
    "_unit_start_index" / Tell,
    "_unit_flag" / UINT,
    "id" / INT,
    "group_id" / INT,
    "hot_key_number" / INT,
    "x" / INT,
    "y" / INT,
    "last_move_turn" / INT,
    "recon_x" / INT,
    "recon_y" / INT,
    "game_turn_created" / INT,
    "damage" / INT,
    "moves" / INT,
    "experience" / INT,
    "level" / INT,
    "cargo" / INT,
    "cargo_capacity" / INT,
    "attack_plot_x" / INT,
    "attack_plot_y" / INT,
    "combat_timer" / INT,
    "combat_first_strikes" / INT,
    "combat_damage" / If(this._unit_flag < 2, INT),
    "fortify_turns" / INT,
    "blitz_count" / INT,
    "amphib_count" / INT,
    "river_count" / INT,
    "enemy_route_count" / INT,
    "always_heal_count" / INT,
    "hills_double_move_count" / INT,
    "immune_to_first_strikes_count" / INT,
    "extra_visibility_range" / INT,
    "extra_moves" / INT,
    "extra_move_discount" / INT,
    "extra_air_range" / INT,
    "extra_intercept" / INT,
    "extra_evasion" / INT,
    "extra_first_strikes" / INT,
    "extra_chance_first_strikes" / INT,
    "extra_withdrawal" / INT,
    "extra_collateral_damage" / INT,
    "extra_bombard_rate" / INT,
    "extra_enemy_heal" / INT,
    "extra_neutral_heal" / INT,
    "extra_friendly_heal" / INT,
    "same_tile_heal" / INT,
    "adjacent_tile_heal" / INT,
    "extra_combat_percent" / INT,
    "extra_city_attack_percent" / INT,
    "extra_city_defense_percent" / INT,
    "extra_hills_attack_percent" / INT,
    "extra_hills_defense_percent" / INT,
    "revolt_protection" / INT,
    "collateral_damage_protection" / INT,
    "pillage_change" / INT,
    "upgrade_discount" / INT,
    "experience_percent" / INT,
    "kamikaze_percent" / INT,
    "base_combat" / INT,
    "facing_direction" / INT,
    "immobile_timer" / INT,
    "made_attack" / Flag,
    "made_interception" / Flag,
    "promotion_ready" / Flag,
    "death_delay" / Flag,
    "combat_focus" / Flag,
    "blockading" / Flag,
    "air_combat" / If(this._unit_flag > 0, Flag),
    "owner" / INT,
    "capturing_player" / INT,
    "unit_type" / INT,
    "leader_unit_type" / INT,
    "combat_unit_owner" / INT,
    "combat_unit_id" / INT,
    "transport_unit_owner" / INT,
    "transport_unit_id" / INT,
    "extra_domain_modifier" / Array(NUM_DOMAIN_TYPES, INT),
    "name" / StringAdapter(WSTRING),
    "script_data" / StringAdapter(STRING),
    "has_promotion" / Array(get_enum_length(e.PromotionType), Flag),
    "terrain_double_move_count" / Array(get_enum_length(e.TerrainType), INT),
    "feature_double_move_count" / Array(get_enum_length(e.FeatureType), INT),
    "extra_terrain_attack_percent" / Array(get_enum_length(e.TerrainType), INT),
    "extra_terrain_defense_percent" / Array(get_enum_length(e.TerrainType), INT),
    "extra_feature_attack_percent" / Array(get_enum_length(e.FeatureType), INT),
    "extra_feature_defense_percent" / Array(get_enum_length(e.FeatureType), INT),
    "extra_unit_combat_modifier" / Array(get_enum_length(e.UnitCombatType), INT),
    "_unit_end_index" / Tell,
)

CvUnitAI = Struct(
    *CvUnit.subcons,
    "_unit_ai_flag" / UINT,
    "birthmark" / INT,
    "unit_ai_type" / INT,
    "automated_abort_turn" / INT,
    "_unit_ai_end_index" / Tell,
)

CvSelectionGroup = Struct(
    "_selection_group_start_index" / Tell,
    "_selection_group_flag" / UINT,
    "id" / INT,
    "mission_timer" / INT,
    "force_update" / Flag,
    "owner" / INT,
    "activity_type" / INT,
    "automate_type" / INT,
    "_sz_units" / COUNT,
    "units" / Array(this._sz_units, IDINFO),
    "_sz_mission_queue" / COUNT,
    "mission_queue" / Array(this._sz_mission_queue, MissionData),
    "_selection_group_end_index" / Tell,
)

CvSelectionGroupAI = Struct(
    *CvSelectionGroup.subcons,
    "_selection_group_ai_flag" / UINT,
    "mission_ai_x" / INT,
    "mission_ai_y" / INT,
    "force_separate" / Flag,
    "mission_ai_type" / INT,
    "mission_ai_unit_owner" / INT,
    "mission_ai_unit_id" / INT,
    "group_attack" / Flag,
    "group_attack_x" / INT,
    "group_attack_y" / INT,
    "_selection_group_ai_end_index" / Tell,
)

EventTriggeredData = Struct(
    "id" / INT,
    "trigger" / INT,
    "turn" / INT,
    "player" / INT,
    "city_id" / INT,
    "plot_x" / INT,
    "plot_y" / INT,
    "unit_id" / INT,
    "other_player" / INT,
    "other_player_city_id" / INT,
    "religion" / INT,
    "corporation" / INT,
    "building" / INT,
    "text" / StringAdapter(WSTRING),
    "global_text" / StringAdapter(WSTRING),
)

CvTalkingHeadMessage = Struct(
    "description" / StringAdapter(WSTRING),
    "sound" / StringAdapter(STRING),
    "icon" / StringAdapter(STRING),
    "length" / INT,
    "flash_color" / INT,
    "flash_x" / INT,
    "flash_y" / INT,
    "off_screen_arrows" / Flag,
    "on_screen_arrows" / Flag,
    "turn" / INT,
    "message_type" / INT,
    "from_player" / INT,
    "target" / INT,
    "shown" / Flag,
)

CvPopupInfo = Struct(
    "data1" / INT,
    "data2" / INT,
    "data3" / INT,
    "flags" / INT,
    "option1" / Flag,
    "option2" / Flag,
    "button_popup_type" / INT,
    "text" / StringAdapter(WSTRING),
    "on_focus_python_callback" / StringAdapter(STRING),
    "on_clicked_python_callback" / StringAdapter(STRING),
    "python_module" / StringAdapter(STRING),
    "_sz_python_buttons" / COUNT,
    "python_buttons"
    / Array(
        this._sz_python_buttons,
        Struct("text" / StringAdapter(WSTRING), "art" / StringAdapter(STRING)),
    ),
)

# FVariableSystem.inl writes eight union bytes for all non-string types.
FVariable = Struct(
    "type" / ExprValidator(INT, lambda value, ctx: 0 <= value <= 10),
    "value"
    / Switch(
        this.type,
        {9: StringAdapter(STRING), 10: StringAdapter(WSTRING)},
        default=Bytes(8),
    ),
)

CvDiploParameters = Struct(
    "_flag" / UINT,
    "who_talking_to" / INT,
    "comment_type" / INT,
    "_sz_our_offer" / COUNT,
    "our_offer" / Array(this._sz_our_offer, TradeData),
    "_sz_their_offer" / COUNT,
    "their_offer" / Array(this._sz_their_offer, TradeData),
    "renegotiate" / Flag,
    "ai_contact" / Flag,
    "data" / INT,
    "human_diplo" / Flag,
    "our_offering" / Flag,
    "their_offering" / Flag,
    "chat_text" / StringAdapter(WSTRING),
    "_sz_diplo_comment_args" / COUNT,
    "diplo_comment_args" / Array(this._sz_diplo_comment_args, FVariable),
)

HistoryEntry = Struct("turn" / INT, "value" / INT)
EventEntry = Struct("event" / Enum(INT, e.EventType), "data" / EventTriggeredData)
FreeUnitCombatPromotion = Struct("unit_combat" / INT, "promotion" / INT)
FreeUnitClassPromotion = Struct("unit_class" / INT, "promotion" / INT)
PlayerVote = Struct("id" / INT, "vote" / Enum(INT, e.PlayerVoteType))
UnitExtraCost = Struct("unit_class" / INT, "cost" / INT)

CvPlayer = Struct(
    "_player_start_index" / Tell,
    "_player_flag" / UINT,
    "starting_x" / INT,
    "starting_y" / INT,
    "total_population" / INT,
    "total_land" / INT,
    "total_land_scored" / INT,
    "gold" / INT,
    "gold_per_turn" / INT,
    "advanced_start_points" / INT,
    "golden_age_turns" / INT,
    "num_unit_golden_ages" / INT,
    "strike_turns" / INT,
    "anarchy_turns" / INT,
    "max_anarchy_turns" / INT,
    "anarchy_modifier" / INT,
    "golden_age_modifier" / INT,
    "global_hurry_modifier" / INT,
    "great_people_created" / INT,
    "great_generals_created" / INT,
    "great_people_threshold_modifier" / INT,
    "great_generals_threshold_modifier" / INT,
    "great_people_rate_modifier" / INT,
    "great_general_rate_modifier" / INT,
    "domestic_great_general_rate_modifier" / INT,
    "state_religion_great_people_rate_modifier" / INT,
    "max_global_building_production_modifier" / INT,
    "max_team_building_production_modifier" / INT,
    "max_player_building_production_modifier" / INT,
    "free_experience" / INT,
    "feature_production_modifier" / INT,
    "worker_speed_modifier" / INT,
    "improvement_upgrade_rate_modifier" / INT,
    "military_production_modifier" / INT,
    "space_production_modifier" / INT,
    "city_defense_modifier" / INT,
    "num_nuke_units" / INT,
    "num_outside_units" / INT,
    "base_free_units" / INT,
    "base_free_military_units" / INT,
    "free_units_population_percent" / INT,
    "free_military_units_population_percent" / INT,
    "gold_per_unit" / INT,
    "gold_per_military_unit" / INT,
    "extra_unit_cost" / INT,
    "num_military_units" / INT,
    "happy_per_military_unit" / INT,
    "military_food_production_count" / INT,
    "conscript_count" / INT,
    "max_conscript" / INT,
    "highest_unit_level" / INT,
    "overflow_research" / INT,
    "no_unhealthy_population_count" / INT,
    "exp_in_border_modifier" / INT,
    "building_only_healthy_count" / INT,
    "distance_maintenance_modifier" / INT,
    "num_cities_maintenance_modifier" / INT,
    "corporation_maintenance_modifier" / INT,
    "total_maintenance" / INT,
    "upkeep_modifier" / INT,
    "level_experience_modifier" / INT,
    "extra_health" / INT,
    "building_good_health" / INT,
    "building_bad_health" / INT,
    "extra_happiness" / INT,
    "building_happiness" / INT,
    "largest_city_happiness" / INT,
    "war_weariness_percent_anger" / INT,
    "war_weariness_modifier" / INT,
    "free_specialist" / INT,
    "no_foreign_trade_count" / INT,
    "no_corporations_count" / INT,
    "no_foreign_corporations_count" / INT,
    "coastal_trade_routes" / INT,
    "trade_routes" / INT,
    "revolution_timer" / INT,
    "conversion_timer" / INT,
    "state_religion_count" / INT,
    "no_non_state_religion_spread_count" / INT,
    "state_religion_happiness" / INT,
    "non_state_religion_happiness" / INT,
    "state_religion_unit_production_modifier" / INT,
    "state_religion_building_production_modifier" / INT,
    "state_religion_free_experience" / INT,
    "capital_city_id" / INT,
    "cities_lost" / INT,
    "wins_vs_barbs" / INT,
    "assets" / INT,
    "power" / INT,
    "population_score" / INT,
    "land_score" / INT,
    "wonders_score" / INT,
    "tech_score" / INT,
    "combat_experience" / INT,
    "alive" / Flag,
    "ever_alive" / Flag,
    "turn_active" / Flag,
    "auto_moves" / Flag,
    "end_turn" / Flag,
    "pbem_new_turn" / Flag,
    "extended_game" / Flag,
    "founded_first_city" / Flag,
    "strike" / Flag,
    "id" / INT,
    "personality_type" / INT,
    "current_era" / INT,
    "last_state_religion" / INT,
    "parent" / INT,
    "sea_plot_yield" / Array(NUM_YIELD_TYPES, INT),
    "yield_rate_modifier" / Array(NUM_YIELD_TYPES, INT),
    "capital_yield_rate_modifier" / Array(NUM_YIELD_TYPES, INT),
    "extra_yield_threshold" / Array(NUM_YIELD_TYPES, INT),
    "trade_yield_modifier" / Array(NUM_YIELD_TYPES, INT),
    "free_city_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_percent" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_rate" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_rate_modifier" / Array(NUM_COMMERCE_TYPES, INT),
    "capital_commerce_rate_modifier" / Array(NUM_COMMERCE_TYPES, INT),
    "state_religion_building_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "specialist_extra_commerce" / Array(NUM_COMMERCE_TYPES, INT),
    "commerce_flexible_count" / Array(NUM_COMMERCE_TYPES, INT),
    "gold_per_turn_by_player" / Array(MAX_PLAYERS, INT),
    "espionage_spending_weight_against_team" / Array(MAX_TEAMS, INT),
    "feat_accomplished" / Array(NUM_FEAT_TYPES, Flag),
    "options" / Array(get_enum_length(e.PlayerOptionType), Flag),
    "script_data" / StringAdapter(STRING),
    "bonus_export" / Array(get_enum_length(e.BonusType), INT),
    "bonus_import" / Array(get_enum_length(e.BonusType), INT),
    "improvement_count" / Array(get_enum_length(e.ImprovementType), INT),
    "free_building_count" / Array(get_enum_length(e.BuildingType), INT),
    "extra_building_happiness" / Array(get_enum_length(e.BuildingType), INT),
    "extra_building_health" / Array(get_enum_length(e.BuildingType), INT),
    "feature_happiness" / Array(get_enum_length(e.FeatureType), INT),
    "unit_class_count" / Array(get_enum_length(e.UnitClassType), INT),
    "unit_class_making" / Array(get_enum_length(e.UnitClassType), INT),
    "building_class_count" / Array(get_enum_length(e.BuildingClassType), INT),
    "building_class_making" / Array(get_enum_length(e.BuildingClassType), INT),
    "hurry_count" / Array(get_enum_length(e.HurryType), INT),
    "special_building_not_required_count"
    / Array(get_enum_length(e.SpecialBuildingType), INT),
    "has_civic_option_count" / Array(get_enum_length(e.CivicOptionType), INT),
    "no_civic_upkeep_count" / Array(get_enum_length(e.CivicOptionType), INT),
    "has_religion_count" / Array(get_enum_length(e.ReligionType), INT),
    "has_corporation_count" / Array(get_enum_length(e.CorporationType), INT),
    "upkeep_count" / Array(get_enum_length(e.UpKeepType), INT),
    "specialist_valid_count" / Array(get_enum_length(e.SpecialistType), INT),
    "researching_tech" / Array(get_enum_length(e.TechType), Flag),
    "loyal_member" / Array(get_enum_length(e.VoteSourceType), Flag),
    "civics" / Array(get_enum_length(e.CivicOptionType), Enum(INT, e.CivicType)),
    "specialist_extra_yield"
    / Array(get_enum_length(e.SpecialistType), INT[NUM_YIELD_TYPES]),
    "improvement_yield_change"
    / Array(get_enum_length(e.ImprovementType), INT[NUM_YIELD_TYPES]),
    "_sz_group_cycle" / COUNT,
    "group_cycle" / Array(this._sz_group_cycle, INT),
    "_sz_research_queue" / COUNT,
    "research_queue" / Array(this._sz_research_queue, Enum(INT, e.TechType)),
    "_sz_city_names" / COUNT,
    "city_names" / WStringArrayAdapter(Array(this._sz_city_names, WSTRING)),
    *_free_list_header("plot_groups", "_sz_plot_groups").subcons,
    "plot_groups" / Array(this._sz_plot_groups, CvPlotGroup),
    *_free_list_header("cities", "_sz_cities").subcons,
    "cities" / Array(this._sz_cities, CvCityAI),
    *_free_list_header("units", "_sz_units").subcons,
    "units" / Array(this._sz_units, CvUnitAI),
    *_free_list_header("selection_groups", "_sz_selection_groups").subcons,
    "selection_groups" / Array(this._sz_selection_groups, CvSelectionGroupAI),
    *_free_list_header("events_triggered", "_sz_events_triggered").subcons,
    "events_triggered" / Array(this._sz_events_triggered, EventTriggeredData),
    "_sz_game_messages" / COUNT,
    "game_messages" / Array(this._sz_game_messages, CvTalkingHeadMessage),
    "_sz_popups" / COUNT,
    "popups" / Array(this._sz_popups, CvPopupInfo),
    "_sz_diplomacy" / COUNT,
    "diplomacy" / Array(this._sz_diplomacy, CvDiploParameters),
    "_sz_score_history" / COUNT,
    "score_history" / Array(this._sz_score_history, HistoryEntry),
    "_sz_economy_history" / COUNT,
    "economy_history" / Array(this._sz_economy_history, HistoryEntry),
    "_sz_industry_history" / COUNT,
    "industry_history" / Array(this._sz_industry_history, HistoryEntry),
    "_sz_agriculture_history" / COUNT,
    "agriculture_history" / Array(this._sz_agriculture_history, HistoryEntry),
    "_sz_power_history" / COUNT,
    "power_history" / Array(this._sz_power_history, HistoryEntry),
    "_sz_culture_history" / COUNT,
    "culture_history" / Array(this._sz_culture_history, HistoryEntry),
    "_sz_espionage_history" / COUNT,
    "espionage_history" / Array(this._sz_espionage_history, HistoryEntry),
    "_sz_events_occurred" / COUNT,
    "events_occurred" / Array(this._sz_events_occurred, EventEntry),
    "_sz_event_countdown" / COUNT,
    "event_countdown" / Array(this._sz_event_countdown, EventEntry),
    "_sz_free_unit_combat_promotions" / COUNT,
    "free_unit_combat_promotions"
    / Array(this._sz_free_unit_combat_promotions, FreeUnitCombatPromotion),
    "_sz_free_unit_class_promotions" / COUNT,
    "free_unit_class_promotions"
    / Array(this._sz_free_unit_class_promotions, FreeUnitClassPromotion),
    "_sz_votes" / COUNT,
    "votes" / Array(this._sz_votes, PlayerVote),
    "_sz_unit_extra_costs" / COUNT,
    "unit_extra_costs" / Array(this._sz_unit_extra_costs, UnitExtraCost),
    "_sz_triggers_fired" / If(this._player_flag > 0, COUNT),
    "triggers_fired"
    / IfThenElse(
        this._player_flag > 0,
        Array(this._sz_triggers_fired, Enum(INT, e.EventTriggerType)),
        Flag[min(176, get_enum_length(e.EventTriggerType))],
    ),
    "pop_rush_hurry_count" / INT,
    "inflation_modifier" / INT,
    "_player_end_index" / Tell,
)

CvPlayerAI = Struct(
    *CvPlayer.subcons,
    "_player_ai_flag" / UINT,
    "peace_weight" / INT,
    "espionage_weight" / INT,
    "attack_odds_change" / INT,
    "civic_timer" / INT,
    "religion_timer" / INT,
    "extra_gold_target" / INT,
    "strategy_hash" / INT,
    "strategy_hash_cache_turn" / INT,
    "averages_cache_turn" / INT,
    "average_great_people_multiplier" / INT,
    "average_yield_multiplier" / Array(NUM_YIELD_TYPES, INT),
    "average_commerce_multiplier" / Array(NUM_COMMERCE_TYPES, INT),
    "average_commerce_exchange" / Array(NUM_COMMERCE_TYPES, INT),
    "upgrade_units_cache_turn" / INT,
    "upgrade_units_cached_exp_threshold" / INT,
    "upgrade_units_cached_gold" / INT,
    "num_train_ai_units" / Array(get_enum_length(e.UnitAIType), INT),
    "num_ai_units" / Array(get_enum_length(e.UnitAIType), INT),
    "same_religion_counter" / Array(MAX_PLAYERS, INT),
    "different_religion_counter" / Array(MAX_PLAYERS, INT),
    "favorite_civic_counter" / Array(MAX_PLAYERS, INT),
    "bonus_trade_counter" / Array(MAX_PLAYERS, INT),
    "peacetime_trade_value" / Array(MAX_PLAYERS, INT),
    "peacetime_grant_value" / Array(MAX_PLAYERS, INT),
    "gold_traded_to" / Array(MAX_PLAYERS, INT),
    "attitude_extra" / Array(MAX_PLAYERS, INT),
    "first_contact" / Array(MAX_PLAYERS, Flag),
    "contact_timer" / Array(MAX_PLAYERS, INT[NUM_CONTACT_TYPES]),  # NUM_CONTACT_TYPES
    "memory_count" / Array(MAX_PLAYERS, INT[get_enum_length(e.MemoryType)]),
    "was_financial_trouble" / Flag,
    "turn_last_production_dirty" / INT,
    "_sz_ai_city_sites" / COUNT,
    "ai_city_sites" / Array(this._sz_ai_city_sites, INT),
    "bonus_value" / Array(get_enum_length(e.BonusType), INT),
    "unit_class_weights" / Array(get_enum_length(e.UnitClassType), INT),
    "unit_combat_weights" / Array(get_enum_length(e.UnitCombatType), INT),
    "close_borders_attitude_cache" / Array(MAX_PLAYERS, INT),
    "_player_ai_end_index" / Tell,
)

CvGameRecord = Struct(
    "_game_record_flag" / UINT,
    "era" / INT,
    "map_name" / StringAdapter(STRING),
)

CvPlayerRecord = Struct(
    "_player_record_start_index" / Tell,
    "_player_record_flag" / UINT,
    "id" / INT,
    "time_played" / INT,
    "victory" / INT,
    "leader" / INT,
    "units_built" / Array(get_enum_length(e.UnitType), INT),
    "units_killed" / Array(get_enum_length(e.UnitType), INT),
    "units_lost" / Array(get_enum_length(e.UnitType), INT),
    "buildings_built" / Array(get_enum_length(e.BuildingType), INT),
    "religions_founded" / Array(get_enum_length(e.ReligionType), Flag),
    "cities_built" / INT,
    "cities_razed" / INT,
    "golden_ages" / INT,
    "_player_record_end_index" / Tell,
)

# CvEventReporter::writeStatistics delegates directly to CvStatistics::write.
# Only ever-alive slots have records, in player-slot order, without a count word.
CvStatistics = Struct(
    "_statistics_start_index" / Tell,
    "game" / CvGameRecord,
    "_player_ids"
    / Computed(
        lambda ctx: [i for i, p in enumerate(ctx._.player_records) if p.ever_alive]
    ),
    "players" / Array(lambda ctx: len(ctx._player_ids), CvPlayerRecord),
    Check(lambda ctx: [p.id for p in ctx.players] == ctx._player_ids),
    "_statistics_end_index" / Tell,
)

# Verified against the footer bytes and the user's identification of the map
# markers. The SDK omits this serializer; retain the unnamed four-byte fields.
MapSign = Struct(
    "_unknown_before_coordinates" / Bytes(4),
    "x" / INT,
    "y" / INT,
    "_unknown_after_coordinates" / Bytes(4),
    "caption" / StringAdapter(WSTRING),
)

EngineSigns = Struct(
    "_unknown" / Bytes(4),
    "_sz_signs" / COUNT,
    "signs" / Array(this._sz_signs, MapSign),
)

# Engine serialization is absent from the SDK. Preserve the unknown bytes;
# the c4lib GameFooter schema independently identifies the last byte + MD5 string.
# Python data is retained as bytes, never executed via pickle.loads.
SaveFooter = Struct(
    "_footer_start_index" / Tell,
    "_sz_python_data" / COUNT,
    "python_data" / Bytes(this._sz_python_data),
    "_engine_data_size"
    / Computed(lambda ctx: stream_size(ctx._io) - ctx._io.tell() - 37),
    Check(this._engine_data_size >= 0),
    "engine_data" / Bytes(this._engine_data_size),
    # Parse only this bounded buffer, so malformed signs cannot read checksum bytes.
    "signs" / Computed(lambda ctx: EngineSigns.parse(ctx.engine_data).signs),
    "checksum_byte" / UCHAR,
    "_checksum_length" / Const(32, UINT),
    "checksum"
    / ExprValidator(
        PaddedString(32, "ascii"),
        lambda value, ctx: (
            len(value) == 32 and all(char in "0123456789abcdefABCDEF" for char in value)
        ),
    ),
    "_footer_end_index" / Tell,
)

# Flatten named sections to preserve SaveFile.raw's existing field access.
CivBeyondSwordSave = Struct(
    *SaveHeader.subcons,
    *CvInitCore.subcons,
    *CompressedSectionHeader.subcons,
    *CvGameAI.subcons,
    *CvMap.subcons,
    "team_records" / Array(MAX_TEAMS, IndexedRecord(CvTeamAI, "team")),
    "_teams_end_index" / Tell,
    "player_records" / Array(MAX_PLAYERS, IndexedRecord(CvPlayerAI, "player")),
    "_players_end_index" / Tell,
    "statistics" / CvStatistics,
    Check(
        lambda ctx: (
            ctx.statistics._statistics_end_index
            == ctx._params.get("trailer_start", ctx.statistics._statistics_end_index)
        )
    ),
    "footer" / SaveFooter,
    "_save_end_index" / Tell,
    Terminated,
)
