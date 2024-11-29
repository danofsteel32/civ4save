"""Represents binary format of a vanilla .CivBeyondSwordSave file.

Notes:
    - Everything is little endian bc x86.
"""
import os
from enum import EnumMeta
from typing import Any, Dict, Iterable, List, Union

from construct import (
    Adapter,
    Array,
    Computed,
    Enum,
    Flag,
    GreedyRange,
    IfThenElse,
    Int8sl,
    Int8ul,
    Int16sl,
    Int16ul,
    Int32sl,
    Int32ul,
    LazyArray,
    PaddedString,
    Padding,
    Pass,
    StopIf,
    Struct,
    Tell,
    this,
)

from civ4save.utils import get_enum_length

from . import enums as e

MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", 19))
MAX_TEAMS = MAX_PLAYERS
NUM_YIELD_TYPES = 3

# Type Aliases
INT = Int32sl
UINT = Int32ul
SHORT = Int16sl
USHORT = Int16ul
CHAR = Int8sl
UCHAR = Int8ul
# Windows string hacks
# https://stackoverflow.com/questions/402283/stdwstring-vs-stdstring
WSTRING = Struct("_sz" / INT, "string" / PaddedString(this._sz * 2, "utf_16_le"))
STRING = Struct("_sz" / INT, "string" / PaddedString(this._sz, "utf_8"))
# corresponds to IDInfo struct
IDINFO = Struct("owner" / INT, "i_id" / INT)
# len prefixed arrays of various types
CHAR_INT_ARRAY = Struct("_sz" / CHAR, "arr" / INT[this._sz])
CHAR_SHORT_ARRAY = Struct("_sz" / CHAR, "arr" / SHORT[this._sz])
CHAR_CHAR_ARRAY = Struct("_sz" / CHAR, "arr" / CHAR[this._sz])
CHAR_FLAG_ARRAY = Struct("_sz" / CHAR, "arr" / Flag[this._sz])
INT_SHORT_ARRAY = Struct("_sz" / INT, "arr" / SHORT[this._sz])


class StringAdapter(Adapter):
    """Just want the actual string don't care about _sz."""

    def _decode(self, obj: Any, *args: Any) -> str:
        return obj.string


class WStringArrayAdapter(Adapter):
    """Eventually need to support _encode."""

    def _decode(self, obj: Iterable, *args: Any) -> List[str]:
        return [s.string for s in obj]


class StringArrayAdapter(Adapter):
    """Eventually need to support _encode."""

    def _decode(self, obj: Iterable, *args: Any) -> List[str]:
        return [s.string for s in obj]


class EnumArrayAdapter(Adapter):
    """Make Enum arrays more useful.

    Used when an array is of len(Enum) and each element of the array is a value
    member of the Enum.
    """

    def __init__(self, _enum: EnumMeta, *args: Any, **kwargs: Any):
        """Needs the _enum arg in order to cast to correct type."""
        self._enum = _enum
        super().__init__(*args, **kwargs)

    def _decode(self, obj: Iterable, *args: Any) -> Dict:
        return {self._enum(n): val for n, val in enumerate(obj)}

    def _encode(self, obj: Dict, *args: Any) -> List[int]:
        # TODO: ensure sorted by enum value writing same order as read
        return [v for k, v in list(obj.items())]


class VoteOutcomeAdapter(Adapter):
    """VoteOutcome is a hash map in the source code."""

    def _decode(self, obj: Iterable, *args: Any) -> Dict:
        return {e.VoteType(n): e.PlayerVoteType(val) for n, val in enumerate(obj)}


class DealsAdapter(Adapter):
    """The traded item could be a BonusType or TradeableItem."""

    def _decode(self, obj: Iterable, *args: Any) -> List:
        def _process_trades(trades: List[Any]) -> List[dict]:
            player_trades = []
            for trade in trades:
                amount = 1
                item: Union[e.BonusType, e.TradeableItem] = e.TradeableItem[trade.item]
                if item.name in {"TRADE_GOLD", "TRADE_GOLD_PER_TURN"}:
                    amount = trade.extra_data
                elif item.name == "TRADE_RESOURCES":
                    item = e.BonusType(trade.extra_data)
                player_trades.append(dict(item=item, amount=amount))
            return player_trades

        deals = []
        for deal in obj:
            trade_deal = dict(
                first_player=deal.first_player,
                second_player=deal.second_player,
                initial_game_turn=deal.initial_game_turn,
                first_trades=_process_trades(deal.first_trades),
                second_trades=_process_trades(deal.second_trades),
            )
            deals.append(trade_deal)
        return deals


