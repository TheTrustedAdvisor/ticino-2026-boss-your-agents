"""Builder toolkit: Fabric REST under the builder identity, bound to one workspace.

    ./py tools/fab.py whoami
    ./py tools/fab.py items
    ./py tools/fab.py lakehouse create <name> [--schemas]
    ./py tools/fab.py lakehouse show <name>
    ./py tools/fab.py lakehouse upload <name> <local file> [--to Files/<path>]
    ./py tools/fab.py lakehouse load-table <name> <table> --from Files/<path> [--schema <s>] [--mode Overwrite|Append]
                                           [--engine onelake|spark]
    ./py tools/fab.py lakehouse schema <name> <table> [--schema <s>]
    ./py tools/fab.py model lint <folder>
    ./py tools/fab.py model deploy <folder> --name <name>
    ./py tools/fab.py model query <name> "<DAX query>"
    ./py tools/fab.py model members list|add --name <model> [--role <role> --member <upn>]
    ./py tools/fab.py item rename --type <Type> --from <old> --to <new>

A model folder holds the item definition as Fabric expects it: <folder>/definition.pbism and
<folder>/definition/*.tmdl (model.tmdl, tables/*.tmdl, optional expressions.tmdl, relationships.tmdl,
roles/*.tmdl). See https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/semantic-model-definition

`lakehouse load-table` writes the Delta table directly over OneLake (pyarrow, no Spark) unless --engine spark
asks for the Load Table API (https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table): on the F2
its Spark session stays up for 20+ minutes and every further load gets HTTP 430 (measured 2026-10-27).

`model deploy` lints, checks every Direct Lake column against the Delta table it reads, creates or updates the
item, refreshes it and runs a DAX row count per table. It says Succeeded only when every table answers.
The toolkit never creates workspaces and cannot reach another workspace.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fabric as f  # noqa: E402
import tmdl  # noqa: E402

AS = "builder"
LEARN = {
    "load": "https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table",
    "schemas": "https://learn.microsoft.com/fabric/data-engineering/lakehouse-api#list-the-tables-in-a-lakehouse",
    "definition": "https://learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/semantic-model-definition",
    "directlake": "https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop",
    "tmdl": "https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview",
}


def die(msg, hint=None, learn=None):
    print(f"ERROR  {msg}", file=sys.stderr)
    if hint:
        print(f"HINT   {hint}", file=sys.stderr)
    if learn:
        print(f"LEARN  {LEARN.get(learn, learn)}", file=sys.stderr)
    sys.exit(1)


def call(method, url, **kw):
    return f.call(method, url, AS, **kw)


# ------------------------------------------------------------------------------------------- lakehouse

def lakehouse(name):
    hit = [i for i in f.items(AS, "Lakehouse") if i["displayName"] == name]
    if not hit:
        have = [i["displayName"] for i in f.items(AS, "Lakehouse")]
        die(f"no lakehouse named «{name}» in {f.WS_NAME}", f"lakehouses here: {', '.join(have) or 'none'}")
    s, b, _ = call("GET", f"{f.FAB}/workspaces/{f.WS}/lakehouses/{hit[0]['id']}")
    if s != 200:
        die(f"read lakehouse {name}: HTTP {s} {f.err_text(b)}")
    return b


def lakehouse_create(a):
    if [i for i in f.items(AS, "Lakehouse") if i["displayName"] == a.name]:
        print(f"exists   Lakehouse {a.name}")
        return lakehouse_show(a)
    body = {"displayName": a.name}
    if a.schemas:
        body["creationPayload"] = {"enableSchemas": True}
    for attempt in range(8):
        s, b, h = call("POST", f"{f.FAB}/workspaces/{f.WS}/lakehouses", body=body)
        if s == 409 and "NotAvailableYet" in str(b) or s >= 500:   # measured 2026-10-10: 500, then 409
            print(f"  lakehouse create HTTP {s}, retry in 20 s")
            time.sleep(20)
            continue
        if s not in (200, 201, 202):
            die(f"create lakehouse «{a.name}»: HTTP {s} {f.err_text(b)}",
                "lakehouse names: letters, digits and underscores, starting with a letter")
        f.lro(s, b, h, AS, f"create {a.name}")
        break
    print(f"created  Lakehouse {a.name}" + (" (schemas enabled)" if a.schemas else ""))
    for _ in range(40):   # the SQL analytics endpoint comes a little later; a Direct Lake model needs its id
        lh = lakehouse(a.name)
        sep = (lh.get("properties") or {}).get("sqlEndpointProperties") or {}
        if sep.get("provisioningStatus") == "Success":
            break
        time.sleep(10)
    return lakehouse_show(a)


def schemas_enabled(lh):
    return bool((lh.get("properties") or {}).get("defaultSchema"))


def table_dir(lh, table, schema):
    if schemas_enabled(lh):
        return f"Tables/{schema or lh['properties']['defaultSchema']}/{table}"
    if schema:
        die(f"lakehouse {lh['displayName']} has no schemas; drop --schema", learn="schemas")
    return f"Tables/{table}"


def delta_schema(lh, tdir):
    """Columns of a Delta table from its transaction log (last metaData action wins)."""
    s, b, _ = f.c.dfs("GET", f.WS, query={"resource": "filesystem", "recursive": "false",
                                          "directory": f"{lh['id']}/{tdir}/_delta_log"}, who=f.WHO[AS])
    if s != 200:
        return None
    logs = sorted(p["name"] for p in b.get("paths", []) if p["name"].endswith(".json"))
    meta = None
    for p in logs:
        s, txt, _ = f.c.dfs("GET", f"{f.WS}/{p}", who=f.WHO[AS])
        if isinstance(txt, (bytes, bytearray)):
            raw = bytes(txt)
        else:   # a one-line log comes back parsed
            raw = (json.dumps(txt) if isinstance(txt, dict) else str(txt)).encode()
        for line in raw.decode("utf-8", "replace").splitlines():
            try:
                act = json.loads(line)
            except ValueError:
                continue
            if "metaData" in act:
                meta = act["metaData"]
    if not meta:
        return None
    return [(c["name"], c["type"] if isinstance(c["type"], str) else "struct")
            for c in json.loads(meta["schemaString"])["fields"]]


def list_tables(lh):
    if schemas_enabled(lh):
        out = []
        s, b, _ = f.c.dfs("GET", f.WS, query={"resource": "filesystem", "recursive": "false",
                                              "directory": f"{lh['id']}/Tables"}, who=f.WHO[AS])
        for sch in (b.get("paths", []) if s == 200 else []):
            s2, b2, _ = f.c.dfs("GET", f.WS, query={"resource": "filesystem", "recursive": "false",
                                                    "directory": sch["name"]}, who=f.WHO[AS])
            for t in (b2.get("paths", []) if s2 == 200 else []):
                out.append((sch["name"].split("/")[-1], t["name"].split("/")[-1]))
        return out
    s, b, _ = call("GET", f"{f.FAB}/workspaces/{f.WS}/lakehouses/{lh['id']}/tables")
    return [(None, t["name"]) for t in (b.get("data", []) if s == 200 else [])]


def lakehouse_show(a):
    lh = lakehouse(a.name)
    p = lh.get("properties") or {}
    sep = p.get("sqlEndpointProperties") or {}
    print(f"lakehouse        {lh['displayName']}  id {lh['id']}")
    print(f"workspace        {f.WS_NAME}  id {f.WS}")
    print(f"schemas          {'enabled, default ' + p['defaultSchema'] if p.get('defaultSchema') else 'not enabled'}")
    print(f"OneLake tables   {p.get('oneLakeTablesPath')}")
    print(f"OneLake files    {p.get('oneLakeFilesPath')}")
    print(f"SQL endpoint     id {sep.get('id')}  status {sep.get('provisioningStatus')}")
    print(f"SQL connection   {sep.get('connectionString')}")
    tabs = list_tables(lh)
    print(f"tables           {', '.join((s + '.' if s else '') + t for s, t in tabs) or 'none'}")


def put_bytes(lh, rel, data):
    """OneLake DFS create -> append -> flush, as the builder. An unflushed file is zero bytes."""
    p = f"{f.WS}/{lh['id']}/{rel}"
    who = f.WHO[AS]
    s, b, _ = f.c.dfs("PUT", p, query={"resource": "file", "overwrite": "true"}, data=b"", who=who)
    if s not in (200, 201):
        die(f"create {rel}: HTTP {s} {f.err_text(b)}")
    if data:
        s, b, _ = f.c.dfs("PATCH", p, data=data, query={"action": "append", "position": "0"},
                          headers={"Content-Type": "application/octet-stream"}, who=who)
        if s not in (200, 202):
            die(f"append {rel}: HTTP {s} {f.err_text(b)}")
    s, b, _ = f.c.dfs("PATCH", p, data=b"", query={"action": "flush", "position": str(len(data))}, who=who)
    if s not in (200, 201):
        die(f"flush {rel}: HTTP {s} {f.err_text(b)}")


def lakehouse_upload(a):
    lh = lakehouse(a.name)
    if not os.path.isfile(a.file):
        die(f"no such file: {a.file}")
    rel = a.to or f"Files/{os.path.basename(a.file)}"
    if not rel.startswith("Files/"):
        die(f"--to must start with Files/ (got {rel})", "files go into the Files area; tables are loaded from there")
    data = open(a.file, "rb").read()
    put_bytes(lh, rel, data)
    print(f"uploaded {a.file} -> {lh['displayName']}/{rel} ({len(data)} bytes)")


ARROW_TO_DELTA = {"int64": "long", "int32": "integer", "int16": "short", "int8": "byte", "double": "double",
                  "float": "float", "string": "string", "large_string": "string", "bool": "boolean",
                  "date32[day]": "date"}


def write_delta(lh, tdir, src, mode):
    """CSV or Parquet file in Files/ -> Delta table in Tables/, written over OneLake without Spark.

    One Parquet file plus a commit in _delta_log, the Delta protocol the lakehouse discovers by itself
    (https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview#automatic-table-discovery-and-registration).
    Types are inferred from the file (pyarrow); the result is printed with the TMDL dataType to use."""
    import io
    import uuid
    import pyarrow as pa
    import pyarrow.csv as pcsv
    import pyarrow.parquet as pq
    s, raw, _ = f.c.dfs("GET", f"{f.WS}/{lh['id']}/{src}", who=f.WHO[AS])
    if s != 200:
        die(f"read {src}: HTTP {s}", "the path is case sensitive and must exist: lakehouse upload first")
    raw = raw if isinstance(raw, (bytes, bytearray)) else (json.dumps(raw) if isinstance(raw, (dict, list)) else str(raw)).encode()
    t = pq.read_table(io.BytesIO(raw)) if src.lower().endswith(".parquet") else pcsv.read_csv(io.BytesIO(raw))
    cols = []
    for fld in t.schema:   # normalize to types Delta and Direct Lake read without extra table features
        typ = str(fld.type)
        if typ == "null":
            t = t.set_column(t.schema.get_field_index(fld.name), fld.name, t[fld.name].cast(pa.string()))
            typ = "string"
        elif typ.startswith("timestamp"):
            import pyarrow.compute as pc
            col = t[fld.name] if "tz=" in typ else pc.assume_timezone(t[fld.name], "UTC")
            t = t.set_column(t.schema.get_field_index(fld.name), fld.name, col.cast(pa.timestamp("us", tz="UTC")))
            cols.append((fld.name, "timestamp"))
            continue
        elif typ.startswith("decimal"):
            cols.append((fld.name, typ.replace("128", "").replace(" ", "")))
            continue
        if typ not in ARROW_TO_DELTA:
            die(f"column {fld.name}: type {typ} not supported here; cast it in the source file")
        cols.append((fld.name, ARROW_TO_DELTA[typ]))
    who = f.WHO[AS]
    base = f"{f.WS}/{lh['id']}/{tdir}"
    log = f.c.dfs("GET", f.WS, query={"resource": "filesystem", "recursive": "false",
                                      "directory": f"{lh['id']}/{tdir}/_delta_log"}, who=who)
    versions = sorted(x["name"] for x in (log[1].get("paths", []) if log[0] == 200 else []) if x["name"].endswith(".json"))
    if mode == "Overwrite" and versions:
        s, b, _ = f.c.dfs("DELETE", base, query={"recursive": "true"}, who=who)
        if s not in (200, 202):
            die(f"overwrite: delete {tdir}: HTTP {s} {f.err_text(b)}")
        versions = []
    if versions:   # Append: the schema must be the one the table has
        have = delta_schema(lh, tdir)
        if have and [(n, ty) for n, ty in have] != cols:
            die(f"append: the file's columns {cols} differ from the table's {have}", "use --mode Overwrite")
    buf = io.BytesIO()
    pq.write_table(t, buf, compression="snappy")
    part = f"part-00000-{uuid.uuid4()}-c000.snappy.parquet"
    put_bytes(lh, f"{tdir}/{part}", buf.getvalue())
    now = int(time.time() * 1000)
    acts = [{"commitInfo": {"timestamp": now, "operation": "WRITE", "engineInfo": "zero-to-hero fab.py",
                            "operationParameters": {"mode": mode}}}]
    if not versions:
        schema = {"type": "struct", "fields": [{"name": n, "type": ty, "nullable": True, "metadata": {}} for n, ty in cols]}
        acts += [{"protocol": {"minReaderVersion": 1, "minWriterVersion": 2}},
                 {"metaData": {"id": str(uuid.uuid4()), "format": {"provider": "parquet", "options": {}},
                               "schemaString": json.dumps(schema), "partitionColumns": [], "configuration": {},
                               "createdTime": now}}]
    acts.append({"add": {"path": part, "partitionValues": {}, "size": buf.getbuffer().nbytes, "modificationTime": now,
                         "dataChange": True, "stats": json.dumps({"numRecords": t.num_rows})}})
    put_bytes(lh, f"{tdir}/_delta_log/{len(versions):020d}.json", "\n".join(json.dumps(x) for x in acts).encode())
    return t.num_rows


def wait_registered(lh, table, schema, timeout=120):
    """The lakehouse registers a Delta table it finds under Tables/ by itself; wait until it lists it."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if any(t == table and (s or None) == (schema if schemas_enabled(lh) else None) or
               (t == table and schemas_enabled(lh) and not schema) for s, t in list_tables(lh)):
            return time.time() - t0
        time.sleep(4)
    return None


