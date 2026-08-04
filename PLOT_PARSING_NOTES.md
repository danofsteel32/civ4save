# CvPlot variable-length array parsing notes

## Summary

Small vanilla BTS saves parse their entire map correctly.  Large saves, including
the Gandhi cultural-victory and Mehmed epic fixtures, stop parsing in the
variable-length tail of `CvPlot`.

The original parser hid this failure by reading plots with `GreedyRange` and
using `StopIf` sentinels.  Once a plot could not be read, `GreedyRange` returned
the already-parsed prefix.  This produced a truncated plot list and, in some
cases, apparent/phantom `-1` plots rather than a useful parse failure.

## Changes tried

`CvPlot` was changed to:

- use `_sz_culture_range_cities` instead of `MAX_PLAYERS` as the outer culture
  row-array length;
- use `_sz_invisible_visibility` instead of `MAX_TEAMS` as the outer invisible
  visibility row-array length;
- reject either count when it is outside `0..MAX_PLAYERS`/`0..MAX_TEAMS`;
- parse exactly `grid_width * grid_height` plots instead of using `GreedyRange`.

The complete-map requirement is correct: malformed plot data should fail
explicitly rather than silently truncate the map.

## Results

The small fixtures parse as complete row-major maps:

- `bismark-emperor-turn86.CivBeyondSwordSave`
- `churchill-random-roll.CivBeyondSwordSave`

The large fixtures still fail:

- `mehmed-epic.CivBeyondSwordSave`: eventually reads `-1` as the length of
  `revealed_route_type`.
- `Gandhi-culture-win-t331.CivBeyondSwordSave`: reaches the culture-range-city
  rows and runs out of input while reading a one-byte row payload.

The legacy greedy parser reaches only 1,881 Gandhi plots, ending at `(24, 29)`;
it does not reach the end of the map.

## Important observation

The attempted outer-count fix does not alter the relevant large-fixture data.
For the non-empty culture and invisible-visibility arrays inspected in Gandhi,
the serialized outer count is `19`, which is also the old `MAX_PLAYERS` value.

At Gandhi plot `(25, 29)`, the culture row data begins with these decoded row
lengths:

```text
0, 7, 7, 5, 0, 0, 0, 0, 0, 0, 0, ...
```

When the parser assumes 19 outer rows, row 11 is decoded as `16847616`
(`0x01010000`) and the parser then exhausts the stream.  That value strongly
looks like bytes belonging to a subsequent field, not a valid row length.

The earlier Gandhi plot `(14, 2)` does successfully contain 19 culture rows.
Therefore a single fixed outer length cannot describe every non-empty plot in
this fixture, but the apparent outer byte is still `19` at the failing plot.

This means the current field called `_sz_culture_range_cities` is either not the
row count for these saves, or the row encoding has another condition/length
field that is currently missing from the parser.

## Likely causes

1. The `CvPlot` layout is incomplete or inaccurate before the culture-range
   fields.  A wrong size in an earlier variable-length field can shift all
   subsequent lengths while still leaving some coordinates plausible.
2. `culture_range_cities` has a sparse or version-dependent representation.
   For example, its leading byte may be an allocation capacity or a flag, while
   the actual number of serialized rows is determined elsewhere.
3. The per-row payload type or its length semantics are wrong.  The parser
   currently treats a row as an `INT` count followed by that many `CHAR`s; an
   omitted terminator, different element width, or conditional payload would
   make later row counts appear nonsensical.
4. The large saves use a save-version or DLL variation not represented by the
   parser, despite otherwise looking like vanilla BTS saves.

## Recommended next steps

1. Obtain and compare the BTS 3.19 `CvPlot::read`/`write` implementation with
   the parser field-for-field.  This is the most reliable way to establish the
   meaning of both leading counts and each row payload.
2. Build a small byte-offset diagnostic parser for `CvPlot`.  For each parsed
   plot, log its start/end offsets, `(x, y)`, both outer counts, and each row
   count.  Compare the final good plot with the first failing one.
3. At Gandhi `(25, 29)`, test candidate row boundaries against the following
   fields (`_sz_invisible_visibility`, `_sz_units`) and the expected start of
   plot `(26, 29)`.  A candidate is credible only if it produces valid bounded
   counts and the next plot's expected coordinates.
4. Parse the same save with an authoritative BTS save reader or an instrumented
   game DLL, if available, and record the exact serialized values for this
   plot.
5. Once the true encoding is confirmed, add focused binary/unit tests for both
   a 19-row plot and the Gandhi `(25, 29)` shape, then restore the full-map
   assertions for Gandhi and Mehmed.

## Safety rule for the parser

Keep the exact `grid_width * grid_height` plot array.  It prevents malformed or
unsupported plot data from being mistaken for a valid, shorter map.  Validation
errors should include the plot coordinates and byte offset where possible.
