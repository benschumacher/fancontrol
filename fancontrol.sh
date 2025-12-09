#!/bin/sh
SCRIPT_DIR=$(dirname "$(realpath "$0")")
source "$SCRIPT_DIR/.venv/bin/activate"
exec "$SCRIPT_DIR/fancontrol.py"
