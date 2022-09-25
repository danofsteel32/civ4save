#!/usr/bin/env bash


set -o errexit
set -o nounset
set -o pipefail

VENVPATH="./venv"

venv() {
    local _bin="${VENVPATH}/bin"
    if [ -d "${_bin}" ]; then
        echo "source ${VENVPATH}/bin/activate"
    else
        echo "source ${VENVPATH}/Scripts/activate"
    fi
}

make-venv() {
    python -m venv "${VENVPATH}"
}

reset-venv() {
    rm -rf "${VENVPATH}"
    make-venv
}

wrapped-python() {
    local _bin="${VENVPATH}/bin"
    if [ -d "${_bin}" ]; then
        "${VENVPATH}"/bin/python "$@"
    else
        "${VENVPATH}"/Scripts/python "$@"
    fi
}

wrapped-pip() {
    wrapped-python -m pip "$@"
}

python-deps() {
    wrapped-pip install --upgrade pip setuptools wheel

    local pip_extras="${1:-}"
    if [ -z "${pip_extras}" ]; then
        wrapped-pip install -e .
    else
        wrapped-pip install -e ".[${pip_extras}]"
    fi
}

install() {
    if [ -d "${VENVPATH}" ]; then
        python-deps "$@"
    else
        make-venv && python-deps "$@"
    fi
}

build() {
    python -m build
}

publish() {
    clean && build
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

tests() {
    wrapped-python -m pytest -rP tests/
}

c4() {
    wrapped-python -m civ4save.cli "$@"
}

default() {
    c4 "$@"
}

TIMEFORMAT="Task completed in %3lR"
time "${@:-default}"
