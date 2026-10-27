"""The gate: combine the reviewers' findings into one report and one decision.

    ./py gate/gate.py            # reads reports/run/*.json, writes reports/<time>-gate.md and reports/latest-gate.md

BLOCKED when any reviewer has a blocking finding or a reviewer is missing. PASSED means: ready for a human
to approve. Open questions (Q-*) never block; they go to a human, who decides them in one sentence each.
The gate never promotes anything itself.
"""
import datetime
import json
import os
import sys

import fabric as f
import findings as F


def main():
    docs = {}
    for r in F.REVIEWERS:
        p = os.path.join(F.RUN, f"{r}.json")
        docs[r] = json.load(open(p)) if os.path.exists(p) else None
    missing = [r for r, d in docs.items() if d is None]
    allf = [dict(x, reviewer=r) for r, d in docs.items() if d for x in d["findings"]]
    blocking = [x for x in allf if x["severity"] == "blocking"]
    questions = [x for x in allf if x["severity"] == "info" and x["id"].startswith("Q-")]
    info = [x for x in allf if x["severity"] == "info" and not x["id"].startswith("Q-")]
    verdict = "BLOCKED" if blocking or missing else "PASSED"
    now = datetime.datetime.now()
    L = [f"# Gate report: {verdict}", "",
         f"{now:%Y-%m-%d %H:%M} · workspace {f.WS_NAME} · {len(blocking)} blocking, {len(questions)} open "
         f"question(s), {len(info)} info", ""]
    if missing:
        L += [f"> Missing reviewer(s): {', '.join(missing)}. The gate does not pass without every review.", ""]
    L += ["| Reviewer | Identity | Checked | Blocking |", "|---|---|---|---|"]
    for r, d in docs.items():
        if d:
            L.append(f"| {r} | {d['identity']} | {'; '.join(d['checked'])} | "
                     f"{sum(1 for x in d['findings'] if x['severity'] == 'blocking')} |")
    for head, group in (("Blocking", blocking), ("Open questions (a human decides)", questions), ("Info", info)):
        if group:
            L += ["", f"## {head}", ""]
            for x in group:
                L += [f"### {x['id']} · {x['rule']} · {x['item']}", "", f"**{x['title']}**", "",
                      f"- Evidence: {x['evidence']}"]
                if x.get("remediation"):
                    L.append(f"- Remediation: {' '.join(str(x['remediation']).split())}")
                L.append(f"- Reviewer: {x['reviewer']}")
                L.append("")
    nxt = ("the builder remediates, then every reviewer runs again." if verdict == "BLOCKED" else
           "a human answers the open questions (one sentence each) and approves; then `./py gate/snapshot.py sign` "
           "records the approved state." if questions else
           "a human approves; then `./py gate/snapshot.py sign` records the approved state.")
    L += ["", "Next: " + nxt]
    text = "\n".join(L) + "\n"
    path = os.path.join(F.ROOT, "reports", f"{now:%Y%m%d-%H%M%S}-gate.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(text)
    open(os.path.join(F.ROOT, "reports", "latest-gate.md"), "w").write(text)
    print(text)
    print(f"{verdict} -> {os.path.relpath(path, F.ROOT)}")
    sys.exit(1 if verdict == "BLOCKED" else 0)


if __name__ == "__main__":
    main()
