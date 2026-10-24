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
2. `CvGame`: implemented.
3. `CvMap`: map fields implemented; area parsing remains incomplete.
4. `CvPlot`: implemented for the full map.
5. `CvArea`: partially implemented; the schema currently reads one area.
6. `CvTeam`: not implemented.
7. `CvPlayer`: not implemented.

The public player objects are assembled from available settings and replay
messages; they do not represent a complete deserialization of `CvPlayer`.

Changes to field order, widths, signedness, counts, and conditional presence
must match the serialized format. Keep the exact `grid_width * grid_height`
plot count and explicit parse failures. Follow [AGENTS.md](AGENTS.md) when
changing or validating the parser.

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
