"""RLS roles, members and filters of a semantic model, read or set over XMLA from inside Fabric.

    run("list", model, as_=<identity>)
    run("add", model, role, member, as_=<identity>)

Why a notebook (measured 2026-10-18): role members are not part of a model's public definition
(getDefinition leaves them out, updateDefinition drops them), there is no REST API for them, and the XMLA
client libraries refused every token from Linux ("Authentication failed for all authenticators"). Inside
Fabric, sempy's TOM connection works. The notebook runs AS the calling identity (job API with that
identity's token), so every caller reads and writes with its own rights.
About 40 to 55 s per call on the F2. The result goes through a file in a lakehouse of the workspace (any
lakehouse: the agent chose its name), read back with the caller's identity and deleted.
"""
import json
import time
import uuid

import fabric as f

NB = "rls-members-helper-{}"   # one per identity, definition rewritten by the caller before every run
CODE = r'''
import json, traceback
out = {"ok": False, "action": action, "model": model}
try:
    import sempy.fabric as fabric
    server = fabric.create_tom_server(readonly=(action == "list"))   # loads the TOM assemblies
    import Microsoft.AnalysisServices.Tabular as TOM
    db = server.Databases.Find(model_id) if model_id else None    # by id: a renamed model lags by name
    if db is None:
        db = server.Databases.GetByName(model)
    m = db.Model
    if action == "add":
        r = m.Roles.Find(role)
        if r is None:
            raise ValueError(f"role {role} not found in the deployed model (deploy the role first)")
        if not any(x.MemberName.lower() == member.lower() for x in r.Members):
            rm = TOM.ExternalModelRoleMember()
            rm.MemberName = member
            rm.IdentityProvider = "AzureAD"
            rm.MemberType = TOM.RoleMemberType.User
            r.Members.Add(rm)
            m.SaveChanges()
            out["added"] = member
        else:
            out["exists"] = member
    out["roles"] = [{"name": r.Name, "members": [x.MemberName for x in r.Members],
                     "filters": {t.Table.Name: t.FilterExpression for t in r.TablePermissions}} for r in m.Roles]
    out["ok"] = True
except Exception:
    out["error"] = traceback.format_exc()[-2500:]
notebookutils.fs.put(target, json.dumps(out), True)
'''
PARAMS = 'action = "list"\nmodel = ""\nmodel_id = ""\nrole = ""\nmember = ""\ntarget = ""\n'


def _lakehouse(as_):
    lhs = f.items(as_, "Lakehouse")
    if not lhs:
        raise RuntimeError("role members are read and set through a notebook that needs a lakehouse in the "
                           "workspace for its result; there is none")
    return sorted(lhs, key=lambda i: i["displayName"])[0]


def ensure_notebook(as_, lh):
    nb = {"nbformat": 4, "nbformat_minor": 5,
          # a pure Python notebook (no Spark): on the F2 a Spark notebook queued behind the Livy session the
          # Load Table API leaves running (measured 2026-10-27: NotStarted for 13 min)
          "metadata": {"kernel_info": {"name": "jupyter", "jupyter_kernel_name": "python3.11"},
                       "language_info": {"name": "python"},
                       "microsoft": {"language": "python", "language_group": "jupyter_python"},
                       "dependencies": {"lakehouse": {"default_lakehouse": lh["id"],
                                                      "default_lakehouse_name": lh["displayName"],
                                                      "default_lakehouse_workspace_id": f.WS}}},
          "cells": [{"cell_type": "code", "execution_count": None, "outputs": [], "metadata": {"tags": ["parameters"]},
                     "source": PARAMS.splitlines(keepends=True)},
                    {"cell_type": "code", "execution_count": None, "outputs": [], "metadata": {},
                     "source": CODE.splitlines(keepends=True)}]}
    parts = [{"path": "notebook-content.ipynb", "payload": f.b64(json.dumps(nb)), "payloadType": "InlineBase64"}]
    name = NB.format(as_)
    hit = [i for i in f.items(as_, "Notebook") if i["displayName"] == name]
    if hit:   # never trust what is deployed: anyone with Contributor could have changed it
        s, b, h = f.call("POST", f"{f.FAB}/workspaces/{f.WS}/notebooks/{hit[0]['id']}/updateDefinition", as_,
                         body={"definition": {"format": "ipynb", "parts": parts}})
        f.lro(s, b, h, as_, "notebook update")
        return hit[0]["id"]
    s, b, h = f.call("POST", f"{f.FAB}/workspaces/{f.WS}/notebooks", as_,
                     body={"displayName": name, "description": "RLS role members over XMLA (helper)",
                           "definition": {"format": "ipynb", "parts": parts}})
    f.lro(s, b, h, as_, "notebook")
    for _ in range(10):
        hit = [i for i in f.items(as_, "Notebook") if i["displayName"] == name]
        if hit:
            return hit[0]["id"]
        time.sleep(3)
    raise RuntimeError(f"notebook {name} created but not listed")


def error_line(err):
    """The informative line of a .NET/Python traceback: the last exception message, not a stack frame."""
    lines = [x.strip() for x in str(err or "?").splitlines() if x.strip()]
    msgs = [x for x in lines if not x.startswith(("at ", "File ", "^", "~")) and
            ("Exception" in x or "Error" in x or "error" in x)]
    return (msgs or lines or ["?"])[-1][:600]


def run(action, model, role="", member="", as_="builder"):
    """Returns the notebook's JSON answer (dict with ok, roles, error)."""
    try:
        lh = _lakehouse(as_)
        nid = ensure_notebook(as_, lh)
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
    hit = [i for i in f.items(as_, "SemanticModel") if i["displayName"] == model]
    if not hit:
        return {"ok": False, "error": f"no semantic model named «{model}» in the workspace"}
    rel = f"Files/_rls/rls-{uuid.uuid4().hex[:12]}.json"
    target = f"abfss://{f.WS}@onelake.dfs.fabric.microsoft.com/{lh['id']}/{rel}"
    params = {k: {"value": v, "type": "string"} for k, v in
              {"action": action, "model": model, "model_id": hit[0]["id"], "role": role, "member": member,
               "target": target}.items()}
    s, b, h = f.call("POST", f"{f.FAB}/workspaces/{f.WS}/items/{nid}/jobs/instances?jobType=RunNotebook", as_,
                     body={"executionData": {"parameters": params}})
    if s != 202:
        return {"ok": False, "error": f"run notebook: HTTP {s} {f.err_text(b)}"}
    loc = h.get("Location") or h.get("location")
    j = {}
    for _ in range(90):
        time.sleep(5)
        s, j, _ = f.call("GET", loc, as_)
        if isinstance(j, dict) and j.get("status") in ("Completed", "Failed", "Cancelled", "Deduped"):
            break
    if not isinstance(j, dict) or j.get("status") != "Completed":
        return {"ok": False, "error": f"notebook {j.get('status') if isinstance(j, dict) else j}: "
                                      f"{str(j.get('failureReason') if isinstance(j, dict) else '')[:300]}"}
    who = f.WHO[as_]
    s, out, _ = f.c.dfs("GET", f"{f.WS}/{lh['id']}/{rel}", who=who)
    f.c.dfs("DELETE", f"{f.WS}/{lh['id']}/{rel}", who=who)
    if s != 200:
        return {"ok": False, "error": f"result file: HTTP {s} {str(out)[:200]}"}
    return out if isinstance(out, dict) else json.loads(out)
