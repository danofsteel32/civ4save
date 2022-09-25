import typing

import construct as C

from .objects import Context
from .utils import get_enum_length

NUM_YIELD_TYPES = 3

"""
Everything is little endian bc x86
Could define string types as:
    W_STRING = partial(C.PaddedString, encoding="utf_16_le")
    STRING = partial(C.PaddedString, encoding="utf_8")
"""
# Type Aliases
INT = C.Int32sl
UINT = C.Int32ul
SHORT = C.Int16sl
USHORT = C.Int16ul
CHAR = C.Int8sl
UCHAR = C.Int8ul


def metadata() -> C.Container[typing.Any]:
    return C.Struct(
        "version" / INT,
        "save_bits" / C.Array(8, INT),
        "bytes_to_zlib_magic_number" / INT,
        "_idx" / C.Tell,
    )


def cv_init_core(ctx: Context) -> C.Container[typing.Any]:
    # CvInitCore
    return C.Struct(
        "save_flag" / UINT,
        "game_type" / C.Enum(INT, ctx.enums.GameType),
        "sz_game_name" / INT,
        "game_name"
        / C.PaddedString(C.this.sz_game_name * 2, "utf_16_le"),  # w_char hack
        "sz_game_password" / UINT,
        "game_password" / C.PaddedString(C.this.sz_game_password * 2, "utf_16_le"),
        "sz_admin_password" / UINT,
        "admin_password" / C.PaddedString(C.this.sz_admin_password * 2, "utf_16_le"),
        "sz_map_script_name" / UINT,
        "map_script_name" / C.PaddedString(C.this.sz_map_script_name * 2, "utf_16_le"),
        "wb_map_no_players" / C.Flag,
        "world_size" / C.Enum(INT, ctx.enums.WorldType),
        "climate" / C.Enum(INT, ctx.enums.ClimateType),
        "sea_level" / C.Enum(INT, ctx.enums.SeaLevelType),
        "start_era" / C.Enum(INT, ctx.enums.EraType),
        "game_speed" / C.Enum(INT, ctx.enums.GameSpeedType),
        "turn_timer" / INT,
        "calendar" / INT,
        "num_custom_map_options" / INT,
        "num_hidden_custom_map_options" / INT,
        "custom_map_options" / INT[C.this.num_custom_map_options],
        "num_victories" / INT,
        "victories" / C.Flag[C.this.num_victories],
        "game_options" / C.Flag[get_enum_length(ctx.enums.GameOptionType)],
        "mp_game_options" / C.Flag[get_enum_length(ctx.enums.MultiplayerOptionType)],
        "stat_reporting" / C.Flag,
        "game_turn" / INT,
        "max_turns" / INT,
        "pitboss_turn_time" / INT,
        "target_score" / INT,
        "max_city_eliminations" / INT,
        "advanced_start_points" / INT,
        "leader_names"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "name" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "civ_descriptions"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "description" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "civ_short_descriptions"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "short_description" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "civ_adjectives"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "adjective" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "emails"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "email" / C.PaddedString(C.this.sz, "utf_8"),
            ),
        ),
        "smtp_hosts"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "smtp_host" / C.PaddedString(C.this.sz, "utf_8"),
            ),
        ),
        "white_flags" / C.Flag[ctx.max_players],
        "mystery?" / INT[ctx.max_players],  # TODO: What is this? Padding?
        "flag_decals"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "sz" / UINT,
                "flag_decal" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "civs"
        / C.Array(
            ctx.max_players,
            C.Enum(INT, ctx.enums.CivilizationType),
        ),
        "leaders"
        / C.Array(
            ctx.max_players,
            C.Enum(INT, ctx.enums.LeaderHeadType),
        ),
        "teams" / INT[ctx.max_players],
        "handicaps"
        / C.Array(
            ctx.max_players,
            C.Enum(INT, ctx.enums.HandicapType),
        ),
        "colors" / INT[ctx.max_players],
        "art_style" / INT[ctx.max_players],
        "slot_statuses" / INT[ctx.max_players],
        "slot_claims" / INT[ctx.max_players],
        "playable_civs" / C.Flag[ctx.max_players],
        "minor_nation_civs" / C.Flag[ctx.max_players],
        "_idx" / C.Tell,
    )