def lakehouse_load(a):
    import fcntl
    lock = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".load.lock"), "w")
    fcntl.flock(lock, fcntl.LOCK_EX)   # one load at a time (rehearsal 2: two parallel loads, one table stayed
    #                                    unreadable for Direct Lake for about 5 minutes)
    lh = lakehouse(a.name)
    tdir = table_dir(lh, a.table, a.schema)
    t0 = time.time()
    if a.engine == "onelake":
        n = write_delta(lh, tdir, a.src, a.mode)
        reg = wait_registered(lh, a.table, a.schema)
        print(f"loaded   {a.src} -> table {a.table} ({a.mode}, {n} rows, Delta over OneLake, {time.time() - t0:.0f} s"
              + (", registered by the lakehouse)" if reg is not None else ", NOT yet listed by the lakehouse after 120 s)"))
    else:
        body = {"relativePath": a.src, "pathType": "File", "mode": a.mode,
                "formatOptions": {"format": "Csv", "header": True, "delimiter": ","} if a.src.lower().endswith(".csv")
                else {"format": "Parquet"}}
        if schemas_enabled(lh):
            sch = a.schema or lh["properties"]["defaultSchema"]
            url = f"{f.FAB}/workspaces/{f.WS}/lakehouses/{lh['id']}/schemas/{sch}/tables/{a.table}/load?beta=true"
        else:
            url = f"{f.FAB}/workspaces/{f.WS}/lakehouses/{lh['id']}/tables/{a.table}/load"
        s, b, h = call("POST", url, body=body)
        try:
            f.lro(s, b, h, AS, f"load {a.table}")
        except RuntimeError as e:
            die(str(e), "430 TooManyRequestsForCapacity: the capacity's Spark is busy (a Load Table session stays "
                        "up for 20+ minutes); use the default --engine onelake", learn="load")
        print(f"loaded   {a.src} -> table {a.table} ({a.mode}, Load Table API on Spark, {time.time() - t0:.0f} s)")
    for n, t in delta_schema(lh, tdir) or []:
        print(f"  column {n:<28} delta {t:<12} -> TMDL dataType {tmdl.delta_to_tmdl(t)}")
    sep = ((lh.get("properties") or {}).get("sqlEndpointProperties") or {}).get("id")
    if sep:   # Direct Lake on SQL reads through the endpoint: make it see the new table now
        s, b, h = call("POST", f"{f.FAB}/workspaces/{f.WS}/sqlEndpoints/{sep}/refreshMetadata", body={})
        try:
            f.lro(s, b, h, AS, "SQL endpoint metadata refresh")
            print("  SQL analytics endpoint metadata refreshed")
        except RuntimeError as e:
            print(f"  note: SQL endpoint metadata refresh: {e}")


