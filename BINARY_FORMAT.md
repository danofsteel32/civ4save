# Binary save format

`SaveFile` decompresses Beyond the Sword saves and parses them with Construct.
The reader is in [save_file.py](src/civ4save/save_file.py); the binary schema
is in [structure.py](src/civ4save/vanilla/structure.py).

A save contains an uncompressed header, a compressed section, and an
uncompressed trailer. The compressed section stores one zlib stream in chunks,
each prefixed by a little-endian uint32 byte length. A zero length terminates
the section.

## Serialization order and parser coverage

The following list tracks the serialized sections in order, including plots
and areas nested within the map:

1. `CvInitCore`: implemented.
2. `CvGame` and its `CvGameAI` trailer: implemented.
3. `CvMap`: implemented, including plots and the area free list.
4. `CvPlot`: implemented for the full map.
5. `CvArea`: implemented for every active area in the map's free list.
6. `CvTeam` and its `CvTeamAI` trailer: implemented for all team slots.
7. `CvPlayer` and its `CvPlayerAI` trailer: implemented for all player slots,
   including owned plot groups, cities, units, selection groups and events.

The public player objects are still assembled from settings and replay
messages. Complete serialized player state is available in
`SaveFile.raw.player_records`; team state is in `SaveFile.raw.team_records`.
The existing `SaveFile.raw.teams`
continues to contain the per-player team assignments from `CvInitCore`.

Changes to field order, widths, signedness, counts, and conditional presence
must match the serialized format. Keep the exact `grid_width * grid_height`
plot count and explicit parse failures. Follow [AGENTS.md](AGENTS.md) when
changing or validating the parser.

## Schema organization and compatibility

`structure.py` defines independently parseable `SaveHeader`, `CvInitCore`,
`CompressedSectionHeader`, `CvGame`, `CvGameAI` and `CvMap` schemas. The root
`CivBeyondSwordSave` composes their fields into the existing flat `SaveFile.raw`
namespace. Deals, vote options/selections/triggered votes, replay messages,
plot extra yields/costs, and vote-source religions also have named record
schemas. The deal, vote and area lists share the SDK's streamable free-list
framing; their counts and records remain accessible under the existing names.

The compression framing words between settings and the decompressed game data
are `_compression_flag` and `_first_chunk_size`. The actual `CvGameAI` flag and
pad follow `CvGame`, as confirmed by `CvGameAI::read/write`; they are exposed as
`_game_ai_flag` and `_game_ai_pad`. The old parser mislabeled the compression
framing as game AI data and folded the actual game AI trailer into a twelve-byte
map preamble. `CvMap` now starts at its own uint32 flag; `_map_unknown` is gone.
These changes affect private raw fields, not the public model exports.

Lengths and counts reject negative values before reading their payloads. Arrays
are eager, so parsing validates every implemented section immediately. The
root parser stops after the final player AI record, leaving the engine-owned
remainder unread; it does not claim to consume the entire save.

Verified the refactored records against the local SDK at commit
`3c14d26e21e6e335a19af00fc2c0d7acf207fd14`, particularly `CvInitCore.cpp`,
`CvGame.cpp`, `CvGameAI.cpp`, `CvDeal.cpp`, `CvReplayMessage.cpp`,
`CvStructs.cpp/h`, and `CvMap.cpp`. Focused tests exposed and cover these
previous layout/data issues:

- `CvInitCore` writes civilization passwords as a fifth per-player wide-string
  array before emails and SMTP hosts. The parser now exposes `civ_passwords`
  and reads each following array in its proper position. The old `_mystery`
  int array only compensated for these bytes when the strings were empty.
- `TradeData` is a twelve-byte raw struct. Its bools occupy offsets 8 and 9,
  followed by two padding bytes, rather than alternating bools and padding.
- `PlotExtraCost` contains x, y and one int32 cost. `extra_costs` is now a
  scalar, matching the wire format; the old three-int array consumed bytes
  from the following section when an extra cost was present.
- Corporation headquarters use the corporation count, and shrine religions
  decode as `ReligionType` rather than `BuildingType`.
- Plot culture-range and invisible-visibility rows expose their parsed values
  in `arr`; the old anonymous row fields discarded those values.

Tests in `test_binary_primitives.py`, `test_binary_sections.py`,
`test_game_records.py` and `test_plots.py` use handwritten wire bytes rather
than the production builders. They cover signed values, UTF-8 byte lengths,
UTF-16 code-unit lengths, populated and empty arrays, sparse free lists,
record/section boundaries, negative counts and truncated input. Plot failures
within a map identify the expected coordinates and starting byte offset.

## Compressed chunk framing

