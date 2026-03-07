#!/usr/bin/env bash
# Create a Python virtual environment and install dependencies for this repo.
# From the project root: ./scripts/setup_venv.sh
# On Debian/Ubuntu, if venv creation fails, run once: sudo apt install python3.12-venv

set -e
cd "$(dirname "$0")/.."
VENV_DIR=".venv"

echo "Creating virtual environment in $VENV_DIR ..."
if ! python3 -m venv "$VENV_DIR" 2>&1; then
    rm -rf "$VENV_DIR"
    echo ""
    echo "Virtual environment creation failed (ensurepip is not available)."
    echo "On Debian/Ubuntu run once:"
    echo "  sudo apt install python3.12-venv"
    echo "Then run this script again."
    exit 1
fi

echo "Installing dependencies from requirements.txt ..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt

echo ""
echo "Done. Activate the environment with:"
echo "  source $VENV_DIR/bin/activate"
echo "Then run scripts from the project root, e.g.:"
echo "  python scripts/plotting_enso.py"
echo ""
echo "Or run without activating:"
echo "  $VENV_DIR/bin/python scripts/plotting_enso.py"
