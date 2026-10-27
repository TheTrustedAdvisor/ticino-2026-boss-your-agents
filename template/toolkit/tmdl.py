"""A small, tolerant TMDL reader: tables, columns, partitions, expressions and roles of a semantic model.

Used to lint a model folder before deploy and to read a deployed definition. Input is
{part path: text}, the shape of a Fabric definition (definition/model.tmdl, definition/tables/x.tmdl, ...).
It reads what the checks need; it is not a full TMDL parser.
TMDL reference: https://learn.microsoft.com/analysis-services/tmdl/tmdl-overview
"""
import re

TMDL_TYPES = {"int64", "string", "double", "decimal", "dateTime", "boolean", "binary", "variant"}
# Delta type (from the table's _delta_log schemaString) -> TMDL dataType
DELTA_TO_TMDL = {"long": "int64", "integer": "int64", "short": "int64", "byte": "int64", "string": "string",
                 "double": "double", "float": "double", "boolean": "boolean", "date": "dateTime",
                 "timestamp": "dateTime", "timestamp_ntz": "dateTime", "binary": "binary"}


def delta_to_tmdl(t):
    return "decimal" if str(t).startswith("decimal") else DELTA_TO_TMDL.get(str(t), "?")


_UNIT = [4]   # spaces per level of the file being read (tabs are one level; Fabric accepts both, measured 2026-10-27)


def _indent(line):
    tabs = len(line) - len(line.lstrip("\t"))
    rest = line[tabs:]
    spaces = len(rest) - len(rest.lstrip(" "))
    return tabs + spaces // _UNIT[0]


def _name(rest):
    """Object name at the start of `rest`: 'quoted name' or a bare token. Returns (name, remainder)."""
    rest = rest.strip()
    if rest.startswith("'"):
        m = re.match(r"'((?:[^']|'')*)'(.*)$", rest)
        if m:
            return m.group(1).replace("''", "'"), m.group(2)
    m = re.match(r"([^\s=.]+)(.*)$", rest)
    return (m.group(1), m.group(2)) if m else ("", rest)


def _prop(line):
    m = re.match(r"\s*(\w+)\s*:\s*(.*?)\s*$", line)
    return (m.group(1), m.group(2).strip().strip("'")) if m else (None, None)


def parse(parts):
    """{path: text} -> model dict: tables, expressions, roles, refs, problems."""
    model = {"tables": {}, "expressions": {}, "roles": {}, "relationships": [], "refs": [], "problems": []}
    for path, text in sorted(parts.items()):
        if not path.endswith(".tmdl"):
            continue
        lines = text.replace("\r\n", "\n").split("\n")
        widths = [len(x) - len(x.lstrip(" ")) for x in lines if x.startswith(" ") and x.strip()]
        _UNIT[0] = min(widths) if widths else 4
        _parse_file(path, lines, model)
    return model


def _block(lines, start, base):
    """Lines after `start` that are indented deeper than `base` (blank lines included)."""
    out = []
    for line in lines[start + 1:]:
        if line.strip() and _indent(line) <= base:
            break
        out.append(line)
    return out


def _parse_file(path, lines, model):
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        ind = _indent(line)
        if not s or s.startswith("///"):
            i += 1
            continue
        if ind == 0 and s.startswith("ref table "):
            model["refs"].append(_name(s[len("ref table "):])[0])
        elif ind == 0 and s.startswith("table "):
            name, _ = _name(s[6:])
            model["tables"][name] = _table(name, lines, i, path)
        elif ind == 0 and s.startswith("expression "):
            name, rest = _name(s[len("expression "):])
            body = [rest.split("=", 1)[1].strip()] if "=" in rest else []
            body += [x.strip() for x in _block(lines, i, 0)]
            model["expressions"][name] = "\n".join(x for x in body if x and x != "```")
        elif ind == 0 and s.startswith("relationship "):
            rel = {}
            for sub in _block(lines, i, 0):
                m = re.match(r"\s*(fromColumn|toColumn)\s*:\s*(.*?)\s*$", sub)
                if m:
                    rel[m.group(1)] = m.group(2)
                    rel["from" if m.group(1) == "fromColumn" else "to"] = _name(m.group(2))[0]
            if rel.get("from") and rel.get("to"):
                model["relationships"].append(rel)
        elif ind == 0 and s.startswith("role "):
            name, _ = _name(s[5:])
            model["roles"][name] = _role(lines, i)
        i += 1


def _table(name, lines, start, path):
    t = {"name": name, "path": path, "columns": {}, "measures": [], "partitions": []}
    body = _block(lines, start, 0)
    j = 0
    while j < len(body):
        line = body[j]
        s = line.strip()
        if _indent(line) == 1 and s.startswith("column "):
            cname, rest = _name(s[7:])
            col = {"name": cname, "dataType": None, "sourceColumn": None, "calculated": "=" in rest}
            for sub in _block(body, j, 1):
                k, v = _prop(sub)
                if k in ("dataType", "sourceColumn"):
                    col[k] = v
            t["columns"][cname] = col
        elif _indent(line) == 1 and s.startswith("measure "):
            t["measures"].append(_name(s[8:])[0])
        elif _indent(line) == 1 and s.startswith("partition "):
            pname, rest = _name(s[10:])
            p = {"name": pname, "kind": rest.split("=", 1)[1].strip() if "=" in rest else "", "mode": None,
                 "entityName": None, "schemaName": None, "expressionSource": None}
            for sub in _block(body, j, 1):
                k, v = _prop(sub)
                if k in ("mode", "entityName", "schemaName", "expressionSource"):
                    p[k] = v
            t["partitions"].append(p)
        j += 1
    return t


def _role(lines, start):
    r = {"modelPermission": None, "filters": {}}
    body = _block(lines, start, 0)
    for n, line in enumerate(body):
        s = line.strip()
        k, v = _prop(line)
        if k == "modelPermission":
            r["modelPermission"] = v
        m = re.match(r"tablePermission\s+(.*)$", s)
        if m and _indent(line) == 1:
            table, rest = _name(m.group(1))
            expr = rest.split("=", 1)[1].strip() if "=" in rest else ""
            if expr in ("", "```"):   # multi-line filter: the indented block below
                expr = " ".join(x.strip() for x in _block(body, n, 1) if x.strip() and x.strip() != "```")
            r["filters"][table] = expr
    return r


def lakehouse_ref(expr):
    """Which lakehouse an M expression points at: ('sql', endpoint id) or ('onelake', ws, item) or None."""
    m = re.search(r'Sql\.Database\(\s*"([^"]*)"\s*,\s*"([^"]*)"', expr or "")
    if m:
        return ("sql", m.group(2).lower())
    m = re.search(r'onelake\.dfs\.fabric\.microsoft\.com/([^/"]+)/([^/"]+)', expr or "", re.I)
    if m:
        return ("onelake", m.group(1).lower(), m.group(2).lower())
    return None