def lakehouse_schema(a):
    lh = lakehouse(a.name)
    cols = delta_schema(lh, table_dir(lh, a.table, a.schema))
    if cols is None:
        die(f"no Delta table «{a.table}» in {a.name}", f"tables: {', '.join(t for _, t in list_tables(lh)) or 'none'}")
    for n, t in cols:
        print(f"{n:<28} delta {t:<12} -> TMDL dataType {tmdl.delta_to_tmdl(t)}")


# ------------------------------------------------------------------------------------------------ model

def read_folder(folder):
    if not os.path.isdir(folder):
        die(f"no such folder: {folder}")
    parts = {}
    for base, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in sorted(files):
            full = os.path.join(base, name)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            if rel == "definition.pbism" or rel == "diagramLayout.json" or (rel.startswith("definition/") and rel.endswith(".tmdl")):
                parts[rel] = open(full, encoding="utf-8").read()
            elif not name.startswith("."):
                print(f"  note: {rel} is not a definition part and is not deployed")
    return parts


def lint(parts, online=True):
    """Returns (errors, warnings, model)."""
    errs, warns = [], []
    if "definition.pbism" not in parts:
        errs.append("definition.pbism missing (required part; for TMDL the version must be 4.0 or higher, "
                    "e.g. {\"version\": \"4.2\", \"settings\": {}})")
    else:
        try:
            v = float(str(json.loads(parts["definition.pbism"]).get("version", "0")).split(".")[0])
            if v < 4:
                errs.append("definition.pbism version < 4.0: TMDL needs 4.0 or higher")
        except ValueError:
            errs.append("definition.pbism is not valid JSON")
    if "definition/model.tmdl" not in parts:
        errs.append("definition/model.tmdl missing")
    elif "powerBI_V3" not in parts["definition/model.tmdl"]:   # measured: else "Import from JSON supported for V3 models only"
        errs.append("definition/model.tmdl: the model needs `defaultPowerBIDataSourceVersion: powerBI_V3`")
    m = tmdl.parse(parts)
    errs += m["problems"]
    if not m["tables"]:
        errs.append("no tables: put one file per table in definition/tables/<table>.tmdl starting with `table <name>`")
    for r in m["refs"]:
        if r not in m["tables"]:
            errs.append(f"model.tmdl has `ref table {r}` but no table {r} is defined")
    for t in m["tables"].values():
        if not t["partitions"]:
            errs.append(f"table {t['name']}: no partition (a Direct Lake table needs `partition <name> = entity`)")
        for c in t["columns"].values():
            if c["calculated"]:
                continue
            if c["dataType"] not in tmdl.TMDL_TYPES:
                errs.append(f"table {t['name']} column {c['name']}: dataType «{c['dataType']}» "
                            f"(one of {', '.join(sorted(tmdl.TMDL_TYPES))})")
            if not c["sourceColumn"]:
                errs.append(f"table {t['name']} column {c['name']}: no sourceColumn")
        for p in t["partitions"]:
            if p["mode"] == "directLake":
                if not p["entityName"]:
                    errs.append(f"table {t['name']}: Direct Lake partition without entityName (the Delta table name)")
                if p["expressionSource"] and p["expressionSource"] not in m["expressions"]:
                    errs.append(f"table {t['name']}: expressionSource «{p['expressionSource']}» is not an "
                                f"expression in expressions.tmdl ({', '.join(m['expressions']) or 'none'})")
                if not p["expressionSource"]:
                    errs.append(f"table {t['name']}: Direct Lake partition without expressionSource")
    for rname, r in m["roles"].items():
        for table in r["filters"]:
            if table not in m["tables"]:
                errs.append(f"role {rname}: tablePermission on unknown table {table}")
        if not r["modelPermission"]:
            warns.append(f"role {rname}: no modelPermission (read is the usual value)")
    if online and not errs:
        errs += check_sources(m)
    return errs, warns, m


