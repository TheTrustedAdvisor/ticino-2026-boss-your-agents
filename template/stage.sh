#!/usr/bin/env bash
# Stage the three working folders of the five steps, bound to your own two Fabric workspaces and identities.
#
#   cp config.example.env config.env      # fill in your workspaces, identities and token commands
#   ./stage.sh [target]                    # default /tmp/boss-your-agents
#
#   target/session-1/        steps 0, 1, 3, 4: builder session, Microsoft Learn MCP + wiki, no rules  (workspace 1)
#   target/review/           step 2: three reviewers + gate, against session 1's decision log        (workspace 1)
#   target/session-2/        step 5: /governed-build, reviewed against wiki/rules                    (workspace 2)
#   target/publish-wiki.sh   step 4: session-1/.omc/wiki + session-1/rules -> target/wiki/
#   target/handover.sh       step 5: wiki/ into session-2, one line into its CLAUDE.md
#
# The script never creates, empties or changes a workspace. Start with two empty workspaces.
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
[ -f "$src/config.env" ] && . "$src/config.env"
dst=${1:-/tmp/boss-your-agents}
omc_ver=${OMC_VERSION:-5.7.18}   # oh-my-claudecode release whose MCP server carries the wiki tools (npm: oh-my-claude-sisyphus)

for v in WORKSPACE_1_ID WORKSPACE_2_ID BUILDER_UPN TOKEN_CMD_BUILDER REVIEWER_UPN TOKEN_CMD_REVIEWER; do
  [ -n "${!v:-}" ] || { echo "$v is not set (config.env, see config.example.env)" >&2; exit 1; }
done
# Claude Code reads CLAUDE.md from every parent folder: nothing above the target may carry instructions.
# (~/.claude/CLAUDE.md is your user memory and loads everywhere; run.sh with PROFILE=<dir> keeps it out.)
d=$(dirname "$dst")
while [ "$d" != "/" ]; do
  for f in "$d/CLAUDE.md" "$d/.claude/CLAUDE.md"; do
    [ "$f" = "$HOME/.claude/CLAUDE.md" ] && continue
    [ -e "$f" ] && { echo "parent instructions found: $f" >&2; exit 1; }
  done
  d=$(dirname "$d")
done
phys=$(cd "$(dirname "$dst")" 2>/dev/null && pwd -P || dirname "$dst")/$(basename "$dst")
command -v node >/dev/null || { echo "node missing: the wiki MCP server is a node script" >&2; exit 1; }

# the wiki: only the MCP server of oh-my-claudecode (no plugin, no hooks, no HUD); OMC_MCP=<path> to use a copy
omc=${OMC_MCP:-}
if [ -z "$omc" ]; then
  cache="${XDG_CACHE_HOME:-$HOME/.cache}/boss-your-agents/omc-$omc_ver"
  if [ ! -f "$cache/package/bridge/mcp-server.cjs" ]; then
    mkdir -p "$cache"
    (cd "$cache" && npm pack "oh-my-claude-sisyphus@$omc_ver" --silent >/dev/null \
       && tar -xzf "oh-my-claude-sisyphus-$omc_ver.tgz" package/bridge/mcp-server.cjs) \
      || { echo "could not fetch oh-my-claude-sisyphus@$omc_ver (npm)" >&2; exit 1; }
  fi
  omc="$cache/package/bridge/mcp-server.cjs"
fi

rm -rf "$dst"; mkdir -p "$dst/.mcp"
cp "$omc" "$dst/.mcp/omc-wiki-mcp.cjs"
cp "$src/py" "$src/publish-wiki.sh" "$src/handover.sh" "$dst/"