CvPlot = Struct(
    "_plot_start_index" / Tell,
    "plot_flag" / UINT,
    "x" / SHORT,
    "y" / SHORT,
    # check to avoid the plots array bug
    StopIf(this._.grid_width == (this.x - 1) and this._.grid_height == (this.y - 1)),
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
    "plot_script_data"
    / StringAdapter(STRING),  # only char* string see so far not sure correct
    "build_progress" / INT_SHORT_ARRAY,
    "_sz_culture_range_cities" / CHAR,
    "culture_range_cities"
    / IfThenElse(
        this._sz_culture_range_cities > 0,
        Array(
            # this._._sz_culture_range_cities,
            MAX_PLAYERS,
            Struct(
                "_sz_crc" / INT, IfThenElse(this._sz_crc > 0, CHAR[this._sz_crc], Pass)
            ),
        ),
        Pass,
    ),
    "_sz_invisible_visibility" / CHAR,
    "invisible_visibles"
    / IfThenElse(
        this._sz_invisible_visibility > 0,
        Array(
            # this._._sz_invisible_visibility,
            MAX_TEAMS,
            Struct(
                "_sz_iv" / INT, IfThenElse(this._sz_iv > 0, SHORT[this._sz_iv], Pass)
            ),
        ),
        Pass,
    ),
    "_sz_units" / INT,
    "units" / Array(this._sz_units, IDINFO),
    "_plot_end_index" / Tell,
    "plot_sizeof" / Computed(this._plot_end_index - this._plot_start_index),
)

# used multiple times in deals struct
TradeData = Struct(
    "item" / Enum(INT, e.TradeableItem),
    "extra_data" / INT,  # could be BonusType or amount of gold/turn
    "offering" / Flag,
    Padding(1),
    "hidden" / Flag,
    Padding(1),
)

# used in vote_selections and votes_triggered structs
VoteOption = Struct(
    "type" / Enum(INT, e.VoteType),
    "player" / INT,
    "city_id" / INT,
    "other_player" / INT,
    "text" / StringAdapter(WSTRING),
)

