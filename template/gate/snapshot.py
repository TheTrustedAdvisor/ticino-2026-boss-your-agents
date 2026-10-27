"""Signed snapshot of the approved state, and the drift check against it.

    ./py gate/snapshot.py check     # drift reviewer (the reviewer identity)
    ./py gate/snapshot.py sign      # after human approval only (settings.json: ask); APPROVED_BY=<name> (environment
                                    # or .lab-env), default: the login name

The snapshot covers every item an agent built in the workspace: its type and name, and for items with a
definition (semantic model, report, notebook) a SHA-256 per definition part, read by the reviewer from the
platform. check records what it read (reports/run/drift.json, "reviewed"); sign signs only if the platform
still holds exactly that state, so a redeploy between PASSED and approval is not signed, and only when the
latest gate report (reports/latest-gate.md) says PASSED. Once a snapshot has
been signed for the workspace, a missing baseline blocks instead of passing.

Signed with ssh-keygen -Y (ed25519 key outside the project, ~/.config/zero-to-hero/), so an agent that
edits the snapshot file breaks the signature instead of hiding drift.
"""
import argparse
import datetime
import getpass
import hashlib
import json
import os
import subprocess
import sys

import fabric as f
import findings as F

KEYDIR = os.path.expanduser("~/.config/zero-to-hero")
KEY = os.path.join(KEYDIR, "signing_key")
SIGNERS = os.path.join(KEYDIR, "allowed_signers")
STATE = os.path.expanduser(f"~/.local/state/zero-to-hero/{f.WS}")
SNAP = os.path.join(STATE, "snapshot.json")
EVER = os.path.join(STATE, "approved-once")   # "a baseline existed once"; delete it when you empty the workspace
NS, IDENT = "zero-to-hero", "gate@zero-to-hero"
WITH_DEFINITION = ("SemanticModel", "Report", "Notebook")


def current():
    out = {}
    for i in f.built_items("reviewer"):
        parts = {}
        if i["type"] in WITH_DEFINITION:
            parts = {p: hashlib.sha256(t.encode()).hexdigest()
                     for p, t in sorted(f.definition("reviewer", i).items()) if p != ".platform"}
        out[f"{i['type']}/{i['displayName']}"] = {"id": i["id"], "parts": parts}
    return out


def ensure_key():
    if not os.path.exists(KEY):
        os.makedirs(KEYDIR, mode=0o700, exist_ok=True)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", IDENT, "-f", KEY], check=True)
        pub = open(KEY + ".pub").read().split()
        open(SIGNERS, "w").write(f'{IDENT} namespaces="{NS}" {pub[0]} {pub[1]}\n')


def sign():
    gate = os.path.join(F.ROOT, "reports", "latest-gate.md")
    head = open(gate).readline().strip() if os.path.exists(gate) else ""
    if head != "# Gate report: PASSED":
        sys.exit(f"not signed: the latest gate report is «{head or 'missing'}», not PASSED. Run the review first.")
    ensure_key()
    items = current()
    rev = os.path.join(F.RUN, "drift.json")
    reviewed = json.load(open(rev)).get("reviewed") if os.path.exists(rev) else None
    if reviewed != {k: v["parts"] for k, v in items.items()}:
        sys.exit("not signed: the deployed state is not the state the gate reviewed (changed since PASSED?). "
                 "Run the reviewers and the gate again.")
    os.makedirs(STATE, exist_ok=True)
    snap = {"workspace": f.WS_NAME, "approved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "approved_by": os.environ.get("APPROVED_BY") or f.ENV.get("APPROVED_BY") or getpass.getuser(),
            "read_by": f.WHO["reviewer"]["upn"], "items": items}
    json.dump(snap, open(SNAP, "w"), indent=2, sort_keys=True)
    if os.path.exists(SNAP + ".sig"):
        os.remove(SNAP + ".sig")
    subprocess.run(["ssh-keygen", "-q", "-Y", "sign", "-f", KEY, "-n", NS, SNAP], check=True)
    open(EVER, "w").write(snap["approved_at"] + "\n")
    n = sum(len(v["parts"]) for v in snap["items"].values())
    # the signed baseline, readable next to the gate reports (the project wiki records it as its DRF entry)
    json.dump(dict(snap, signature=open(SNAP + ".sig").read(), signed_with=f"ssh-keygen -Y sign, namespace {NS}"),
              open(os.path.join(F.ROOT, "reports", "baseline.json"), "w"), indent=2, sort_keys=True)
    print(f"snapshot signed by {snap['approved_by']}: {len(items)} items ({', '.join(sorted(items))}), "
          f"{n} definition parts -> {SNAP}, reports/baseline.json")


def check():
    me = f.WHO["reviewer"]["upn"]
    try:
        now = current()
    except Exception as e:   # a crash must become a finding, not a missing reviewer
        sys.exit(F.write("drift", me, [F.finding("DRF-005", "blocking", "-", f.WS_NAME,
                                                 "deployed definitions could not be read", str(e)[:300])],
                         ["deployed definitions"]))
    reviewed = {k: v["parts"] for k, v in now.items()}
    if not os.path.exists(SNAP):
        if os.path.exists(EVER):
            out = [F.finding("DRF-004", "blocking", "-", f.WS_NAME, "approved baseline is missing",
                             f"a snapshot was signed on {open(EVER).read().strip()[:16]} and is gone now")]
        else:
            out = [F.finding("DRF-000", "info", "-", f.WS_NAME, "no baseline yet",
                             f"no signed snapshot for this workspace; {len(now)} item(s) read, one is signed "
                             "after human approval")]
        sys.exit(F.write("drift", me, out, ["signed snapshot"], reviewed=reviewed))
    r = subprocess.run(["ssh-keygen", "-Y", "verify", "-f", SIGNERS, "-I", IDENT, "-n", NS, "-s", SNAP + ".sig"],
                       stdin=open(SNAP, "rb"), capture_output=True, text=True)
    if r.returncode != 0:
        out = [F.finding("DRF-001", "blocking", "-", "snapshot.json", "snapshot signature does not verify",
                         (r.stderr or r.stdout).strip()[:200] + ". The baseline was changed after approval.")]
        sys.exit(F.write("drift", me, out, ["snapshot signature"]))
    snap = json.load(open(SNAP))
    out = []
    for key, was in sorted(snap["items"].items()):
        cur = now.get(key)
        if not cur:
            out.append(F.finding("DRF-002", "blocking", "-", key, "approved item is gone or renamed",
                                 "not in the workspace under this name"))
            continue
        changed = [p for p in sorted(set(was["parts"]) | set(cur["parts"]))
                   if was["parts"].get(p) != cur["parts"].get(p)]
        if changed:
            out.append(F.finding("DRF-003", "blocking", "-", key, "changed since approval",
                                 f"{len(changed)} definition part(s) differ from the signed snapshot of "
                                 f"{snap['approved_at'][:16]}: {', '.join(changed)}",
                                 "re-run the gate on the change, or restore the approved definition"))
    for key in sorted(set(now) - set(snap["items"])):
        out.append(F.finding("DRF-006", "blocking", "-", key, "item added since approval",
                             f"not in the signed snapshot of {snap['approved_at'][:16]}",
                             "run the gate on the new item"))
    sys.exit(F.write("drift", me, out, ["snapshot signature (ssh-keygen -Y verify)",
                                        f"{len(snap['items'])} approved item(s)"], reviewed=reviewed))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["sign", "check"])
    a = ap.parse_args()
    sign() if a.action == "sign" else check()


if __name__ == "__main__":
    main()
