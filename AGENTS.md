# Repository guidance for coding agents

## Project map

`civ4save` reads vanilla Civilization IV: Beyond the Sword save files. Keep the
README focused on users; use this file for repository-specific development
rules.

- `src/civ4save/__init__.py` defines package metadata and the top-level public
  API (`SaveFile` and `NotASaveFile`). `src/civ4save/save_file.py` handles save
  decompression, parsing, and access to the higher-level objects.
- `src/civ4save/cli.py` implements the `civ4save` Click command, and
  `src/civ4save/__main__.py` supports `python -m civ4save`.
- `src/civ4save/objects/` contains the typed settings, game-state, player, and
  plot wrappers exposed over parsed data. Its `__init__.py` is also a public
  export surface.
- `src/civ4save/xml_files.py` and the XML-related functions in
  `src/civ4save/utils.py` locate Civ IV data files and transform their XML.
- `src/civ4save/contrib/` contains convenience models plus reference/generated
  JSON under `contrib/data/`.
- `src/civ4save/vanilla/enums.py` contains reference/generated game enums.
  `src/civ4save/vanilla/structure.py` is the central Construct schema for the
  vanilla BTS binary wire format.
- `tests/saves/` contains binary fixtures; the Python tests live directly under
  `tests/`.
- `tests/conftest.py` isolates the home directory and working directory for
  every test. Its synthetic installation models vanilla/Warlords/BTS XML
  precedence and plain/nested translation values. Use these fixtures for
  filesystem and XML tests; do not depend on an installed game. Resolve binary
  fixture paths relative to the test module, since the working directory varies.

## Development and validation

Use the checked-in `uv.lock` and the canonical `uv` workflow:

```bash
uv sync --locked
uv run --locked pytest
uv run --locked ruff check src tests
uv run --locked mypy src
```

The full pytest suite parses several binary saves and can be slow. During
development, run the narrowest relevant test first, for example:

```bash
uv run pytest tests/test_cli.py
uv run pytest tests/test_savefile.py -k bismark
uv run civ4save --help
uv run civ4save parse --settings tests/saves/bismark-emperor-turn86.CivBeyondSwordSave
```

Before handing off a change, expand validation in proportion to its scope and
report any tests or checks that were not run. Use direct `uv` commands; the old
shell script and tox configuration have been removed. Ruff's `--fix` option
modifies files, so omit it when inspecting the current state. CI runs the full
pytest suite and mypy on Python 3.9 and 3.15, including known baseline failures;
do not hide these failures with broad exclusions or `continue-on-error`.

## Coding expectations

- Preserve Python 3.9 compatibility (`requires-python = ">=3.9"`). Do not use
  syntax or standard-library APIs introduced only in newer Python versions.
- Keep source code typed; the mypy configuration rejects untyped function
  definitions in `src/`.
- Add or update focused tests alongside behavioral changes. Avoid broad fixture
  or snapshot rewrites that hide the behavior being changed.
- Preserve the exports in `src/civ4save/__init__.py` and
  `src/civ4save/objects/__init__.py` unless an intentional public-API change is
  part of the task.
- For a release, keep the version in `pyproject.toml`,
  `src/civ4save/__init__.py`, and `tests/test_civ4save.py` synchronized.
- Treat `tests/saves/*.CivBeyondSwordSave`, `src/civ4save/contrib/data/*.json`,
  and `src/civ4save/vanilla/enums.py` as binary fixtures or reference/generated
  data. Do not reformat, regenerate, or replace them casually; document the
  source and reason when a task requires such a change.

## Binary parser safeguards

Changes to `src/civ4save/vanilla/structure.py` require extra care. Field order,
byte width, signedness, count fields, and conditional presence are wire-format
contracts, not ordinary implementation details. Confirm them against the
serialized format rather than guessing from values in one save.

Read `PLOT_PARSING_NOTES.md` before changing `CvPlot` or plot-array parsing.
Preserve the exact `grid_width * grid_height` plot count and explicit parse
failures. Do not restore `GreedyRange`, sentinel-based stopping, silent
truncation, or any behavior that accepts a partially parsed map as complete.
Where practical, parse errors should identify the plot coordinates and byte
offset.

Validate parser changes against both categories of fixture:

- Small, currently complete maps:
  `bismark-emperor-turn86.CivBeyondSwordSave` and
  `churchill-random-roll.CivBeyondSwordSave`.
- Large maps: `mehmed-epic.CivBeyondSwordSave` and
  `Gandhi-culture-win-t331.CivBeyondSwordSave`.

## Maintenance-branch baseline

Keep known baseline issues separate from regressions introduced by a change:

- The `parse --json` CLI path emits one document with named sections, serializing
  attrs models recursively and enums by name. Keep stdout free of text headers
  and terminal formatting; preserve the existing option precedence.
- The large Mehmed and Gandhi fixtures must parse complete maps. Their former
  failures came from compressed chunk framing, as documented in
  `PLOT_PARSING_NOTES.md`; do not weaken plot validation.
- Ruff uses its current default rule set with `target-version = "py39"`.
  The expanded defaults expose existing lint findings, mostly unused `noqa`
  comments and older typing syntax. Keep these findings separate from new
  violations when validating unrelated changes.

When reporting validation, identify these as pre-existing maintenance-branch
failures and call out any additional failure separately.
