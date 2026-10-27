#!/usr/bin/env bash
# Step 5: session 2 starts with the project wiki. What it does (shown on the slide):
#   cp -R wiki session-2/wiki
#   echo "Project wiki of the last delivery: @wiki/index.md - read it and the pages it lists before you plan, and cite their ids." >> session-2/CLAUDE.md
set -euo pipefail
cd "$(dirname "$0")"
[ -f wiki/index.md ] || { echo "no wiki/ yet: run ./publish-wiki.sh first" >&2; exit 1; }
rm -rf session-2/wiki
cp -R wiki session-2/wiki
line="Project wiki of the last delivery: @wiki/index.md - read it and the pages it lists before you plan, and cite their ids."
grep -qxF "$line" session-2/CLAUDE.md || printf '\n%s\n' "$line" >> session-2/CLAUDE.md
echo "session-2: wiki/ ($(ls session-2/wiki/*.md | wc -l | tr -d ' ') pages, $(ls session-2/wiki/rules/*.yaml 2>/dev/null | wc -l | tr -d ' ') rules), CLAUDE.md: «$line»"