The checked-in fixtures use 65,536-byte compressed chunks followed by a shorter
final chunk. The stream is flushed without a zlib EOF marker, so the chunk
framing determines where the uncompressed trailer starts. The reader removes
each length word before decompressing its chunk and preserves the header and
trailer.

Earlier large-save failures came from passing the intervening length words
into zlib. These bytes could be accepted as deflate data, corrupting the output
without immediately raising an error. Searching for the end by interpreting
zlib errors did not remove them. The resulting plot failures did not require
changes to the `CvPlot` schema.

Evidence from the checked-in fixtures:

- Gandhi's first chunk ends at file byte 67,035. The corresponding decompressed
  position (including the header) is 951,594, inside plot `(25, 29)`'s culture
  rows. This explains the misleading row lengths and eventual oversized read.
- Mehmed's first chunk ends at file byte 67,055, corresponding to decompressed
  position 1,011,906. Corruption there eventually produced a negative
  `revealed_route_type` length in the old parser.

These offsets are useful when diagnosing framing regressions. The framing was
verified directly against the binary fixtures, not inferred from the SDK.

## CvPlot layout verification

Compared `CvPlot::read` and `CvPlot::write` in
`beyond-the-sword-sdk/CvGameCoreDLL/CvPlot.cpp` and member declarations in
`CvPlot.h` at SDK commit `3c14d26e21e6e335a19af00fc2c0d7acf207fd14`.
The source confirms the existing layout:

- Culture-range cities: a signed byte outer count, then an int32 length and
  that many chars for each row.
- Invisible visibility: a signed byte outer count, then an int32 length and
  that many int16 values for each row.
- Unit list follows those arrays.

No plot field widths, ordering, or conditional-presence rules needed changing
to resolve the compressed chunk framing failures.

## CvArea layout verification

