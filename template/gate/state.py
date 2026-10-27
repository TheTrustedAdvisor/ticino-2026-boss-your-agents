"""The deployed state of the workspace, read by the reviewers with their own identity.

    import state; st = state.read()

What an agent built (items and names), each lakehouse (schemas on or off), and per semantic model: storage
mode and the lakehouse it reads, tables with columns and measures, relationships, RLS roles with their filters,
and the role members. The definition comes from getDefinition (TMDL); members are not part of it and are read
through a notebook inside Fabric (rls_members.py, about 45 s). Never from what the builder said it did.

Reviewers run in parallel; the first one reads, the others wait for its result (reports/run/state.json, one
read per review round: new_run.py empties reports/run).
"""
import fcntl
import json
import os

import fabric as f
import findings as F
import rls_members
import tmdl

CACHE = os.path.join(F.RUN, "state.json")


def _storage(m, by_id):
    """('direct_lake_onelake' | 'direct_lake_sql' | 'import' | 'mixed', lakehouse name or None)."""
    parts = [p for t in m["tables"].values() for p in t["partitions"]]
    if parts and all((p["mode"] or "").lower() == "directlake" for p in parts):
        refs = {tmdl.lakehouse_ref(m["expressions"].get(p["expressionSource"] or "", "")) for p in parts}
        kinds = {r[0] for r in refs if r}
        if len(kinds) == 1 and None not in refs:
            r = next(iter(refs))
            name = by_id.get(r[-1], r[-1])
            return ("direct_lake_onelake" if r[0] == "onelake" else "direct_lake_sql"), name
        return "mixed", None
    if parts and all((p["mode"] or "import").lower() == "import" and p["kind"] != "entity" for p in parts):
        return "import", None
    return "mixed", None


def _model(it, by_id):
    m = tmdl.parse(f.definition("reviewer", it))
    storage, source = _storage(m, by_id)
    out = {"name": it["displayName"], "id": it["id"], "storage": storage, "source_lakehouse": source,
           "tables": {n: {"columns": sorted(c["name"] for c in t["columns"].values()), "measures": t["measures"],
                          "source_columns": sorted(c["sourceColumn"] for c in t["columns"].values()
                                                   if c["sourceColumn"]),
                          "column_sources": {c["name"]: c["sourceColumn"] for c in t["columns"].values()
                                             if c["sourceColumn"]}}
                      for n, t in sorted(m["tables"].items())},
           "relationships": [{"from": r.get("fromColumn"), "to": r.get("toColumn"),
                              "from_table": r["from"], "to_table": r["to"]} for r in m["relationships"]],
           "roles": {n: {"modelPermission": r["modelPermission"], "filters": r["filters"]}
                     for n, r in sorted(m["roles"].items())},
           "members": {}, "members_error": None}
    if m["roles"]:
        live = rls_members.run("list", it["displayName"], as_="reviewer")
        if live.get("ok"):
            out["members"] = {r["name"]: r["members"] for r in live.get("roles", [])}
        else:
            out["members"] = None
            out["members_error"] = rls_members.error_line(live.get("error"))[:300]
    return out


def _read():
    every = f.items("reviewer")
    by_id = {i["id"].lower(): i["displayName"] for i in every}
    # a SQL endpoint carries its lakehouse's name: Direct Lake on SQL points at the endpoint id
    built = f.built_items("reviewer")
    lakehouses = []
    for i in sorted((i for i in built if i["type"] == "Lakehouse"), key=lambda i: i["displayName"]):
        s, b, _ = f.call("GET", f"{f.FAB}/workspaces/{f.WS}/lakehouses/{i['id']}", "reviewer")
        if s != 200 or not isinstance(b, dict):   # never guess: the reviewer's crash handler makes it blocking
            raise RuntimeError(f"read lakehouse {i['displayName']}: HTTP {s} {f.err_text(b)}")
        props = b.get("properties") or {}
        lakehouses.append({"name": i["displayName"], "schemas": bool(props.get("defaultSchema"))})
    roles_ws, err = f.workspace_roles("reviewer")
    return {"workspace": f.WS_NAME, "read_by": f.WHO["reviewer"]["upn"],
            "items": sorted(({"type": i["type"], "name": i["displayName"]} for i in built),
                            key=lambda x: (x["type"], x["name"])),
            "lakehouses": lakehouses,
            "models": [_model(i, by_id) for i in sorted((i for i in built if i["type"] == "SemanticModel"),
                                                        key=lambda i: i["displayName"])],
            "workspace_roles": roles_ws, "workspace_roles_error": err}


def read():
    os.makedirs(F.RUN, exist_ok=True)
    with open(CACHE + ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if os.path.exists(CACHE):
            return json.load(open(CACHE))
        st = _read()
        json.dump(st, open(CACHE, "w"), indent=2)
        return st


def guarding(model, table):
    """{role: (filtered table, expression)} for roles that filter `table`: directly, or a table one active
    relationship away on the one side (a filter there flows to `table`)."""
    via = {table} | {r["to_table"] for r in model["relationships"] if r["from_table"] == table}
    return {role: (t, e) for role, r in model["roles"].items() for t, e in r["filters"].items() if t in via}
