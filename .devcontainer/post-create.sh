#!/usr/bin/env bash
#
# This shell script runs after the devcontainer is created (see postCreateCommand in
# devcontainer.json) and sets up an isolated virtual environment at .venv. Then the 
# OpenSTRAN library is installed in editable mode along with its development dependencies.

set -euo pipefail

WORKSPACE="$PWD"
VENV="$WORKSPACE/.venv"

echo "==> Upgrading system pip"
python3 -m pip install --upgrade pip

echo "==> Creating virtual environment at $VENV"
python3 -m venv "$VENV"

# shellcheck source=/dev/null
source "$VENV/bin/activate"

echo "==> Upgrading pip inside the virtual environment"
python -m pip install --upgrade pip

echo "==> Installing development dependencies (editable OpenSTRAN + pytest)"
python -m pip install -r "$WORKSPACE/requirements-dev.txt"

# Activate the venv in every interactive shell
ACTIVATE_LINE="[ -f \"$VENV/bin/activate\" ] && source \"$VENV/bin/activate\""