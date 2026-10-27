"""Rules reviewer: does the deployed state follow the project wiki's accepted decisions?

    ./py gate/check_rules.py                 # review: RULES in .lab-env (wiki/rules) against the deployed state
    ./py gate/check_rules.py --lint <dir>    # format check only, no Fabric (used when the wiki is compiled)

A rule file is written in step 4 (/compile-wiki) from the project's own decisions, one per ADR that can be
checked by machine:

    id: ADR-001                       # the ADR page it belongs to
    title: <short title>
    status: accepted                  # only accepted rules are reviewed
    decided_by: <who decided: the session, or the human who answered an open question>
    decision: <one paragraph>
    page: <wiki page file of the ADR>
    sources: [<learn.microsoft.com URL>, ...]
    check:                            # optional; only these kinds, any number of them
      item_names: {<Fabric item type>: <regex for the whole name>}
      storage_mode: direct_lake_onelake | direct_lake_sql | import      # every semantic model
      rls: {table_with_columns: [<column>, ...], filter_contains: <text>, min_members: <n>}
      lakehouse_schemas: true | false                                   # every lakehouse

Findings: DEC-201 blocking (the state breaks a rule), DEC-204 blocking (an accepted rule matches nothing
deployed: fail closed, a human looks), DEC-200 blocking (rules missing or not readable), DEC-202 info (an item
type without a naming pattern), DEC-203 info (a rule without a machine check: reviewed by people, from its
page). Column names and filter texts compare without case, spaces, brackets and underscores; columns against
model and source column names.
"""
import glob
import os
import re
import sys

import yaml

TYPES = {"Lakehouse", "SemanticModel", "Report", "Notebook", "Warehouse", "DataPipeline", "Dataflow",
         "Eventhouse", "KQLDatabase", "Environment", "SparkJobDefinition", "MLModel", "MLExperiment"}
MODES = {"direct_lake_onelake", "direct_lake_sql", "import"}
REQUIRED = ("id", "title", "status", "decision", "page")
STATUSES = ("accepted", "proposed", "superseded", "deprecated")


def load(d):
    """(rules by id, errors). Every error names the file."""
    rules, errors = {}, []
    files = sorted(glob.glob(os.path.join(d, "*.yaml")))
    if not files:
        return {}, [f"no rules in {d} (*.yaml)"]
    for p in files:
        n = os.path.basename(p)
        try:
            r = yaml.safe_load(open(p, encoding="utf-8"))
        except yaml.YAMLError as e:
            errors.append(f"{n}: not YAML ({str(e).splitlines()[0]})")
            continue
        if not isinstance(r, dict):
            errors.append(f"{n}: not a mapping")
            continue
        errors += [f"{n}: missing {k}" for k in REQUIRED if not r.get(k)]
        if r.get("id") and not re.fullmatch(r"ADR-\d{3}", str(r["id"])):
            errors.append(f"{n}: id «{r['id']}» is not ADR-nnn")
        if r.get("id") in rules:
            errors.append(f"{n}: id {r['id']} twice")
        if r.get("status") and r["status"] not in STATUSES:
            errors.append(f"{n}: status must be one of {', '.join(STATUSES)}")
        chk = r.get("check")
        if "check" in r and (not isinstance(chk, dict) or not chk):
            errors.append(f"{n}: check must be a non-empty mapping of check kinds (or left out)")
            chk = {}
        for k, v in (chk or {}).items():
            if k == "item_names":
                if not isinstance(v, dict) or not v:
                    errors.append(f"{n}: item_names must map item types to patterns")
                    continue
                for t, pat in v.items():
                    if t not in TYPES:
                        errors.append(f"{n}: item_names: unknown item type {t} ({', '.join(sorted(TYPES))})")
                    if not isinstance(pat, str) or not pat.strip():
                        errors.append(f"{n}: item_names {t}: pattern must be a non-empty string")
                        continue
                    try:
                        re.compile(pat)
                    except re.error as e:
                        errors.append(f"{n}: item_names {t}: bad pattern ({e})")
            elif k == "storage_mode":
                if v not in MODES:
                    errors.append(f"{n}: storage_mode must be one of {', '.join(sorted(MODES))}")
            elif k == "rls":
                twc = v.get("table_with_columns") if isinstance(v, dict) else None
                if not isinstance(twc, list) or not twc or not all(isinstance(c, str) and c.strip() for c in twc):
                    errors.append(f"{n}: rls table_with_columns must be a non-empty list of column names")
                if isinstance(v, dict):
                    mm = v.get("min_members", 1)
                    if not isinstance(mm, int) or isinstance(mm, bool) or mm < 1:
                        errors.append(f"{n}: rls min_members must be a whole number of at least 1")
                    if "filter_contains" in v and (not isinstance(v["filter_contains"], str)
                                                    or not v["filter_contains"].strip()):
                        errors.append(f"{n}: rls filter_contains must be a non-empty text (or left out)")
            elif k == "lakehouse_schemas":
                if not isinstance(v, bool):
                    errors.append(f"{n}: lakehouse_schemas must be true or false")
            else:
                errors.append(f"{n}: unknown check kind «{k}» (item_names, storage_mode, rls, lakehouse_schemas)")
        if r.get("id"):
            rules[r["id"]] = dict(r, _file=n)
    return rules, errors


