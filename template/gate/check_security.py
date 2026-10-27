"""Security reviewer: do the deployed models meet the generic security baseline?

    ./py gate/check_security.py

The baseline is the yaml block in .claude/agents/security-reviewer.md (visible where the reviewer is defined,
the same for every project). Reads the deployed state (state.py: getDefinition, role members through a
notebook), not the builder's summary. A table is sensitive by its COLUMNS, whatever the agent named it.
"""
import os
import re
import sys

import yaml

import fabric as f
import findings as F
import state

ME = f.WHO["reviewer"]["upn"]
AGENT = os.path.join(F.ROOT, ".claude", "agents", "security-reviewer.md")


def baseline():
    m = re.search(r"## Security baseline.*?```yaml\n(.*?)```", open(AGENT, encoding="utf-8").read(), re.S)
    if not m:
        raise RuntimeError(f"no baseline block in {os.path.relpath(AGENT, F.ROOT)}")
    return yaml.safe_load(m.group(1))


def main():
    try:
        review()
    except SystemExit:
        raise
    except Exception as e:   # a crash must become a finding, not a missing reviewer
        sys.exit(F.write("security", ME, [F.finding("SEC-005", "blocking", "baseline", f.WS_NAME,
                                                    "security review failed", f"{type(e).__name__}: {str(e)[:300]}")],
                         ["model definitions"]))


def review():
    base = baseline()
    pat = re.compile("|".join(base["sensitive_columns"]), re.I)
    st = state.read()
    out, checked = [], [f"{len(st['models'])} semantic model(s): definition (getDefinition, TMDL)"]
    for m in st["models"]:
        sens = {t: sorted({c for c in x["columns"] + x.get("source_columns", []) if pat.search(c)})
                for t, x in m["tables"].items()}
        sens = {t: c for t, c in sens.items() if c}
        for table, cols in sorted(sens.items()):
            g = state.guarding(m, table)
            if not g:
                filt = [f"{r}: {t} = {e}" for r, x in m["roles"].items() for t, e in x["filters"].items()]
                out.append(F.finding(
                    "SEC-001", "blocking", "baseline", f"{m['name']} / {table}",
                    f"table {table} holds sensitive columns ({', '.join(cols)}) without row-level security",
                    f"definition has {len(m['roles'])} role(s) ({', '.join(m['roles']) or 'none'})"
                    + (f"; filters: {'; '.join(filt)}" if filt else "")
                    + f". No role filters {table}: every workspace Viewer sees every row.",
                    "add a role that filters this table (definition/roles/), deploy, add its members"))
                continue
            if m["members"] is None:
                out.append(F.finding("SEC-004", "blocking", "baseline", f"{m['name']} / {', '.join(sorted(g))}",
                                     "role members could not be read", m["members_error"] or "?"))
                continue
            for role in sorted(g):
                have = m["members"].get(role, [])
                if len(have) < base["min_members"]:
                    out.append(F.finding(
                        "SEC-003", "blocking", "baseline", f"{m['name']} / {role}",
                        f"role «{role}» has no members: Viewers see no data",
                        f"members read as {ME}: {have or 'none'}",
                        "add the members with tools/fab.py model members add"))
        if m["roles"]:
            checked.append(f"role members of {m['name']} (XMLA, inside Fabric)" if m["members"] is not None
                           else f"role members of {m['name']}: NOT READ")
        checked.append(f"{m['name']}: {sum(len(c) for c in sens.values())} sensitive column(s) in "
                       f"{len(sens)} table(s)")
    if st["workspace_roles_error"]:
        err = st["workspace_roles_error"]
        out.append(F.finding("SEC-010", "info", "baseline", f.WS_NAME,
                             "workspace roles not readable by the reviewer (least privilege)",
                             f"GET roleAssignments as {ME}: {' '.join(err.split()[:2])}"
                             + (" InsufficientWorkspaceRole" if "InsufficientWorkspaceRole" in err else "")
                             + ". RLS does not apply to Admin, Member or Contributor; a human checks who holds "
                               "those roles."))
    sys.exit(F.write("security", ME, out, checked))


if __name__ == "__main__":
    main()
