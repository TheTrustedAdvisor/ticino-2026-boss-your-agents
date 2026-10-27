#!/usr/bin/env python3
"""PreToolUse hook: every script belongs to exactly one agent role (found in a code review: the allow rules in
settings.json apply to every agent, so without this the builder could run the reviewers' checks as
the reviewer identity and write their findings).

  builder            tools/fab.py (its own identity, its own workspace), edits in work/
  security-reviewer  gate/check_security.py
  decision-reviewer  gate/check_decisions.py, writes only reports/run/decisions.draft.json
  rules-reviewer     gate/check_rules.py
  drift-reviewer     gate/snapshot.py check
  orchestrator       gate/new_run.py, gate/gate.py, gate/snapshot.py sign (still asks the human)
  nobody (human)     anything else in gate/

The role comes from the hook input's agent_type (the subagent's name; absent in the main session).
ROLE_GUARD_LOG=<file> logs every call (rehearsal diagnostics). Edit paths are resolved (realpath: .. and
symlinks) before the check. Offline self-test: ./py gate/role_guard.py --self-test
"""
import json
import os
import re
import sys

OWNER = [(r"tools/fab\.py\b", "builder"),
         (r"gate/check_security\.py\b", "security-reviewer"), (r"gate/check_decisions\.py\b", "decision-reviewer"),
         (r"gate/check_rules\.py\b", "rules-reviewer"),
         (r"gate/snapshot\.py\s+check\b", "drift-reviewer"), (r"gate/snapshot\.py\s+sign\b", "orchestrator"),
         (r"gate/gate\.py\b", "orchestrator"), (r"gate/new_run\.py\b", "orchestrator")]


def decide(d, project):
    """None (allowed) or the reason for denying this tool call."""
    who = d.get("agent_type") or "orchestrator"
    tool, inp = d.get("tool_name"), d.get("tool_input") or {}
    if tool == "Bash":
        cmd = (inp.get("command") or "").strip()
        owned = [role for pat, role in OWNER if re.search(pat, cmd)]
        if "gate/" in cmd or owned:
            bare = re.sub(r"'[^']*'", "''", cmd)   # a DAX query in single quotes may contain <> or >=
            if re.search(r"[;&|`$<>]|\n", bare) or '"' in bare and re.search(r'"[^"]*[`$][^"]*"', bare):
                return "gate and toolkit commands run alone: no chaining, pipes, redirects or substitutions"
            if not owned:
                return "this gate script is for the human, not for agents"
            if len(set(owned)) > 1 or owned[0] != who:
                return f"{cmd.split()[1] if len(cmd.split()) > 1 else cmd} belongs to the {owned[0]}, not the {who}"
    elif tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = inp.get("file_path") or inp.get("notebook_path") or ""
        real = os.path.realpath(os.path.join(project, path))   # resolves .. and symlinks
        root = os.path.realpath(project)
        if who == "decision-reviewer" and real == os.path.join(root, "reports", "run", "decisions.draft.json"):
            return None
        if who != "builder" or not real.startswith(os.path.join(root, "work") + os.sep):
            return f"only the builder edits, and only in work/ ({who}: {path})"
    return None


def self_test():
    """Offline: ./py gate/role_guard.py --self-test (no hook input, no network)."""
    import tempfile
    root = tempfile.mkdtemp()
    os.makedirs(os.path.join(root, "work"))
    os.symlink(os.path.join(root, "gate"), os.path.join(root, "work", "link"))

    def call(agent, tool, **inp):
        return decide({"agent_type": agent, "tool_name": tool, "tool_input": inp}, root)

    cases = [
        ("builder writes work/", call("builder", "Write", file_path=f"{root}/work/m/model.tmdl"), True),
        ("builder writes relative work/", call("builder", "Write", file_path="work/x.tmdl"), True),
        ("builder escapes with ..", call("builder", "Write", file_path=f"{root}/work/../gate/gate.py"), False),
        ("builder escapes by symlink", call("builder", "Write", file_path=f"{root}/work/link/gate.py"), False),
        ("builder writes a sibling workx/", call("builder", "Write", file_path=f"{root}/workx/a"), False),
        ("reviewer writes work/", call("security-reviewer", "Write", file_path=f"{root}/work/a"), False),
        ("decision draft", call("decision-reviewer", "Write",
                                file_path=f"{root}/reports/run/decisions.draft.json"), True),
        ("decision draft via ..", call("decision-reviewer", "Write",
                                       file_path=f"{root}/reports/run/../run/../../gate/x.py"), False),
        ("builder runs fab.py", call("builder", "Bash", command="./py tools/fab.py items"), True),
        ("builder runs a check", call("builder", "Bash", command="./py gate/check_security.py"), False),
        ("security runs its check", call("security-reviewer", "Bash", command="./py gate/check_security.py"), True),
        ("chained check", call("security-reviewer", "Bash", command="./py gate/check_security.py; ls"), False),
        ("orchestrator signs", call(None, "Bash", command="./py gate/snapshot.py sign"), True),
        ("drift reviewer signs", call("drift-reviewer", "Bash", command="./py gate/snapshot.py sign"), False),
    ]
    bad = 0
    for name, reason, want in cases:
        ok = (reason is None) == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {'allowed' if reason is None else 'denied'}")
    print(f"{len(cases) - bad}/{len(cases)} passed")
    return 1 if bad else 0


def main():
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(self_test())
    d = json.load(sys.stdin)
    log = os.environ.get("ROLE_GUARD_LOG")
    if log:
        with open(log, "a") as fh:
            fh.write(json.dumps({k: d.get(k) for k in ("agent_type", "agent_id", "tool_name", "tool_input")}) + "\n")
    reason = decide(d, os.environ.get("CLAUDE_PROJECT_DIR") or d.get("cwd") or os.getcwd())
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