def lint(d):
    rules, errors = load(d)
    for e in errors:
        print(f"ERROR  {e}")
    checks = sum(1 for r in rules.values() if r.get("check"))
    print(f"{len(rules)} rule(s), {checks} with a machine check, {len(errors)} error(s)")
    return 1 if errors else 0


def norm(text):
    """Names and filter texts compare without case, spaces, brackets and underscores:
    «[Account Manager]» = account_manager."""
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def with_sources(expr, table):
    """The filter with every [column] also spelled by its source column: a rule written against the Delta
    column (account_manager_upn) still finds a filter on the renamed model column ([Account Manager])."""
    src = table.get("column_sources", {})
    return re.sub(r"\[([^\]]+)\]", lambda x: "[" + src.get(x.group(1), x.group(1)) + "]", expr)


def violations(rule, st):
    """[(item, evidence)] where the deployed state breaks the rule's check. ("-", "NOT APPLIED: ...") when a
    check finds nothing deployed to apply to: fail closed, a human looks."""
    out = []
    chk = rule.get("check") or {}
    if "item_names" in chk:
        hit = [i for i in st["items"] if i["type"] in chk["item_names"]]
        for i in hit:
            pat = chk["item_names"][i["type"]]
            if not re.fullmatch(str(pat), i["name"]):
                out.append((i["name"], f"{i['type']} «{i['name']}» does not match {pat}"))
        if not hit:
            out.append(("-", f"NOT APPLIED: no deployed item of type {', '.join(chk['item_names'])}"))
    if "storage_mode" in chk:
        for m in st["models"]:
            if m["storage"] != chk["storage_mode"]:
                out.append((m["name"], f"storage mode is {m['storage']}, the rule says {chk['storage_mode']}"))
        if not st["models"]:
            out.append(("-", "NOT APPLIED: no semantic model deployed"))
    if "rls" in chk:
        import state
        r = chk["rls"]
        cols = {norm(c) for c in r["table_with_columns"]}
        want = norm(r.get("filter_contains") or "")
        applied = 0
        for m in st["models"]:
            for t, x in m["tables"].items():
                hit = sorted({c for c in x["columns"] + x.get("source_columns", []) if norm(c) in cols})
                if not hit:
                    continue
                applied += 1
                g = {role: e for role, (ft, e) in state.guarding(m, t).items()
                     if want in norm(e) or want in norm(with_sources(e, m["tables"].get(ft, {})))}
                if not g:
                    out.append((f"{m['name']} / {t}", f"table {t} ({', '.join(hit)}): no role filters it"
                                + (f" with {r['filter_contains']}" if want else "")
                                + f"; roles: {', '.join(m['roles']) or 'none'}"))
                    continue
                if m["members"] is None:
                    out.append((f"{m['name']} / {t}", f"role members not readable: {m['members_error']}"))
                    continue
                n = max(len(m["members"].get(role, [])) for role in g)
                if n < int(r.get("min_members", 1)):
                    out.append((f"{m['name']} / {', '.join(sorted(g))}",
                                f"{n} member(s), the rule asks for at least {r.get('min_members', 1)}"))
        if not applied:
            out.append(("-", f"NOT APPLIED: no model table has a column {', '.join(r['table_with_columns'])} "
                             "(model or source column name)"))
    if "lakehouse_schemas" in chk:
        for lh in st["lakehouses"]:
            if lh["schemas"] != chk["lakehouse_schemas"]:
                out.append((lh["name"], f"schemas {'enabled' if lh['schemas'] else 'off'}, the rule says "
                                        f"{'enabled' if chk['lakehouse_schemas'] else 'off'}"))
        if not st["lakehouses"]:
            out.append(("-", "NOT APPLIED: no lakehouse deployed"))
    return out