def check_sources(m):
    """Every Direct Lake column against the Delta table it reads: name exists, type matches."""
    errs = []
    lhs = []
    for i in f.items(AS, "Lakehouse"):
        s, b, _ = call("GET", f"{f.FAB}/workspaces/{f.WS}/lakehouses/{i['id']}")
        if s == 200:
            lhs.append(b)
    for t in m["tables"].values():
        for p in t["partitions"]:
            if p["mode"] != "directLake":
                continue
            ref = tmdl.lakehouse_ref(m["expressions"].get(p["expressionSource"], ""))
            if not ref:
                errs.append(f"expression {p['expressionSource']}: no lakehouse found in it. Direct Lake on SQL: "
                            "Sql.Database(\"<SQL connection>\", \"<SQL endpoint id>\"); Direct Lake on OneLake: "
                            "AzureStorage.DataLake(\"https://onelake.dfs.fabric.microsoft.com/<ws id>/<lakehouse id>\") "
                            "(ids from `lakehouse show`)")
                continue
            if ref[0] == "sql":
                lh = [x for x in lhs if ((x.get("properties") or {}).get("sqlEndpointProperties") or {})
                      .get("id", "").lower() == ref[1]]
                where = f"SQL endpoint id {ref[1]}"
            else:
                lh = [x for x in lhs if x["id"].lower() == ref[2] or x["displayName"].lower() == ref[2]]
                where = f"OneLake item {ref[2]}"
                if ref[1] not in (f.WS.lower(), f.WS_NAME.lower()):
                    errs.append(f"expression {p['expressionSource']}: workspace {ref[1]} is not {f.WS_NAME} ({f.WS})")
            if not lh:
                errs.append(f"expression {p['expressionSource']}: {where} is no lakehouse in {f.WS_NAME}")
                continue
            lh = lh[0]
            sch = p["schemaName"] if schemas_enabled(lh) else None
            cols = delta_schema(lh, f"Tables/{sch}/{p['entityName']}" if sch else f"Tables/{p['entityName']}")
            if cols is None:
                errs.append(f"table {t['name']}: no Delta table «{(sch + '.') if sch else ''}{p['entityName']}» in "
                            f"lakehouse {lh['displayName']} (tables: "
                            f"{', '.join(((s + '.') if s else '') + n for s, n in list_tables(lh)) or 'none'})")
                continue
            delta = dict(cols)
            for c in t["columns"].values():
                if c["calculated"] or not c["sourceColumn"]:
                    continue
                if c["sourceColumn"] not in delta:
                    errs.append(f"table {t['name']} column {c['name']}: sourceColumn «{c['sourceColumn']}» not in "
                                f"{p['entityName']} ({', '.join(delta)})")
                elif tmdl.delta_to_tmdl(delta[c["sourceColumn"]]) != c["dataType"]:
                    errs.append(f"table {t['name']} column {c['name']}: dataType {c['dataType']}, but the Delta "
                                f"column is {delta[c['sourceColumn']]} -> use {tmdl.delta_to_tmdl(delta[c['sourceColumn']])}")
    return errs


