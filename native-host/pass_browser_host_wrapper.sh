#!/bin/bash
# Wrapper script to set up PATH before launching native messaging host
# This is needed because Edge/Chrome start with a minimal PATH on macOS

# Add common paths where pass/gpg might be installed
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Launch the Python host
exec python3 "$SCRIPT_DIR/pass_browser_host.py" "$@"
