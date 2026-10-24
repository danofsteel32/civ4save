# CvPlot parsing and compressed chunk framing

## Resolved cause

The large-save failures were caused by decompression, not the `CvPlot` schema.
BTS stores one zlib stream in chunks, each prefixed by a little-endian uint32
compressed-byte length. A zero length terminates the section. The fixtures use
65,536-byte chunks followed by a shorter final chunk. The stream is flushed
without a zlib EOF marker; the framing determines where the trailer starts.

The old reader passed the intervening length words into zlib. These bytes could
be accepted as deflate data, corrupting the output without immediately raising
an error. Searching for the end by interpreting zlib errors did not remove them.
The reader now strips each length word before decompressing its chunk and
preserves the uncompressed header and trailer.

Evidence from the checked-in fixtures:

- Gandhi's first chunk ends at file byte 67,035. The corresponding decompressed
  position (including the header) is 951,594, inside plot `(25, 29)`'s culture
  rows. This explains the misleading row lengths and eventual oversized read.
- Mehmed's first chunk ends at file byte 67,055, corresponding to decompressed
  position 1,011,906. Corruption there eventually produced a negative
  `revealed_route_type` length in the old parser.
- With framing removed, all four required maps parse in full row-major order:
  Bismark and Churchill each have 4,368 plots, Gandhi has 2,560, and Mehmed has
  6,656.

## SDK verification

Compared `CvPlot::read` and `CvPlot::write` in
`beyond-the-sword-sdk/CvGameCoreDLL/CvPlot.cpp` and member declarations in
`CvPlot.h` at SDK commit `3c14d26e21e6e335a19af00fc2c0d7acf207fd14`.
The source confirms the existing layout:

- Culture-range cities: a signed byte outer count, then an int32 length and
  that many chars for each row.
- Invisible visibility: a signed byte outer count, then an int32 length and
  that many int16 values for each row.
- Unit list follows those arrays.

No plot field widths, ordering, or conditional-presence rules needed changing.
The SDK comparison establishes the plot layout; the compressed framing was
verified directly against the binary fixtures, not inferred from `CvPlot.cpp`.

## Regression safeguards

Keep the exact `grid_width * grid_height` plot count. Do not restore
`GreedyRange`, sentinel-based stopping, or silent truncation. The full-map tests
cover all four fixtures and assert every coordinate in row-major order.
Synthetic decompression tests independently cover multiple chunks, a single
chunk, trailer preservation, and malformed framing.