Verified against `CvArea::read/write`, `CvMap::read/write`,
`ReadStreamableFFreeListTrashArray` and `WriteStreamableFFreeListTrashArray`
in `beyond-the-sword-sdk/CvGameCoreDLL/` at the same pinned SDK commit
`3c14d26e21e6e335a19af00fc2c0d7acf207fd14`.
The upstream sources are [CvArea.cpp](https://github.com/dguenms/beyond-the-sword-sdk/blob/3c14d26e21e6e335a19af00fc2c0d7acf207fd14/CvGameCoreDLL/CvArea.cpp)
and [FFreeListTrashArray.h](https://github.com/dguenms/beyond-the-sword-sdk/blob/3c14d26e21e6e335a19af00fc2c0d7acf207fd14/CvGameCoreDLL/FFreeListTrashArray.h).

After the plots, the area free list stores five signed int32 metadata fields,
one signed int32 next-free index per allocated slot, then a signed int32 active
count followed by exactly that many `CvArea` records. Slot capacity and active
count are distinct: freed slots have no serialized area record. Area IDs
contain generation bits and need not be contiguous or equal their record index.
The parser rejects negative counts, slot capacities above the SDK's 8,192-slot
limit, active counts above capacity, and incomplete records.

Each area stores a uint32 expansion flag, eight signed int32 fields, a one-byte
water flag, then fixed arrays. `best_found_value` is per player; revealed tiles,
clean power, border obstacles and area AI types are per team. Target cities
contain two signed int32 values per player. Yield modifiers have three int32
values per player; both unit-AI arrays have 41 per player, as defined by
`NUM_UNITAI_TYPES` in `CvEnums.h`. The final arrays contain one int32 per bonus
and improvement. With vanilla's 19 players/teams, 35 bonuses and 25 improvements,
each area occupies 7,953 bytes. Arrays are parsed eagerly so truncated records
fail during save parsing.

The existing flat `SaveFile.raw` area fields are preserved. Private offsets
`_area_start_index`, `_area_end_index` and `_areas_end_index` identify record
boundaries in the decompressed save, including its uncompressed header:

| Fixture | End of init core | Start of map | Active areas | First byte after areas |
| --- | ---: | ---: | ---: | ---: |
| `bismark-emperor-turn86.CivBeyondSwordSave` | 1,527 | 31,108 | 36 | 1,316,822 |
| `churchill-random-roll.CivBeyondSwordSave` | 1,501 | 11,158 | 13 | 881,418 |
| `mehmed-epic.CivBeyondSwordSave` | 1,511 | 119,882 | 21 | 2,376,410 |
| `Gandhi-culture-win-t331.CivBeyondSwordSave` | 1,491 | 78,966 | 21 | 1,361,972 |

These boundaries and counts were checked against the binary fixtures. Tests
also reconcile each area's tile count with plot area IDs and check aggregate
land and owned tile counts. Synthetic wire-layout tests in
[test_areas.py](tests/test_areas.py) cover all arrays, sparse and empty free lists,
malformed counts, truncation, and leaving the next serialized section unread.

## CvTeam and CvPlayer layout verification

Verified the read and write methods in the same pinned SDK commit, particularly
`CvTeam.cpp`, `CvTeamAI.cpp`, `CvPlayer.cpp`, `CvPlayerAI.cpp`, `CvPlotGroup.cpp`,
`CvCity.cpp`, `CvCityAI.cpp`, `CvUnit.cpp`, `CvUnitAI.cpp`,
`CvSelectionGroup.cpp`, `CvSelectionGroupAI.cpp`, `CvStructs.cpp/h`,
`CvTalkingHeadMessage.cpp`, `CvPopupInfo.cpp`, `CvDiploParameters.cpp`,
`LinkedList.h`, and `FVariableSystem.inl`.

The map is followed by exactly `MAX_TEAMS` team AI records, then exactly
`MAX_PLAYERS` player AI records, including dead, unused and barbarian slots.
Each AI record includes its base record followed by an expansion flag and AI
state. These arrays are eager; incomplete records fail instead of yielding a
partial set of teams or players. Root failures identify the team/player index
and its starting offset, followed by the nested Construct field path.

Team project art arrays have no separate length words: each row uses its
corresponding earlier project count. Player-owned plot groups, cities, units,
selection groups and triggered events each use the same streamable free-list
framing as areas. City, unit and selection group records also include their AI
trailers. Other player data includes research and group queues, city names,
messages, popups, diplomacy, seven history maps, event maps, promotions, votes,
extra costs and fired triggers.

Widths and conditional fields that need special care:

- Flags are one byte; scalar state and enum values are signed int32, except
  expansion flags. Vanilla uses 4 commerce types, 4 domains, 21 city plots,
  31 feats, 14 contact types, 33 memory types and 8 maximum city trade routes.
- `CLinkList` writes raw Windows structs: `OrderData` is 16 bytes (three int32s,
  one bool and three padding bytes), `MissionData` is five int32s, `IDInfo` and
  plot coordinates are two int32s each. `TradeData` remains 12 bytes.
- Unit flags 0 and 1 include the obsolete combat-damage int32; flag 2 omits it.
  Unit flags above 0 include an air-combat bool after the other unit bools.
- Player flag 0 uses 176 fired-trigger bools (or the trigger table size if
  smaller); flags above 0 use a count and int32 trigger IDs. `triggers_fired`
  retains the appropriate wire representation for each version.
- Diplomacy arguments (`FVariable`) store a signed int32 type followed by
  either a narrow/wide string or eight union bytes. Non-string union values
  remain raw bytes, preserving their type-specific bits and unused padding.
- City/unit names, event text and message descriptions are UTF-16 strings;
  scripts, sounds, icons and Python callbacks use narrow strings.

The parser retains scalar enum IDs in the newly added raw records except where
an explicit Construct enum is used. Public object models and exports have not
changed. The engine-owned data after the players is deliberately left unread.

Record boundaries and aggregate counts verified against all four fixtures:

| Fixture | First byte after teams | First byte after players | Cities | Units |
| --- | ---: | ---: | ---: | ---: |
| `bismark-emperor-turn86.CivBeyondSwordSave` | 1,402,436 | 2,212,221 | 36 | 147 |
| `churchill-random-roll.CivBeyondSwordSave` | 967,032 | 1,307,798 | 7 | 52 |
| `mehmed-epic.CivBeyondSwordSave` | 2,462,024 | 5,014,887 | 96 | 731 |
| `Gandhi-culture-win-t331.CivBeyondSwordSave` | 1,447,586 | 3,059,850 | 47 | 471 |

[Tests](tests/test_teams_players.py) independently pack populated and empty
records, project-dependent art arrays, all supported legacy flags, raw struct
padding and Unicode strings. They verify boundaries, reject negative counts,
unknown diplomacy argument types and truncated records, and reconcile real
player cities with map city IDs, populations and selection-group unit IDs.

## Regression safeguards

Keep the exact `grid_width * grid_height` plot count and explicit parse
failures. Do not restore `GreedyRange`, sentinel-based stopping, or silent
truncation. Where practical, errors should identify plot coordinates and byte
offsets.

The full-map tests in [test_savefile.py](tests/test_savefile.py) assert every
coordinate in row-major order for all four fixtures:

| Fixture | Plot count |
| --- | ---: |
| `bismark-emperor-turn86.CivBeyondSwordSave` | 4,368 |
| `churchill-random-roll.CivBeyondSwordSave` | 4,368 |
| `mehmed-epic.CivBeyondSwordSave` | 6,656 |
| `Gandhi-culture-win-t331.CivBeyondSwordSave` | 2,560 |

Synthetic tests in [test_save_decompression.py](tests/test_save_decompression.py)
independently cover multiple chunks, a single chunk, trailer preservation, and
malformed framing.