# main Struct
CivBeyondSwordSave = Struct(
    "version" / INT,
    "_save_bits" / Array(8, INT),
    "_bytes_to_zlib_magic_number" / INT,
    # BEGIN CvInitCore
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
    "num_custom_map_options" / INT,
    "num_hidden_custom_map_options" / INT,
    "custom_map_options" / INT[this.num_custom_map_options],
    "_sz_victories" / INT,
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
    "emails" / StringArrayAdapter(STRING[MAX_PLAYERS]),
    "smtp_hosts" / StringArrayAdapter(STRING[MAX_PLAYERS]),
    "white_flags" / Flag[MAX_PLAYERS],
    "_mystery" / INT[MAX_PLAYERS],
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
    # BEGIN CvGameAI
    "_game_ai_flag" / UINT,
    "_game_ai_pad" / INT,
    # BEGIN CvGame
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
    "ai_rank_team" / INT[MAX_PLAYERS],
    "ai_team_rank" / INT[MAX_PLAYERS],
    "ai_team_score" / INT[MAX_PLAYERS],
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
    "holy_cities" / LazyArray(get_enum_length(e.ReligionType), IDINFO),
    "corporation_headquarters" / LazyArray(get_enum_length(e.ReligionType), IDINFO),
    "_sz_cities_destroyed" / INT,
    "cities_destroyed" / WStringArrayAdapter(WSTRING[this._sz_cities_destroyed]),
    "_sz_gp_born" / INT,
    "great_people_born" / WStringArrayAdapter(WSTRING[this._sz_gp_born]),
    "_deals_num_slots" / INT,
    "_deals_last_index" / INT,
    "_deals_free_list_head" / INT,
    "_deals_free_list_count" / INT,
    "_deals_current_id" / INT,
    "_deals_next_free_index_array" / INT[this._deals_num_slots],
    "_sz_deals" / INT,
    "deals"
    / DealsAdapter(
        Array(
            this._sz_deals,
            Struct(
                "_flag" / UINT,
                "id" / INT,
                "initial_game_turn" / INT,
                "first_player" / INT,
                "second_player" / INT,
                "_sz_first_trades" / INT,
                "first_trades" / Array(this._sz_first_trades, TradeData),
                "_sz_second_trades" / INT,
                "second_trades" / Array(this._sz_second_trades, TradeData),
            ),
        )
    ),
    "_vote_selections_num_slots" / INT,
    "_vote_selections_last_index" / INT,
    "_vote_selections_free_list_head" / INT,
    "_vote_selections_free_list_count" / INT,
    "_vote_selections_current_id" / INT,
    "_vote_selections_next_free_index_array" / INT[this._vote_selections_num_slots],
    "_sz_vote_selections" / INT,
    "vote_selections"
    / Array(
        this._sz_vote_selections,
        Struct(
            "vote_id" / INT,
            "vote_source" / Enum(INT, e.VoteSourceType),
            "_sz_vote_options" / INT,
            "vote_options" / Array(this._sz_vote_options, VoteOption),
        ),
    ),
    "_votes_triggered_num_slots" / INT,
    "_votes_triggered_last_index" / INT,
    "_votes_triggered_free_list_head" / INT,
    "_votes_triggered_free_list_count" / INT,
    "_votes_triggered_current_id" / INT,
    "_votes_triggered_next_free_index_array" / INT[this._votes_triggered_num_slots],
    "_sz_votes_triggered" / INT,
    "votes_triggered"
    / Array(
        this._sz_votes_triggered,
        Struct(
            "vote_id" / INT,
            "vote_source" / Enum(INT, e.VoteSourceType),
            "vote_option" / VoteOption,
        ),
    ),
    "map_random_seed" / UINT,
    "soren_random_seed" / UINT,
    "_sz_replay_messages" / INT,
    "replay_messages"
    / LazyArray(
        this._sz_replay_messages,
        Struct(
            "turn" / INT,
            "type" / Enum(INT, e.ReplayMessageType),
            "plot_x" / INT,
            "plot_y" / INT,
            "player" / INT,
            "text" / StringAdapter(WSTRING),
            "e_color" / Enum(INT, e.ColorValsType),
        ),
    ),
    "num_sessions" / INT,
    "_sz_plot_extra_yields" / INT,
    "plot_extra_yields"
    / Array(
        this._sz_plot_extra_yields,
        Struct(
            "plot_x" / INT,
            "plot_y" / INT,
            "extra_yields" / INT[NUM_YIELD_TYPES],
        ),
    ),
    "_sz_plot_extra_costs" / INT,
    "plot_extra_costs"
    / Array(
        this._sz_plot_extra_costs,
        Struct(
            "plot_x" / INT,
            "plot_y" / INT,
            "extra_costs" / INT[NUM_YIELD_TYPES],
        ),
    ),
    "_sz_vote_source_religions" / INT,
    "vote_source_religions"
    / Array(
        this._sz_vote_source_religions,
        Struct(
            "vote_source" / Enum(INT, e.VoteSourceType),
            "religion" / Enum(INT, e.ReligionType),
        ),
    ),
    "_sz_inactive_triggers" / INT,
    "inactive_triggers"
    / LazyArray(
        this._sz_inactive_triggers,
        Enum(INT, e.EventTriggerType),
    ),
    "shrine_building_count" / INT,
    "shrine_buildings"
    / LazyArray(
        get_enum_length(e.BuildingType),
        Enum(INT, e.BuildingType),
    ),
    "shrine_religion"
    / LazyArray(
        get_enum_length(e.BuildingType),
        Enum(INT, e.BuildingType),
    ),
    "num_culture_victory_cities" / INT,
    "culture_victory_level" / Enum(INT, e.CultureLevelType),
    # BEGIN CvMap
    "_map_flag" / UINT,
    "_map_unknown" / CHAR[8],
    "grid_width" / INT,
    "grid_height" / INT,
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
    "plots" / GreedyRange(CvPlot),
    # raise StopFieldError if len(plots) != grid_width * grid_height
    StopIf(
        (this.plots[-1].x, this.plots[-1].y)  # type:ignore
        != (this.grid_width - 1, this.grid_height - 1)
    ),
    # BEGIN CvArea
    "_areas_num_slots" / INT,
    "_areas_last_index" / INT,
    "_areas_free_list_head" / INT,
    "_areas_free_list_count" / INT,
    "_areas_current_id" / INT,
    "_areas_next_free_index_array" / INT[this._areas_num_slots],
    "sz_areas" / INT,
    "areas"
    / Array(
        # this.sz_areas,
        1,
        Struct(
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
            "best_found_value" / INT[MAX_TEAMS],
            "num_revealed_tiles" / INT[MAX_TEAMS],
            "clean_power_count" / INT[MAX_TEAMS],
            "border_obstacle_count" / INT[MAX_TEAMS],
            "area_ai_type" / Array(MAX_TEAMS, Enum(INT, e.AreaAIType)),
            "target_cities" / LazyArray(MAX_PLAYERS, IDINFO),
            "yield_rate_modifiers" / LazyArray(MAX_PLAYERS, INT[NUM_YIELD_TYPES]),
            "num_train_ai_units" / LazyArray(MAX_PLAYERS, INT[41]),  # UNIT_AI_TYPE
            "num_ai_units" / LazyArray(MAX_PLAYERS, INT[41]),
            "num_bonuses"
            / EnumArrayAdapter(e.BonusType, INT[get_enum_length(e.BonusType)]),
            "num_improvements"
            / EnumArrayAdapter(
                e.ImprovementType, INT[get_enum_length(e.ImprovementType)]
            ),
        ),
    ),
)