def model_lint(a):
    errs, warns, m = lint(read_folder(a.folder))
    for w in warns:
        print(f"WARN   {w}")
    for e in errs:
        print(f"ERROR  {e}")
    if errs:
        print(f"LEARN  {LEARN['definition']}\nLEARN  {LEARN['directlake']}")
        sys.exit(1)
    print(f"lint ok: {len(m['tables'])} table(s), {len(m['roles'])} role(s), {len(m['expressions'])} expression(s)")


def model_item(name):
    hit = [i for i in f.items(AS, "SemanticModel") if i["displayName"] == name]
    return hit[0] if hit else None


def refresh(mid):
    s, b, _ = f.call("POST", f"{f.PBI}/groups/{f.WS}/datasets/{mid}/refreshes", AS, resource=f.PBI_RES,
                     body={"notifyOption": "NoNotification"})
    if s not in (200, 202):
        return f"refresh: HTTP {s} {f.err_text(b)}"
    for _ in range(60):
        time.sleep(4)
        s, b, _ = f.call("GET", f"{f.PBI}/groups/{f.WS}/datasets/{mid}/refreshes?$top=1", AS, resource=f.PBI_RES)
        r = (b.get("value") or [{}])[0] if isinstance(b, dict) else {}
        if r.get("status") == "Completed":
            return None
        if r.get("status") in ("Failed", "Cancelled", "Disabled"):
            return f"refresh {r.get('status')}: {str(r.get('serviceExceptionJson'))[:800]}"
    return "refresh: timeout"


