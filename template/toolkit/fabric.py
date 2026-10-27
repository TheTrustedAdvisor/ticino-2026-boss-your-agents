"""Fabric REST access under one identity per role, bound to one workspace.

Everything comes from the folder's `.lab-env` (written by stage.sh), never from an agent:

    WORKSPACE_ID=<workspace id>          every call goes to this one workspace
    WORKSPACE_NAME=<display name>        for reports only
    BUILDER_UPN=builder@contoso.example  for reports only
    TOKEN_CMD_BUILDER=<shell command>    prints an access token for $RESOURCE as the builder identity
    REVIEWER_UPN=reviewer@contoso.example
    TOKEN_CMD_REVIEWER=<shell command>   the same for the reviewer identity

A folder knows only the identities its agents may use: the builder folder has no TOKEN_CMD_REVIEWER, the review
folder no TOKEN_CMD_BUILDER. A typical token command keeps one Azure CLI login per identity:

    TOKEN_CMD_BUILDER=AZURE_CONFIG_DIR=$HOME/.azure-builder az account get-access-token --tenant <tenant id> --resource "$RESOURCE" --query accessToken -o tsv

Tokens are never printed.
"""
import base64
import json
import os
import subprocess
import sys
import time
import types
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _env():
    out = {}
    p = os.path.join(ROOT, ".lab-env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.rstrip("\n").split("=", 1)
                out[k] = v
    return out


ENV = _env()
FAB = "https://api.fabric.microsoft.com/v1"
PBI = "https://api.powerbi.com/v1.0/myorg"
DFS = "https://onelake.dfs.fabric.microsoft.com"
FAB_RES = "https://api.fabric.microsoft.com"
PBI_RES = "https://analysis.windows.net/powerbi/api"
STORAGE_RES = "https://storage.azure.com"

WHO = {role: {"role": role, "upn": ENV.get(f"{role.upper()}_UPN") or role}
       for role in ("builder", "reviewer") if ENV.get(f"TOKEN_CMD_{role.upper()}")}
WS = os.environ.get("WORKSPACE_ID") or ENV.get("WORKSPACE_ID") or ""
WS_NAME = ENV.get("WORKSPACE_NAME") or WS
if not WS:
    sys.exit("WORKSPACE_ID missing in .lab-env: run stage.sh")
# helper notebooks for RLS role members (rls_members.py), one per identity; not part of what an agent built
HELPERS = {("Notebook", f"rls-members-helper-{who}") for who in ("builder", "reviewer")}

_cache = {}


def token(role, resource):
    if role not in WHO:
        raise RuntimeError(f"no identity «{role}» in this folder (.lab-env has no TOKEN_CMD_{role.upper()})")
    hit = _cache.get((role, resource))
    if hit and hit[1] > time.time():
        return hit[0]
    r = subprocess.run(ENV[f"TOKEN_CMD_{role.upper()}"], shell=True, capture_output=True, text=True, timeout=60,
                       env=dict(os.environ, RESOURCE=resource))
    tok = r.stdout.strip().splitlines()[-1] if r.returncode == 0 and r.stdout.strip() else ""
    if not tok:
        raise RuntimeError(f"token command for {role} failed (exit {r.returncode}): {r.stderr.strip()[:200]}")
    _cache[(role, resource)] = (tok, time.time() + 20 * 60)
    return tok


def _http(method, url, role, resource=FAB_RES, body=None, headers=None, raw=None):
    """(status, parsed body, response headers). Errors come back, not raise. 429 is retried."""
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    for _ in range(6):
        hdr = {"Authorization": f"Bearer {token(role, resource)}"}
        if body is not None:
            hdr["Content-Type"] = "application/json"
        hdr.update(headers or {})
        req = urllib.request.Request(url, data=data, method=method, headers=hdr)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                content = r.read()
                parsed = {}
                if content and content.strip() != b"null":   # a 202 can carry the body `null`
                    try:
                        parsed = json.loads(content)
                    except ValueError:
                        parsed = content
                return r.status, parsed, dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                return e.code, e.read().decode(errors="replace")[:1500], dict(e.headers)
            wait = int(e.headers.get("Retry-After") or 0) or 30
            print(f"  429 throttled, waiting {wait} s")
            time.sleep(min(wait, 120))
    return 429, "throttled", {}


def call(method, url, as_, body=None, resource=FAB_RES, headers=None, raw=None):
    return _http(method, url, as_, resource=resource, body=body, headers=headers, raw=raw)


def dfs(method, path, data=None, query=None, headers=None, who=None):
    """OneLake DFS call as `who` (an entry of WHO)."""
    url = f"{DFS}/{path}" + (("?" + urllib.parse.urlencode(query)) if query else "")
    h = {"x-ms-version": "2023-11-03"}
    h.update(headers or {})
    return _http(method, url, who["role"], resource=STORAGE_RES, raw=data, headers=h)


c = types.SimpleNamespace(dfs=dfs)   # fab.py and rls_members.py call f.c.dfs(...)


def err_text(b):
    """Fabric error body -> one readable line (errorCode, message, moreDetails)."""
    if isinstance(b, (bytes, str)):
        try:
            b = json.loads(b)
        except ValueError:
            return str(b)[:600]
    if not isinstance(b, dict):
        return str(b)[:600]
    e = b.get("error") if isinstance(b.get("error"), dict) else b
    parts = [str(e.get("errorCode") or e.get("code") or ""), str(e.get("message") or "")]
    for d in e.get("moreDetails") or e.get("details") or []:
        parts.append(f"{d.get('errorCode') or d.get('code') or ''}: {d.get('message') or ''}")
    return " | ".join(p for p in parts if p.strip())[:1500] or json.dumps(b)[:600]


def lro(s, b, h, as_, label):
    """Wait for a long-running operation as the same identity; returns the result body (or {})."""
    if s in (200, 201):
        return b
    if s != 202:
        raise RuntimeError(f"{label}: HTTP {s} {err_text(b)}")
    loc = h.get("Location") or h.get("location")
    if not loc:
        return {}
    for _ in range(180):
        time.sleep(min(int(h.get("Retry-After", 2) or 2), 5))
        s2, b2, _ = call("GET", loc, as_)
        st = b2.get("status") if isinstance(b2, dict) else None
        if st == "Succeeded":
            s3, res, _ = call("GET", loc.rstrip("/") + "/result", as_)
            return res if s3 == 200 else b2
        if st == "Failed":
            raise RuntimeError(f"{label} failed: {err_text(b2)}")
    raise RuntimeError(f"{label}: timeout")


def items(as_, typ=None):
    s, b, _ = call("GET", f"{FAB}/workspaces/{WS}/items" + (f"?type={typ}" if typ else ""), as_)
    if s != 200:
        raise RuntimeError(f"list items: HTTP {s} {err_text(b)}")
    return b.get("value", [])


def built_items(as_):
    """What an agent built: every item except auto-created SQL endpoints and the RLS helper notebooks."""
    return [i for i in items(as_) if i["type"] != "SQLEndpoint" and (i["type"], i["displayName"]) not in HELPERS]


def definition(as_, item):
    """{path: text} of an item's definition (getDefinition, LRO). Needs read and write on the item."""
    path = {"SemanticModel": "semanticModels", "Report": "reports", "Notebook": "notebooks"}.get(item["type"], "items")
    s, b, h = call("POST", f"{FAB}/workspaces/{WS}/{path}/{item['id']}/getDefinition", as_)
    res = lro(s, b, h, as_, f"getDefinition {item['displayName']}")
    return {p["path"]: base64.b64decode(p["payload"]).decode("utf-8", "replace")
            for p in res["definition"]["parts"]}


def workspace_roles(as_):
    s, b, _ = call("GET", f"{FAB}/workspaces/{WS}/roleAssignments", as_)
    if s != 200:
        return None, f"HTTP {s} {err_text(b)}"
    return [{"principal": r["principal"].get("userDetails", {}).get("userPrincipalName")
             or r["principal"].get("displayName"), "type": r["principal"]["type"], "role": r["role"]}
            for r in b.get("value", [])], None


def b64(text):
    return base64.b64encode(text.encode("utf-8") if isinstance(text, str) else text).decode()
