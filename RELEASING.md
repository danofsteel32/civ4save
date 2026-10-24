# Releasing civ4save

## Prepare and validate

1. Choose an unused release version. Update `pyproject.toml`,
   `src/civ4save/__init__.py`, and `tests/test_civ4save.py` together.
   `uv version` alone does not update all three files.
2. Run `uv lock`, review its diff, and run `uv sync --locked`.
3. Run the checks below and confirm CI passes on Python 3.9 and 3.15.
4. Write release notes covering user-visible changes, compatibility changes,
   and fixes. Commit the release preparation, including `uv.lock`.

```bash
uv run --locked pre-commit run --all-files
uv run --locked pytest
```

## Build and inspect

Build from the reviewed release commit into a directory dedicated to that
version. For 0.8.0:

```bash
uv build --no-sources --out-dir dist/0.8.0
uvx twine check --strict dist/0.8.0/civ4save-0.8.0.tar.gz dist/0.8.0/civ4save-0.8.0-py3-none-any.whl
```

`uv build` builds the wheel from the source distribution by default. Inspect
both archives: the wheel must include `contrib/data/*.json`, the package code,
and `COPYING` in its license metadata. Confirm the version, Python requirement,
license expression, project links, and rendered README.

Smoke-test the wheel in an isolated environment outside the checkout. This
installs its published dependencies rather than importing the editable project:

```bash
uv venv /tmp/civ4save-release-smoke
uv pip install --python /tmp/civ4save-release-smoke/bin/python dist/0.8.0/civ4save-0.8.0-py3-none-any.whl
cd /tmp
/tmp/civ4save-release-smoke/bin/civ4save --version
/tmp/civ4save-release-smoke/bin/civ4save civs --list
/tmp/civ4save-release-smoke/bin/python -c "from civ4save import SaveFile, NotASaveFile; from civ4save.contrib.leaders import get_leaders; assert get_leaders()"
```

The smoke-test paths above assume Linux/macOS; on Windows use the environment's
`Scripts` directory. Return to the repository before publishing.

## Publish

For local uploads, use a project-scoped PyPI API token through uv's credential
handling or the `UV_PUBLISH_TOKEN` environment variable. Keep credentials out of
committed files and shell command arguments.

Upload only the two artifacts inspected for this release:

```bash
uv publish dist/0.8.0/civ4save-0.8.0.tar.gz dist/0.8.0/civ4save-0.8.0-py3-none-any.whl
```

After a successful upload, check the PyPI page and test the published command:

```bash
uvx --from civ4save==0.8.0 civ4save --version
```

Tag the reviewed release commit as `v0.8.0`, push the tag, and create a GitHub
release with the release notes. If publishing later moves into GitHub Actions,
configure a PyPI Trusted Publisher for the release workflow instead of storing
a long-lived token in GitHub secrets.

References: [uv publishing guide](https://docs.astral.sh/uv/guides/package/),
[PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/).