def dax(mid, query):
    s, b, _ = f.call("POST", f"{f.PBI}/groups/{f.WS}/datasets/{mid}/executeQueries", AS, resource=f.PBI_RES,
                     body={"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}})
    if s != 200:
        return None, f"HTTP {s} {f.err_text(b)}"
    try:
        return b["results"][0]["tables"][0]["rows"], None
    except (KeyError, IndexError, TypeError):
        return None, f.err_text(b)


def model_deploy(a):
    parts = read_folder(a.folder)
    errs, warns, m = lint(parts)
    for w in warns:
        print(f"WARN   {w}")
    if errs:
        for e in errs:
            print(f"ERROR  {e}")
        print(f"LEARN  {LEARN['definition']}\nLEARN  {LEARN['directlake']}")
        sys.exit(1)
    body_parts = [{"path": p, "payload": f.b64(t), "payloadType": "InlineBase64"} for p, t in sorted(parts.items())]
    t0 = time.time()
    it = model_item(a.name)
    try:
        if it:
            s, b, h = call("POST", f"{f.FAB}/workspaces/{f.WS}/semanticModels/{it['id']}/updateDefinition",
                           body={"definition": {"parts": body_parts}})
            f.lro(s, b, h, AS, f"update {a.name}")
            verb = "updated"
        else:
            s, b, h = call("POST", f"{f.FAB}/workspaces/{f.WS}/semanticModels",
                           body={"displayName": a.name, "definition": {"parts": body_parts}})
            f.lro(s, b, h, AS, f"create {a.name}")
            verb = "created"
    except RuntimeError as e:
        die(str(e), "Fabric validates the whole TMDL; the message names the object it could not read",
            learn="definition")
    for _ in range(10):
        it = model_item(a.name)
        if it:
            break
        time.sleep(3)
    if not it:
        die(f"{a.name} deployed but not listed")
    print(f"{verb:<8} SemanticModel {a.name} ({time.time() - t0:.0f} s)")
    err = refresh(it["id"])
    t1 = time.time()
    while err and "do not exist or access was denied" in err and time.time() - t1 < 300:
        # measured 2026-10-27 (rehearsal 2): a table loaded moments before can stay unreadable for Direct Lake for
        # minutes, then reads fine without any change. Waiting is the remedy, not a new definition.
        print(f"  refresh  a source table is not readable yet; retrying for up to 5 min ({time.time() - t1:.0f} s)")
        time.sleep(20)
        err = refresh(it["id"])
    if err:
        die(f"deployed, but the model does not load: {err}", learn="directlake")
    print("  refresh  Completed")
    bad = 0
    for t in m["tables"]:
        rows, err = dax(it["id"], f"EVALUATE ROW(\"rows\", COUNTROWS('{t.replace(chr(39), chr(39) * 2)}'))")
        if err:
            bad += 1
            print(f"  query    {t}: FAILED {err}")
        else:
            print(f"  query    {t}: {list(rows[0].values())[0]} rows")
    if bad:
        die(f"{bad} table(s) do not answer a DAX query", learn="directlake")
    print(f"Succeeded ({time.time() - t0:.0f} s)")


def model_query(a):
    it = model_item(a.name) or die(f"no semantic model named «{a.name}»")
    rows, err = dax(it["id"], a.query)
    if err:
        die(err)
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def model_members(a):
    import rls_members
    if a.action == "add" and not (a.role and a.member):
        die("add needs --role and --member")
    t0 = time.time()
    out = rls_members.run(a.action, a.name, a.role or "", a.member or "", as_=AS)
    if not out.get("ok"):
        die(rls_members.error_line(out.get("error")),
            "a member must be a user (or group) of this tenant; an address that does not exist there is refused")
    for r in out.get("roles", []):
        print(f"role {r['name']}: members {', '.join(r['members']) or 'none'}; filters {r['filters']}")
    if out.get("added"):
        print(f"added {out['added']}")
    print(f"({time.time() - t0:.0f} s)")


def item_rename(a):
    hit = [i for i in f.items(AS, a.type) if i["displayName"] == a.old]
    if not hit:
        die(f"no {a.type} named «{a.old}»")
    s, b, _ = call("PATCH", f"{f.FAB}/workspaces/{f.WS}/items/{hit[0]['id']}", body={"displayName": a.new})
    if s != 200:
        die(f"rename failed: HTTP {s} {f.err_text(b)}")
    print(f"renamed  {a.type} {a.old} -> {a.new}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("whoami")
    sp.add_parser("items")
    lh = sp.add_parser("lakehouse").add_subparsers(dest="sub", required=True)
    x = lh.add_parser("create"); x.add_argument("name"); x.add_argument("--schemas", action="store_true")
    x = lh.add_parser("show"); x.add_argument("name")
    x = lh.add_parser("upload"); x.add_argument("name"); x.add_argument("file"); x.add_argument("--to")
    x = lh.add_parser("load-table"); x.add_argument("name"); x.add_argument("table")
    x.add_argument("--from", dest="src", required=True); x.add_argument("--schema")
    x.add_argument("--mode", default="Overwrite", choices=["Overwrite", "Append"])
    x.add_argument("--engine", default="onelake", choices=["onelake", "spark"],
                   help="onelake (default): write the Delta table directly, no Spark; spark: the Lakehouse Load "
                        "Table API (on an F2 its Spark session blocks further loads for 20+ minutes)")
    x = lh.add_parser("schema"); x.add_argument("name"); x.add_argument("table"); x.add_argument("--schema")
    md = sp.add_parser("model").add_subparsers(dest="sub", required=True)
    x = md.add_parser("lint"); x.add_argument("folder")
    x = md.add_parser("deploy"); x.add_argument("folder"); x.add_argument("--name", required=True)
    x = md.add_parser("query"); x.add_argument("name"); x.add_argument("query")
    x = md.add_parser("members"); x.add_argument("action", choices=["list", "add"]); x.add_argument("--name", required=True)
    x.add_argument("--role"); x.add_argument("--member")
    it = sp.add_parser("item").add_subparsers(dest="sub", required=True)
    x = it.add_parser("rename"); x.add_argument("--type", required=True)
    x.add_argument("--from", dest="old", required=True); x.add_argument("--to", dest="new", required=True)
    a = ap.parse_args()
    if a.cmd == "whoami":
        print(f"identity   {f.WHO[AS]['upn']} (builder)\nworkspace  {f.WS_NAME} ({f.WS})")
    elif a.cmd == "items":
        for i in sorted(f.items(AS), key=lambda i: (i["type"], i["displayName"])):
            print(f"{i['type']:<16} {i['displayName']:<32} {i['id']}")
    elif a.cmd == "lakehouse":
        {"create": lakehouse_create, "show": lakehouse_show, "upload": lakehouse_upload,
         "load-table": lakehouse_load, "schema": lakehouse_schema}[a.sub](a)
    elif a.cmd == "model":
        {"lint": model_lint, "deploy": model_deploy, "query": model_query, "members": model_members}[a.sub](a)
    else:
        item_rename(a)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        die(str(e))