lab_env() {   # folder workspace-id workspace-name roles [extra lines]
  {
    printf 'WORKSPACE_ID=%s\nWORKSPACE_NAME=%s\n' "$2" "$3"
    [ -z "${PY:-}" ] || printf 'PY=%s\n' "$PY"
    [ -z "${APPROVED_BY:-}" ] || printf 'APPROVED_BY=%s\n' "$APPROVED_BY"
    case " $4 " in *" builder "*) printf 'BUILDER_UPN=%s\nTOKEN_CMD_BUILDER=%s\n' "$BUILDER_UPN" "$TOKEN_CMD_BUILDER";; esac
    case " $4 " in *" reviewer "*) printf 'REVIEWER_UPN=%s\nTOKEN_CMD_REVIEWER=%s\n' "$REVIEWER_UPN" "$TOKEN_CMD_REVIEWER";; esac
    [ -z "${5:-}" ] || printf '%s\n' "$5"
  } > "$1/.lab-env"
  cp "$src/py" "$src/run.sh" "$1/"
}
builder_kit() {   # folder: task, data, toolkit, MCP servers, git repository (the wiki lives in its top level)
  mkdir -p "$1/task" "$1/data" "$1/tools" "$1/work"
  cp "$src/session-1/task/sales-request.md" "$1/task/"
  cp "$src/data/customers.csv" "$src/data/orders.csv" "$1/data/"
  cp "$src"/toolkit/*.py "$1/tools/"
  python3 - "$1/.mcp.json" "$dst/.mcp/omc-wiki-mcp.cjs" <<'PY'
import json, sys
off = "lsp,ast,python,trace,state,notepad,memory,skills,interop,codex,gemini,antigravity,shared-memory,deepinit"
json.dump({"mcpServers": {
    "microsoft-learn": {"type": "http", "url": "https://learn.microsoft.com/api/mcp"},
    "wiki": {"type": "stdio", "command": "node", "args": [sys.argv[2]],
             # OMC_STATE_DIR empty: the wiki stays in the folder's git repository, never in a central state dir
             "env": {"OMC_DISABLE_TOOLS": off, "OMC_DISABLE_MULTIREPO": "1", "OMC_STATE_DIR": ""}}}},
          open(sys.argv[1], "w"), indent=2)
PY
  (cd "$1" && git init -q . && git config user.name Demo && git config user.email demo@example.com \
     && printf 'work/\nreports/\n.lab-env\n__pycache__/\n' > .gitignore)
}
gate_kit() {   # folder
  mkdir -p "$1/gate" "$1/reports"
  cp "$src"/gate/*.py "$src/toolkit/fabric.py" "$src/toolkit/tmdl.py" "$src/toolkit/rls_members.py" "$1/gate/"
}
settings() {   # {{ROOT}} -> the target (and its physical path, e.g. /private/tmp on macOS); absolute paths need //
  python3 - "$1/.claude/settings.json" "$dst" "$phys" <<'PY'
import json, sys
p, roots = sys.argv[1], list(dict.fromkeys(sys.argv[2:]))
c = json.load(open(p))
for kind, rules in c.get("permissions", {}).items():
    out = []
    for r in rules:
        for x in ([r.replace("{{ROOT}}", "/" + root) for root in roots] if "{{ROOT}}" in r else [r]):
            if x not in out:
                out.append(x)
    c["permissions"][kind] = out
json.dump(c, open(p, "w"), indent=2)
PY
}

# session 1: builder, no rules
mkdir -p "$dst/session-1"
(cd "$src/session-1" && tar --exclude=./task -cf - .) | (cd "$dst/session-1" && tar -xf -)
lab_env "$dst/session-1" "$WORKSPACE_1_ID" "${WORKSPACE_1_NAME:-workspace 1}" builder
builder_kit "$dst/session-1"
settings "$dst/session-1"

# review of workspace 1 against session 1's decision log and the security baseline
mkdir -p "$dst/review"
(cd "$src/review" && tar -cf - .) | (cd "$dst/review" && tar -xf -)
lab_env "$dst/review" "$WORKSPACE_1_ID" "${WORKSPACE_1_NAME:-workspace 1}" reviewer \
  "$(printf 'DECISIONS=../session-1/.omc/wiki\nREVIEWERS=security,decisions,drift')"
gate_kit "$dst/review"
settings "$dst/review"

# session 2: builder + reviewers + gate; its rules arrive with the wiki (handover.sh)
mkdir -p "$dst/session-2"
(cd "$src/session-2" && tar --exclude=./CLAUDE.governed.md -cf - .) | (cd "$dst/session-2" && tar -xf -)
cat "$src/session-1/CLAUDE.md" "$src/session-2/CLAUDE.governed.md" > "$dst/session-2/CLAUDE.md"
lab_env "$dst/session-2" "$WORKSPACE_2_ID" "${WORKSPACE_2_NAME:-workspace 2}" "builder reviewer" \
  "$(printf 'RULES=wiki/rules\nREVIEWERS=security,rules,drift')"
builder_kit "$dst/session-2"
gate_kit "$dst/session-2"
settings "$dst/session-2"

chmod +x "$dst"/*.sh "$dst"/py "$dst"/*/run.sh "$dst"/*/py
echo "staged: $dst"
echo "next:   cd $dst/session-1 && ./py tools/fab.py whoami   # must print the builder identity and workspace 1"
