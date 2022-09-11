#!/usr/bin/env bash


set -o errexit
set -o nounset
set -o pipefail


APPNAME="civ4save"
VENVPATH="${HOME}/.venv/${APPNAME}"
# SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"


venv() {
    echo "source ${VENVPATH}/bin/activate"
}


make-venv() {
    python -m venv "${VENVPATH}"
}


wrapped-python() {
    "${VENVPATH}"/bin/python "$@"
}


wrapped-pip() {
    wrapped-python -m pip "$@"
}


python-deps() {
    wrapped-pip install --upgrade pip setuptools wheel

    local pip_extras="${1:-}"
    if [ -z "${pip_extras}" ]; then
        wrapped-pip install .
    else
        wrapped-pip install ".[${pip_extras}]"
    fi
}

install() {
    if [ -d "${VENVPATH}" ]; then
        python-deps "$@"
    else
        make-venv && python-deps "$@"
    fi
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
    wrapped-python -m civ4save "$@"
}


default() {
    wrapped-python
}


TIMEFORMAT="Task completed in %3lR"
time "${@:-default}"