def trade_data(ctx: Context) -> C.Container[typing.Any]:
    return C.Struct(
        "item" / C.Enum(INT, ctx.enums.TradeableItem),
        "extra_data" / INT,  # BonusType sometimes applicable
        "offering" / C.Flag,
        C.Padding(1),
        "hidden" / C.Flag,
        C.Padding(1),
    )


def vote_option(ctx: Context) -> C.Container[typing.Any]:
    return C.Struct(
        "type" / C.Enum(INT, ctx.enums.VoteType),
        "player" / INT,
        "city_id" / INT,
        "other_player" / INT,
        "sz_text" / INT,
        "text" / C.PaddedString(C.this.sz_text * 2, "utf_16_le"),
    )


def cv_game(ctx: Context) -> C.Container[typing.Any]:
    # CvGameAi + CvGame
    TradeData = trade_data(ctx)
    VoteOption = vote_option(ctx)
    return C.Struct(
        "game_ai_ui_flag" / UINT,
        "game_ai_pad" / INT,
        "game_ui_flag" / UINT,
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
        "score_dirty" / C.Flag,
        "circumnavigated" / C.Flag,
        "final_initialized" / C.Flag,
        "hot_pbem_between_turns" / C.Flag,
        "nukes_valid" / C.Flag,
        "handicap" / C.Enum(INT, ctx.enums.HandicapType),
        "pause_player" / INT,  # -1 = NO_PLAYER, otherwise is index of players array
        "best_land_unit" / C.Enum(INT, ctx.enums.UnitType),
        "winner" / INT,  # -1 = NO_TEAM, otherwise is index of teams array
        "victory" / C.Enum(INT, ctx.enums.VictoryType),
        "game_state" / C.Enum(INT, ctx.enums.GameStateType),
        "sz_script_data" / UINT,
        "script_data" / C.PaddedString(C.this.sz_script_data, "utf_8"),
        "ai_rank_player" / INT[ctx.max_players],
        "ai_player_rank" / INT[ctx.max_players],
        "ai_player_score" / INT[ctx.max_players],
        "ai_rank_team" / INT[ctx.max_players],
        "ai_team_rank" / INT[ctx.max_players],
        "ai_team_score" / INT[ctx.max_players],
        "unit_created_counts" / INT[get_enum_length(ctx.enums.UnitType)],
        "unit_class_created_counts" / INT[get_enum_length(ctx.enums.UnitClassType)],
        "building_class_created_counts"
        / INT[get_enum_length(ctx.enums.BuildingClassType)],
        "project_created_counts" / INT[get_enum_length(ctx.enums.ProjectType)],
        "force_civic_counts" / INT[get_enum_length(ctx.enums.CivicType)],
        "vote_outcomes" / INT[get_enum_length(ctx.enums.VoteType)],
        "religion_game_turn_founded" / INT[get_enum_length(ctx.enums.ReligionType)],
        "corporation_game_turn_founded"
        / INT[get_enum_length(ctx.enums.CorporationType)],
        "secretary_general_timer" / INT[get_enum_length(ctx.enums.VoteSourceType)],
        "vote_timer" / INT[get_enum_length(ctx.enums.VoteSourceType)],
        "diplo_vote" / INT[get_enum_length(ctx.enums.VoteSourceType)],
        "special_unit_valid" / C.Flag[get_enum_length(ctx.enums.SpecialUnitType)],
        "special_building_valid"
        / C.Flag[get_enum_length(ctx.enums.SpecialBuildingType)],
        "religion_slot_taken" / C.Flag[get_enum_length(ctx.enums.ReligionType)],
        "holy_cities"
        / C.Array(
            get_enum_length(ctx.enums.ReligionType),
            C.Struct("owner" / INT, "city_id?" / INT),
        ),
        "corporation_headquarters"
        / C.Array(
            get_enum_length(ctx.enums.CorporationType),
            C.Struct("owner" / INT, "city_id?" / INT),
        ),
        "num_cities_destroyed" / INT,
        "cities_destroyed"
        / C.Array(
            C.this.num_cities_destroyed,
            C.Struct(
                "sz" / UINT,
                "name" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "num_great_people_born" / INT,
        "great_people_born"
        / C.Array(
            C.this.num_great_people_born,
            C.Struct(
                "sz" / UINT,
                "name" / C.PaddedString(C.this.sz * 2, "utf_16_le"),
            ),
        ),
        "deals_num_slots" / INT,
        "deals_last_index" / INT,
        "deals_free_list_head" / INT,
        "deals_free_list_count" / INT,
        "deals_current_id" / INT,
        "deals_next_free_index_array" / INT[C.this.deals_num_slots],
        "sz_deals" / INT,
        "deals"
        / C.Array(
            C.this.sz_deals,
            C.Struct(
                "ui_flag" / UINT,
                "id" / INT,
                "initial_game_turn" / INT,
                "first_player" / INT,
                "second_player" / INT,
                "sz_first_trades" / INT,
                "first_trades" / C.Array(C.this.sz_first_trades, TradeData),
                "sz_second_trades" / INT,
                "second_trades" / C.Array(C.this.sz_second_trades, TradeData),
            ),
        ),
        "vote_selections_num_slots" / INT,
        "vote_selections_last_index" / INT,
        "vote_selections_free_list_head" / INT,
        "vote_selections_free_list_count" / INT,
        "vote_selections_current_id" / INT,
        "vote_selections_next_free_index_array" / INT[C.this.vote_selections_num_slots],
        "sz_vote_selections" / INT,
        "vote_selections"
        / C.Array(
            C.this.sz_vote_selections,
            C.Struct(
                "vote_id" / INT,
                "vote_source" / C.Enum(INT, ctx.enums.VoteSourceType),
                "sz_vote_options" / INT,
                "vote_options" / C.Array(C.this.sz_vote_options, VoteOption),
            ),
        ),
        "votes_triggered_num_slots" / INT,
        "votes_triggered_last_index" / INT,
        "votes_triggered_free_list_head" / INT,
        "votes_triggered_free_list_count" / INT,
        "votes_triggered_current_id" / INT,
        "votes_triggered_next_free_index_array" / INT[C.this.vote_selections_num_slots],
        "sz_votes_triggered" / INT,
        "votes_triggered"
        / C.Array(
            C.this.sz_votes_triggered,
            C.Struct(
                "vote_id" / INT,
                "vote_source" / C.Enum(INT, ctx.enums.VoteSourceType),
                "vote_option" / VoteOption,
            ),
        ),
        "map_random_seed" / UINT,
        "soren_random_seed" / UINT,
        "sz_replay_messages" / INT,
        "replay_messages"
        / C.Array(
            C.this.sz_replay_messages,
            C.Struct(
                "turn" / INT,
                "type" / C.Enum(INT, ctx.enums.ReplayMessageType),
                "plot_x" / INT,
                "plot_y" / INT,
                "player" / INT,
                "sz_text" / INT,
                "text" / C.PaddedString(C.this.sz_text * 2, "utf_16_le"),
                "e_color" / INT,
            ),
        ),
        "num_sessions" / INT,
        "sz_plot_extra_yields" / INT,
        "plot_extra_yields"
        / C.Array(
            C.this.sz_plot_extra_yields,
            C.Struct(
                "plot_x" / INT,
                "plot_y" / INT,
                "extra_yields" / INT[NUM_YIELD_TYPES],
            ),
        ),
        "sz_plot_extra_costs" / INT,
        "plot_extra_costs"
        / C.Array(
            C.this.sz_plot_extra_costs,
            C.Struct(
                "plot_x" / INT,
                "plot_y" / INT,
                "extra_costs" / INT[NUM_YIELD_TYPES],
            ),
        ),
        "sz_vote_source_religions" / INT,
        "vote_source_religions"
        / C.Array(
            C.this.sz_vote_source_religions,
            C.Struct(
                "vote_source" / C.Enum(INT, ctx.enums.VoteSourceType),
                "religion" / C.Enum(INT, ctx.enums.ReligionType),
            ),
        ),
        "sz_inactive_triggers" / INT,
        "inactive_triggers"
        / C.Array(
            C.this.sz_inactive_triggers,
            C.Enum(INT, ctx.enums.EventTriggerType),
        ),
        "shrine_building_count" / INT,
        "shrine_buildings"
        / C.Array(
            get_enum_length(ctx.enums.BuildingType),
            C.Enum(INT, ctx.enums.BuildingType),
        ),
        "shrine_religion"
        / C.Array(
            get_enum_length(ctx.enums.BuildingType),
            C.Enum(INT, ctx.enums.BuildingType),
        ),
        "num_culture_victory_cities" / INT,
        "culture_victory_level" / C.Enum(INT, ctx.enums.CultureLevelType),
        "_idx" / C.Tell,
    )


def cv_map_base(ctx: Context) -> C.Container[typing.Any]:
    # CvMap
    return C.Struct(
        "map_ui_flag" / UINT,
        "map_unknown_ints" / CHAR[8],
        "grid_width" / INT,
        "grid_height" / INT,
        "land_plots" / INT,
        "owned_plots" / INT,
        "top_latitude" / INT,
        "bottom_latitude" / INT,
        "next_river_id" / INT,
        "wrap_x" / C.Flag,
        "wrap_y" / C.Flag,
        "bonus_counts" / INT[get_enum_length(ctx.enums.BonusType)],
        "bonus_counts_on_land" / INT[get_enum_length(ctx.enums.BonusType)],
        "_idx" / C.Tell,
    )


def cv_plot(ctx: Context) -> C.Container[typing.Any]:
    # CvPlot (called in CvMap)
    return C.Struct(
        "ui_flag" / UINT,
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
        "starting_plot" / C.Flag,
        "hills" / C.Flag,
        "north_of_river" / C.Flag,
        "west_of_river" / C.Flag,
        "irrigated" / C.Flag,
        "potential_city_work" / C.Flag,
        "owner" / CHAR,
        "plot_type" / C.Enum(SHORT, ctx.enums.PlotType),
        "terrain_type" / C.Enum(SHORT, ctx.enums.TerrainType),
        "feature_type" / C.Enum(SHORT, ctx.enums.FeatureType),
        "bonus_type" / C.Enum(SHORT, ctx.enums.BonusType),
        "improvement_type" / C.Enum(SHORT, ctx.enums.ImprovementType),
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
        "sz_culture" / CHAR,
        "culture" / INT[C.this.sz_culture],
        "sz_found_value" / CHAR,
        "found_value" / SHORT[C.this.sz_found_value],
        "sz_player_city_radius" / CHAR,
        "player_city_radius" / CHAR[C.this.sz_player_city_radius],
        "sz_plot_group" / CHAR,
        "plot_group" / INT[C.this.sz_plot_group],
        "sz_visibility" / CHAR,
        "visibility" / SHORT[C.this.sz_visibility],
        "sz_stolen_visibility" / CHAR,
        "stolen_visibility" / SHORT[C.this.sz_stolen_visibility],
        "sz_blockaded" / CHAR,
        "blockaded" / SHORT[C.this.sz_blockaded],
        "sz_revealed_owner" / CHAR,
        "revealed_owner" / CHAR[C.this.sz_revealed_owner],
        "sz_direction_types" / CHAR,
        "river_crossings" / C.Flag[C.this.sz_direction_types],
        "sz_revealed" / CHAR,
        "revealed" / C.Flag[C.this.sz_revealed],
        "sz_revealed_improvement_type" / CHAR,
        "revealed_improvement_type" / SHORT[C.this.sz_revealed_improvement_type],
        "sz_revealed_route_type" / CHAR,
        "revealed_route_type" / SHORT[C.this.sz_revealed_route_type],
        "sz_plot_script_data" / INT,
        "plot_script_data" / C.PaddedString(C.this.sz_plot_script_data, "utf_8"),
        "sz_build_progress" / INT,
        "build_progress" / SHORT[C.this.sz_build_progress],
        "sz_culture_range_cities" / CHAR,
        "culture_range_cities"
        / C.Array(
            C.this.sz_culture_range_cities,
            C.Struct(
                "crc_sz" / INT,
                "crc" / CHAR[C.this.crc_sz],
            ),
        ),
        "sz_invisible_visibility" / CHAR,
        "invisible_visibles"
        / C.Array(
            C.this.sz_invisible_visibility,
            C.Struct(
                "inv_sz" / INT,
                "inv_vis" / SHORT[C.this.inv_sz],
            ),
        ),
        "sz_units" / INT,
        "units"
        / C.Array(
            C.this.sz_units,
            C.Struct("owner" / INT, "id" / INT),
        ),
        "end_plot_index" / C.Tell,
    )


def cv_plot_debug(ctx: Context) -> C.Container[typing.Any]:
    # Can play with this for debugging without messing up actual CvPlot
    return C.Struct(
        "ui_flag" / UINT,
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
        "starting_plot" / C.Flag,
        "hills" / C.Flag,
        "north_of_river" / C.Flag,
        "west_of_river" / C.Flag,
        "irrigated" / C.Flag,
        "potential_city_work" / C.Flag,
        "owner" / CHAR,
        "plot_type" / C.Enum(SHORT, ctx.enums.PlotType),
        "terrain_type" / C.Enum(SHORT, ctx.enums.TerrainType),
        "feature_type" / C.Enum(SHORT, ctx.enums.FeatureType),
        "bonus_type" / C.Enum(SHORT, ctx.enums.BonusType),
        "improvement_type" / C.Enum(SHORT, ctx.enums.ImprovementType),
        "route_type" / SHORT,
        "river_north_south" / CHAR,
        "river_east_west" / CHAR,
        "plot_city_owner" / INT,
        "plot_city_id" / INT,
        "working_city_owner" / INT,
        "working_city_id" / INT,
        "working_city_override_owner" / INT,
        "working_city_override_id" / INT,
        "yields" / SHORT[NUM_YIELD_TYPES],  # dutch
        "sz_culture" / CHAR,
        "culture" / INT[C.this.sz_culture],
        "sz_found_value" / CHAR,
        "_idx" / C.Tell,
        # "found_value" / SHORT[C.this.sz_found_value],
        # "sz_player_city_radius" / CHAR,
        # "player_city_radius" / CHAR[C.this.sz_player_city_radius],
        # "sz_plot_group" / CHAR,
        # "plot_group" / INT[C.this.sz_plot_group],
        # "sz_visibility" / CHAR,
        # "visibility" / SHORT[C.this.sz_visibility],
        # "sz_stolen_visibility" / CHAR,
        # "stolen_visibility" / SHORT[C.this.sz_stolen_visibility],
        # "sz_blockaded" / CHAR,
        # "blockaded" / SHORT[C.this.sz_blockaded],
        # "sz_revealed_owner" / CHAR,
        # "revealed_owner" / CHAR[C.this.sz_revealed_owner],
        # "sz_direction_types" / CHAR,
        # "river_crossings" / C.Flag[C.this.sz_direction_types],
        # "sz_revealed" / CHAR,
        # "revealed" / C.Flag[C.this.sz_revealed],
        # "sz_revealed_improvement_type" / CHAR,
        # "revealed_improvement_type" / SHORT[C.this.sz_revealed_improvement_type],
        # "sz_revealed_route_type" / CHAR,
        # "revealed_route_type" / SHORT[C.this.sz_revealed_route_type],
        # "sz_plot_script_data" / INT,
        # "plot_script_data" / C.PaddedString(C.this.sz_plot_script_data, "utf_8"),
        # "sz_build_progress" / INT,
        # "build_progress" / SHORT[C.this.sz_build_progress],
    )


def cv_map_area(ctx: Context) -> C.Container[typing.Any]:
    # CvArea (called in CvMap)
    return C.Struct(
        #   pStream->Write(uiFlag);		// flag for expansion
        "area_ui_flag" / UINT,
        # 	pStream->Write(m_iID);
        "area_id" / INT,
        # 	pStream->Write(m_iNumTiles);
        "num_tiles" / INT,
        # 	pStream->Write(m_iNumOwnedTiles);
        "num_owned_tiles" / INT,
        # 	pStream->Write(m_iNumRiverEdges);
        "num_river_edges" / INT,
        # 	pStream->Write(m_iNumUnits);
        "num_units" / INT,
        # 	pStream->Write(m_iNumCities);
        "num_cities" / INT,
        # 	pStream->Write(m_iTotalPopulation);
        "total_population" / INT,
        # 	pStream->Write(m_iNumStartingPlots);
        "num_starting_plots" / INT,
        # 	pStream->Write(m_bWater);
        "water" / C.Flag,
        # 	pStream->Write(MAX_PLAYERS, m_aiUnitsPerPlayer);
        "units_per_player" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiAnimalsPerPlayer);
        "animals_per_player" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiCitiesPerPlayer);
        "cities_per_player" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiPopulationPerPlayer);
        "population_per_player" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiBuildingGoodHealth);
        "building_good_health" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiBuildingBadHealth);
        "building_bad_health" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiBuildingHappiness);
        "building_happiness" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiFreeSpecialist);
        "free_specialist" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiPower);
        "power" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_PLAYERS, m_aiBestFoundValue);
        "best_found_value" / C.Array(ctx.max_players, INT),
        # 	pStream->Write(MAX_TEAMS, m_aiNumRevealedTiles);
        "num_revealed_tiles" / C.Array(ctx.max_teams, INT),
        # 	pStream->Write(MAX_TEAMS, m_aiCleanPowerCount);
        "clean_power_count" / C.Array(ctx.max_teams, INT),
        # 	pStream->Write(MAX_TEAMS, m_aiBorderObstacleCount);
        "border_obstacle_count" / C.Array(ctx.max_teams, INT),
        # pStream->Read(MAX_TEAMS, (int*)m_aeAreaAIType);
        # "area_ai_type" / C.Array(ctx.max_teams, C.Enum(INT, ctx.enums.AreaAIType)),
        # for (iI=0;iI<MAX_PLAYERS;iI++)
        # {
        # 	pStream->Read((int*)&m_aTargetCities[iI].eOwner);
        # 	pStream->Read(&m_aTargetCities[iI].iID);
        # }
        "target_cities"
        / C.Array(
            ctx.max_players,
            C.Struct(
                "player_id" / INT,
                "city_id" / INT,
            ),
        ),
        # for (iI = 0; iI < MAX_PLAYERS; iI++)
        # {
        # 	pStream->Read(NUM_YIELD_TYPES, m_aaiYieldRateModifier[iI]);
        # }
        "yield_rate_modifier" / C.Array(ctx.max_players, C.Array(NUM_YIELD_TYPES, INT)),
        # for (iI = 0; iI < MAX_PLAYERS; iI++)
        # {
        # 	pStream->Read(NUM_UNITAI_TYPES, m_aaiNumTrainAIUnits[iI]);
        # }
        "num_train_ai_units" / C.Array(ctx.max_players, C.Array(41, INT)),
        # for (iI = 0; iI < MAX_PLAYERS; iI++)
        # {
        # 	pStream->Read(NUM_UNITAI_TYPES, m_aaiNumAIUnits[iI]);
        # }
        "num_ai_units" / C.Array(ctx.max_players, C.Array(41, INT)),
        # pStream->Read(GC.getNumBonusInfos(), m_paiNumBonuses);
        "num_bonuses" / INT[get_enum_length(ctx.enums.BonusType)],
        # pStream->Read(GC.getNumImprovementInfos(), m_paiNumImprovements);
        "num_improvements" / INT[get_enum_length(ctx.enums.ImprovementType)],
        "_idx" / C.Tell,
    )


