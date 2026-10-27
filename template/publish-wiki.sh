#!/usr/bin/env bash
# Step 4, after /compile-wiki in session-1: the project wiki becomes a visible folder next to the sessions.
# What it does (shown on the slide):
#   cp -R session-1/.omc/wiki wiki         # ADR-*, SEC-*, DRF-*, the decision log, index.md
#   cp -R session-1/rules wiki/rules       # machine-checkable rules for the next review
set -euo pipefail
cd "$(dirname "$0")"
[ -f session-1/.omc/wiki/index.md ] || { echo "no wiki in session-1/.omc/wiki: run /compile-wiki first" >&2; exit 1; }
ls session-1/.omc/wiki | grep -q '^adr-' || { echo "no ADR pages in session-1/.omc/wiki: run /compile-wiki first" >&2; exit 1; }
rm -rf wiki
cp -R session-1/.omc/wiki wiki
if ls session-1/rules/*.yaml >/dev/null 2>&1; then
  cp -R session-1/rules wiki/rules
  ./py review/gate/check_rules.py --lint wiki/rules
fi
chmod -R a+rX wiki
n() { ls wiki | grep -c "^$1-" || true; }
echo "wiki/: $(n adr) ADR, $(n sec) SEC, $(n drf) DRF, $(ls wiki/*.md | wc -l | tr -d ' ') pages in all," \
     "$(ls wiki/rules/*.yaml 2>/dev/null | wc -l | tr -d ' ') rule file(s)"
