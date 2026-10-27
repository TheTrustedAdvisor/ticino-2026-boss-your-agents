#!/usr/bin/env bash
# Claude Code in the folder this script sits in.
#   ./run.sh                 # interactive
#   ./run.sh -p "/build"     # headless
# PROFILE=<dir> starts Claude Code with a separate, clean configuration (CLAUDE_CONFIG_DIR): no personal
# settings, plugins, hooks or global CLAUDE.md leak into the demo. Sign in once in that profile.
here=$(cd "$(dirname "$0")" && pwd)
[ -z "${PROFILE:-}" ] || export CLAUDE_CONFIG_DIR=$PROFILE
cd "$here" && exec claude "$@"