def cv_map_areas(ctx: Context) -> C.Container[typing.Any]:
    # CvArea (CvMap)
    # CvMapArea FFlist metadata plus CvArea array
    # UNDER CONSTRUCTION
    CvMapArea = cv_map_area(ctx)
    return C.Struct(
        "areas_num_slots" / INT,
        "areas_last_index" / INT,
        "areas_free_list_head" / INT,
        "areas_free_list_count" / INT,
        "areas_current_id" / INT,
        "areas_next_free_index_array" / INT[C.this.areas_num_slots],
        "sz_areas" / INT,
        "areas" / C.Array(C.this.sz_areas, CvMapArea),
        # "areas" / C.Array(1, CvMapArea),
        "peek" / INT[32],
        "_idx" / C.Tell,
    )


# # CvTeamAI.cpp::write + CvTeam.cpp::write
# # UNDER CONSTRUCTION
# CvTeam = C.Struct(
#     "team_data" / INT[200],
#     # "team_ui_flag" / UINT,
#     # "team_at_war_plan_state_counter" / C.Array(
#     #     ctx.max_teams,
#     #     INT
#     # ),
#     # "at_war_counter" / INT[ctx.max_teams],
#     # "at_peace_counter" / INT[ctx.max_teams],
#     # "has_met_counter" / INT[ctx.max_teams],
#     # "open_borders_counter" / INT[ctx.max_teams],
#     # "defensive_pact_counter" / INT[ctx.max_teams],
#     # "share_war_counter" / INT[ctx.max_teams],
#     # "war_success" / INT[ctx.max_teams],
#     # "enemy_peace_time_trade_value" / INT[ctx.max_teams],
#     # "enemy_peace_time_grant_value" / INT[ctx.max_teams],
#     # "war_plan" / INT[ctx.max_teams],
#     "_idx" / C.Tell,
# )