def review():
    import fabric as f
    import findings as F
    import state
    me = f.WHO["reviewer"]["upn"]
    rel = os.path.relpath(F.RULES, F.ROOT)
    try:
        every, errors = load(F.RULES)
        if errors:
            sys.exit(F.write("rules", me, [F.finding("DEC-200", "blocking", "-", rel, "rules not readable",
                                                     "; ".join(errors)[:600])], [f"{rel}/"]))
        rules = {k: r for k, r in every.items() if r.get("status") == "accepted"}
        st = state.read()
        out = []
        for rid, r in sorted(rules.items()):
            if not r.get("check"):
                out.append(F.finding("DEC-203", "info", rid, r["title"], "no machine check",
                                     f"{r['_file']} has no check: block; people review it from {r['page']}"))
            for item, ev in violations(r, st):
                if ev.startswith("NOT APPLIED: "):
                    out.append(F.finding("DEC-204", "blocking", rid, r["title"],
                                         "accepted rule matches nothing deployed",
                                         ev[len("NOT APPLIED: "):] + f"; a human checks the deployment against "
                                         f"{r['page']} and decides whether the rule still fits"))
                    continue
                out.append(F.finding("DEC-201", "blocking", rid, item, f"breaks {rid} «{r['title']}»", ev,
                                     " ".join(str(r["decision"]).split())))
        named = {t for r in rules.values() for t in (r.get("check") or {}).get("item_names", {})}
        if named:
            for t in sorted({i["type"] for i in st["items"]} - named):
                out.append(F.finding("DEC-202", "info", "-", t, f"no naming pattern for item type {t}",
                                     f"the rules name {', '.join(sorted(named))}"))
    except SystemExit:
        raise
    except Exception as e:   # a crash must become a finding, not a missing reviewer
        sys.exit(F.write("rules", me, [F.finding("DEC-200", "blocking", "-", f.WS_NAME, "rules review failed",
                                                 f"{type(e).__name__}: {str(e)[:300]}")], [f"{rel}/"]))
    checks = sum(1 for r in rules.values() if r.get("check"))
    skipped = len(every) - len(rules)
    sys.exit(F.write("rules", me, out, [f"{len(rules)} accepted rule(s) from {rel}/ ({checks} with a machine "
                                        "check" + (f", {skipped} not accepted, skipped" if skipped else "") + ")",
                                        f"{len(st['items'])} item(s), {len(st['models'])} model(s)"]))


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--lint":
        sys.exit(lint(sys.argv[2]))
    review()


if __name__ == "__main__":
    main()
