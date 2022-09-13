import construct as C

NUM_YIELD_TYPES = 3

# Aliases
INT = C.Int32sl
UINT = C.Int32ul
SHORT = C.Int16sl
USHORT = C.Int16ul
CHAR = C.Int8sl
UCHAR = C.Int8ul


def get_enum_length(e) -> int:
    """
    Ignores the negative value members of the enum because we don't want to
    count the NO_<something> = -1
    """
    return len([m for m in e.__members__ if e[m].value >= 0])


def get_format(ai_survivor: bool = False, plots: bool = False, debug: bool = False):
    if ai_survivor:
        from civ4save.enums import ai_survivor as e
    else:
        from civ4save.enums import vanilla as e

    TradeData = C.Struct(
        'item' / C.Enum(INT, e.TradeableItem),
        'extra_data' / INT,  # BonusType sometimes applicable
        'offering' / C.Flag,
        'pad1' / C.Byte,
        'hidden' / C.Flag,
        'pad2' / C.Byte,
    )

    VoteOption = C.Struct(
        'type' / C.Enum(INT, e.VoteType),
        'player' / INT,
        'city_id' / INT,
        'other_player' / INT,
        'sz_text' / INT,
        'text' / C.PaddedString(C.this.sz_text*2, 'utf_16_le'),
    )

    SaveFormat = C.Struct(
        # C.Probe(C.this._params),
        'save_flag' / INT,
        'save_bits' / C.Array(8, INT),
        'bytes_to_zlib_magic_number' / INT,
        'unknown_int' / INT,
        'game_type' / C.Enum(INT, e.GameType),
        'sz_game_name' / INT,
        'game_name' / C.PaddedString(C.this.sz_game_name*2, 'utf_16_le'),  # w_char hack
        'sz_game_password' / UINT,
        'game_password' / C.PaddedString(C.this.sz_game_password*2, 'utf_16_le'),
        'sz_admin_password' / UINT,
        'admin_password' / C.PaddedString(C.this.sz_admin_password*2, 'utf_16_le'),
        'sz_map_script_name' / UINT,
        'map_script_name' / C.PaddedString(C.this.sz_map_script_name*2, 'utf_16_le'),
        'wb_map_no_players' / C.Flag,
        'world_size' / C.Enum(INT, e.WorldSizeType),
        'climate' / C.Enum(INT, e.ClimateType),
        'sea_level' / C.Enum(INT, e.SeaLevelType),
        'start_era' / C.Enum(INT, e.EraType),
        'game_speed' / C.Enum(INT, e.GameSpeedType),
        'turn_timer' / INT,
        'calendar' / INT,
        'num_custom_map_options' / INT,
        'num_hidden_custom_map_options' / INT,
        'custom_map_options' / INT[C.this.num_custom_map_options],
        'num_victories' / INT,
        'victories' / C.Flag[C.this.num_victories],
        'game_options' / C.Flag[get_enum_length(e.GameOptionType)],
        'mp_game_options' / C.Flag[get_enum_length(e.MultiplayerOptionType)],
        'stat_reporting' / C.Flag,
        'game_turn' / INT,
        'max_turns' / INT,
        'pitboss_turn_time' / INT,
        'target_score' / INT,
        'max_city_eliminations' / INT,
        'advanced_start_points' / INT,
        'leader_names' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'name' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'civ_descriptions' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'description' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'civ_short_descriptions' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'short_description' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'civ_adjectives' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'adjective' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'emails' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'email' / C.PaddedString(C.this.sz, 'utf8'),
                # 'email' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'smtp_hosts' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'smtp_host' / C.PaddedString(C.this.sz, 'utf8'),
                # 'smtp_host' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'white_flags' / C.Flag[C.this._params.max_players],
        'mystery?' / INT[C.this._params.max_players],  # TODO: What is this?
        'flag_decals' / C.Array(
            C.this._params.max_players,
            C.Struct(
                'sz' / UINT,
                'flag_decal' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'civs' / C.Array(
            C.this._params.max_players,
            C.Enum(INT, e.CivilizationType),
        ),
        'leaders' / C.Array(
            C.this._params.max_players,
            C.Enum(INT, e.LeaderHeadType),
        ),
        'teams' / INT[C.this._params.max_players],
        'handicaps' / C.Array(
            C.this._params.max_players,
            C.Enum(INT, e.HandicapType),
        ),
        'colors' / INT[C.this._params.max_players],
        'art_style' / INT[C.this._params.max_players],
        'slot_statuses' / INT[C.this._params.max_players],
        'slot_claims' / INT[C.this._params.max_players],
        'playable_civs' / C.Flag[C.this._params.max_players],
        'minor_nation_civs' / C.Flag[C.this._params.max_players],
        'game_ai_ui_flag' / UINT,
        'game_ai_ipad' / INT,
        'game_ui_flag' / UINT,
        'elapsed_game_turns' / INT,
        'start_turn' / INT,
        'start_year' / INT,
        'estimated_end_turn' / INT,
        'turn_slice' / INT,
        'cutoff_slice' / INT,
        'num_game_turn_active' / INT,
        'total_cities' / INT,
        'total_population' / INT,
        'trade_routes' / INT,
        'free_trade_count' / INT,
        'no_nukes_count' / INT,
        'nukes_exploded' / INT,
        'max_population' / INT,
        'max_land' / INT,
        'max_tech' / INT,
        'max_wonders' / INT,
        'init_population' / INT,
        'init_land' / INT,
        'init_tech' / INT,
        'init_wonders' / INT,
        'init_ai_autoplay' / INT,
        'score_dirty' / C.Flag,
        'circumnavigated' / C.Flag,
        'final_initialized' / C.Flag,
        'hot_pbem_between_turns' / C.Flag,
        'nukes_valid' / C.Flag,
        'handicap' / C.Enum(INT, e.HandicapType),
        'pause_player' / INT,
        'best_land_unit' / C.Enum(INT, e.UnitType),
        'winner' / INT,
        'victory' / C.Enum(INT, e.VictoryType),
        'game_state' / C.Enum(INT, e.GameStateType),
        'sz_script_data' / UINT,
        'script_data' / C.PaddedString(C.this.sz_script_data*2, 'utf_16_le'),
        'ai_rank_player' / INT[C.this._params.max_players],
        'ai_player_rank' / INT[C.this._params.max_players],
        'ai_player_score' / INT[C.this._params.max_players],
        'ai_rank_team' / INT[C.this._params.max_players],
        'ai_team_rank' / INT[C.this._params.max_players],
        'ai_team_score' / INT[C.this._params.max_players],
        'unit_created_counts' / INT[get_enum_length(e.UnitType)],
        'unit_class_created_counts' / INT[get_enum_length(e.UnitClassType)],
        'building_class_created_counts' / INT[get_enum_length(e.BuildingClassType)],
        'project_created_counts' / INT[get_enum_length(e.ProjectType)],
        'force_civic_counts' / INT[get_enum_length(e.CivicType)],
        'vote_outcomes' / INT[get_enum_length(e.VoteType)],
        'religion_game_turn_founded' / INT[get_enum_length(e.ReligionType)],
        'corporation_game_turn_founded' / INT[get_enum_length(e.CorporationType)],
        'secretary_general_timer' / INT[get_enum_length(e.VoteSourceType)],
        'vote_timer' / INT[get_enum_length(e.VoteSourceType)],
        'diplo_vote' / INT[get_enum_length(e.VoteSourceType)],
        'special_unit_valid' / C.Flag[get_enum_length(e.SpecialUnitType)],
        'special_building_valid' / C.Flag[get_enum_length(e.SpecialBuildingType)],
        'religion_slot_taken' / C.Flag[get_enum_length(e.ReligionType)],
        'holy_cities' / C.Array(
            get_enum_length(e.ReligionType),
            C.Struct(
                'owner' / INT,
                'city_id?' / INT
            ),
        ),
        'corporation_headquarters' / C.Array(
            get_enum_length(e.CorporationType),
            C.Struct(
                'owner' / INT,
                'city_id?' / INT
            ),
        ),
        'num_cities_destroyed' / INT,
        'cities_destroyed' / C.Array(
            C.this.num_cities_destroyed,
            C.Struct(
                'sz' / UINT,
                'name' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        'num_great_people_born' / INT,
        'great_people_born' / C.Array(
            C.this.num_great_people_born,
            C.Struct(
                'sz' / UINT,
                'name' / C.PaddedString(C.this.sz*2, 'utf_16_le'),
            ),
        ),
        # useless FFreeListTrashArray metadata
        'deals_num_slots' / INT,
        'deals_last_index' / INT,
        'deals_free_list_head' / INT,
        'deals_free_list_count' / INT,
        'deals_current_id' / INT,
        'deals_next_free_index_array' / INT[C.this.deals_num_slots],
        'sz_deals' / INT,
        'deals' / C.Array(
            C.this.sz_deals,
            C.Struct(
                'ui_flag' / UINT,
                'id' / INT,
                'initial_game_turn' / INT,
                'first_player' / INT,
                'second_player' / INT,
                'sz_first_trades' / INT,
                'first_trades' / C.Array(C.this.sz_first_trades, TradeData),
                'sz_second_trades' / INT,
                'second_trades' / C.Array(C.this.sz_second_trades, TradeData),
            ),
        ),
        'vote_selections_num_slots' / INT,
        'vote_selections_last_index' / INT,
        'vote_selections_free_list_head' / INT,
        'vote_selections_free_list_count' / INT,
        'vote_selections_current_id' / INT,
        'vote_selections_next_free_index_array' / INT[C.this.vote_selections_num_slots],
        'sz_vote_selections' / INT,
        'vote_selections' / C.Array(
            C.this.sz_vote_selections,
            C.Struct(
                'vote_id' / INT,
                'vote_source' / C.Enum(INT, e.VoteSourceType),
                'sz_vote_options' / INT,
                'vote_options' / C.Array(C.this.sz_vote_options, VoteOption),
            ),
        ),
        'votes_triggered_num_slots' / INT,
        'votes_triggered_last_index' / INT,
        'votes_triggered_free_list_head' / INT,
        'votes_triggered_free_list_count' / INT,
        'votes_triggered_current_id' / INT,
        'votes_triggered_next_free_index_array' / INT[C.this.vote_selections_num_slots],
        'sz_votes_triggered' / INT,
        'votes_triggered' / C.Array(
            C.this.sz_votes_triggered,
            C.Struct(
                'vote_id' / INT,
                'vote_source' / C.Enum(INT, e.VoteSourceType),
                'vote_option' / VoteOption
            ),
        ),
        'map_random_seed' / UINT,
        'soren_random_seed' / UINT,
        'sz_replay_messages' / INT,
        'replay_messages' / C.Array(
            C.this.sz_replay_messages,
            C.Struct(
                'turn' / INT,
                'type' / C.Enum(INT, e.ReplayMessageType),
                'plot_x' / INT,
                'plot_y' / INT,
                'player' / INT,
                'sz_text' / INT,
                'text' / C.PaddedString(C.this.sz_text*2, 'utf_16_le'),
                'e_color' / INT,
            ),
        ),
        'num_sessions' / INT,
        'sz_plot_extra_yields' / INT,
        'plot_extra_yields' / C.Array(
            C.this.sz_plot_extra_yields,
            C.Struct(
                'plot_x' / INT,
                'plot_y' / INT,
                'extra_yields' / INT[NUM_YIELD_TYPES],
            ),
        ),
        'sz_plot_extra_costs' / INT,
        'plot_extra_costs' / C.Array(
            C.this.sz_plot_extra_costs,
            C.Struct(
                'plot_x' / INT,
                'plot_y' / INT,
                'extra_costs' / INT[NUM_YIELD_TYPES],
            ),
        ),
        'sz_vote_source_religions' / INT,
        'vote_source_religions' / C.Array(
            C.this.sz_vote_source_religions,
            C.Struct(
                'vote_source' / C.Enum(INT, e.VoteSourceType),
                'religion' / C.Enum(INT, e.ReligionType),
            ),
        ),
        'sz_inactive_triggers' / INT,
        'inactive_triggers' / C.Array(
            C.this.sz_inactive_triggers,
            C.Enum(INT, e.EventTriggerType),
        ),
        C.Struct(
            'shrine_building_count' / INT,
            'shrine_buildings' / C.Array(
                get_enum_length(e.BuildingType),
                C.Enum(INT, e.BuildingType),
            ),
        ),
        'shrine_religion' / INT[get_enum_length(e.BuildingType)],  # idk
        'num_culture_victory_cities' / INT,
        'culture_victory_level' / C.Enum(INT, e.CultureLevelType),
        # Start CvMap
        'map_ui_flag' / UINT,
        'map_unknown_ints' / INT[2],
        'grid_width' / INT,
        'grid_height' / INT,
        'land_plots' / INT,
        'owned_plots' / INT,
        'top_latitude' / INT,
        'bottom_latitude' / INT,
        'next_river_id' / INT,
        'wrap_x' / C.Flag,
        'wrap_y' / C.Flag,
        'bonus_counts' / INT[get_enum_length(e.BonusType)],
        'bonus_counts_on_land' / INT[get_enum_length(e.BonusType)],
    )

    Plot = C.Struct(
        'ui_flag' / UINT,
        'x' / SHORT,
        'y' / SHORT,
        'area_id' / INT,

        'feature_variety' / SHORT,
        'ownership_duration' / SHORT,
        'improvement_duration' / SHORT,
        'upgrade_progress' / SHORT,
        'force_unowned_timer' / SHORT,
        'city_radius_count' / SHORT,
        'river_id' / INT,
        'min_original_start_distance' / SHORT,
        'recon_count' / SHORT,
        'river_crossing_count' / SHORT,

        'starting_plot' / C.Flag,
        'hills' / C.Flag,
        'north_of_river' / C.Flag,
        'west_of_river' / C.Flag,
        'irrigated' / C.Flag,
        'potential_city_work' / C.Flag,

        'owner' / CHAR,
        'plot_type' / C.Enum(SHORT, e.PlotType),
        'terrain_type' / C.Enum(SHORT, e.TerrainType),
        'feature_type' / C.Enum(SHORT, e.FeatureType),
        'bonus_type' / C.Enum(SHORT, e.BonusType),
        'improvement_type' / C.Enum(SHORT, e.ImprovementType),

        'route_type' / SHORT,
        'river_north_south' / CHAR,
        'river_east_west' / CHAR,

        'plot_city_owner' / INT,
        'plot_city_id' / INT,
        'working_city_owner' / INT,
        'working_city_id' / INT,
        'working_city_override_owner' / INT,
        'working_city_override_id' / INT,

        'yields' / SHORT[NUM_YIELD_TYPES],

        'sz_culture' / CHAR,
        'culture' / INT[C.this.sz_culture],

        'sz_found_value' / CHAR,
        'found_value' / SHORT[C.this.sz_found_value],

        'sz_player_city_radius' / CHAR,
        'player_city_radius' / CHAR[C.this.sz_player_city_radius],

        'sz_plot_group' / CHAR,
        'plot_group' / INT[C.this.sz_plot_group],

        'sz_visibility' / CHAR,
        'visibility' / SHORT[C.this.sz_visibility],

        'sz_stolen_visibility' / CHAR,
        'stolen_visibility' / SHORT[C.this.sz_stolen_visibility],

        'sz_blockaded' / CHAR,
        'blockaded' / SHORT[C.this.sz_blockaded],

        'sz_revealed_owner' / CHAR,
        'revealed_owner' / CHAR[C.this.sz_revealed_owner],

        'sz_direction_types' / CHAR,
        'river_crossings' / C.Flag[C.this.sz_direction_types],

        'sz_revealed' / CHAR,
        'revealed' / C.Flag[C.this.sz_revealed],

        'sz_revealed_improvement_type' / CHAR,
        'revealed_improvement_type' / SHORT[C.this.sz_revealed_improvement_type],

        'sz_revealed_route_type' / CHAR,
        'revealed_route_type' / SHORT[C.this.sz_revealed_route_type],

        # 'sz_script_data2' / CHAR[4],
        'sz_script_data2' / INT,

        'script_offset' / C.Tell,
        'script_data' / C.PaddedString(C.this.sz_script_data2, 'utf_8'),

        'sz_build_progress' / INT,
        'build_progress' / SHORT[C.this.sz_build_progress],

        'sz_culture_range_cities' / CHAR,

        'culture_range_cities' / C.Array(
            C.this.sz_culture_range_cities,
            C.Struct(
                'crc_sz' / INT,
                'crc' / CHAR[C.this.crc_sz],
            ),
        ),

        'sz_invisible_visibility' / CHAR,
        'invisible_visibles' / C.Array(
            C.this.sz_invisible_visibility,
            C.Struct(
                'inv_sz' / INT,
                'inv_vis' / SHORT[C.this.inv_sz],
            ),
        ),

        'sz_units' / INT,
        'units' / C.Array(
            C.this.sz_units,
            C.Struct(
                'owner' / INT,
                'id' / INT
            ),
        ),
        'offset' / C.Tell,
    )

    # Buggy, does not work consistently
    # See CvPlot.{cpp,h}
    CvPlots = C.Struct(
        'plots' / C.Array(
            C.this.grid_width * C.this.grid_height,
            Plot
        ),
    )

    # DebugPlot = Plot + C.Struct(C.Probe())
    # DebugPlots = C.Struct(
    #     'plots' / C.Array(
    #         C.this.grid_width * C.this.grid_height,
    #         DebugPlot
    #     ),
    # )

    fmt = SaveFormat
    if plots:
        fmt = fmt + CvPlots

    if debug:
        fmt = fmt + C.Struct(C.Probe())
    return fmt
