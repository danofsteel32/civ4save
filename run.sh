#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

VENVPATH="./venv"

venv() {
    if [[ -d "${VENVPATH}/bin" ]]; then
        echo "source ${VENVPATH}/bin/activate"
    else
        echo "source ${VENVPATH}/Scripts/activate"
    fi
}

make_venv() {
    python -m venv "${VENVPATH}"
}

reset_venv() {
    rm -rf "${VENVPATH}"
    make_venv
}

wrapped_python() {
    if [[ -d "${VENVPATH}/bin" ]]; then
        "${VENVPATH}"/bin/python "$@"
    else
        "${VENVPATH}"/Scripts/python "$@"
    fi
}

wrapped_pip() {
    wrapped_python -m pip "$@"
}

python_deps() {
    wrapped_pip install --upgrade pip setuptools wheel

    local pip_extras="${1:-}"
    if [[ -z "${pip_extras}" ]]; then
        wrapped_pip install -e .
    else
        wrapped_pip install -e ".[${pip_extras}]"
    fi
}

install() {
    if [[ -d "${VENVPATH}" ]]; then
        python_deps "$@"
    else
        make_venv && python_deps "$@"
    fi
}

build() {
    python -m build
}

publish() {
    lint && tests && clean && build
    python -m twine upload dist/*
}

clean() {
    rm -rf dist/
    rm -rf .eggs/
    rm -rf build/
    find . -name '*.pyc' -exec rm -f {} +
    find . -name '*.pyo' -exec rm -f {} +
    find . -name '*~' -exec rm -f {} +
    find . -name '__pycache__' -exec rm -fr {} +
    find . -name '.mypy_cache' -exec rm -fr {} +
    find . -name '.pytest_cache' -exec rm -fr {} +
    find . -name '*.egg-info' -exec rm -fr {} +
}

lint() {
    clean
    wrapped_python -m flake8 src/ &&
    wrapped_python -m mypy src/
}

tests() {
    wrapped_python -m pytest -rA tests/
}

c4() {
    wrapped_python -m civ4save.cli "$@"
}

version_bump() {
    sed -i "s/${1}/${2}/g" pyproject.toml src/civ4save/__init__.py tests/test_civ4save.py
}

default() {
    wrapped_python -i -c 'import civ4save'
}

TIMEFORMAT="Task completed in %3lR"
time "${@:-default}"
