"""Findings: one JSON file per reviewer in reports/run/, combined by gate.py.

A finding is blocking (stops the deployment) or info (goes into the report only). Every finding carries
evidence read from the platform with the reviewer's own identity, never from what the builder said it did.

The review of session 1 has no rules: it checks the state against session 1's decision log (DECISIONS in
.lab-env) and the security baseline. Session 2 checks against the project wiki's machine-checkable rules
(RULES in .lab-env, wiki/rules/*.yaml), written in step 4 from session 1's own material.
"""
import datetime
import json
import os

import fabric as f

ROOT = f.ROOT
RUN = os.path.join(ROOT, "reports", "run")
RULES = os.path.join(ROOT, f.ENV.get("RULES", "wiki/rules"))
DECISIONS = os.path.normpath(os.path.join(ROOT, f.ENV.get("DECISIONS", ".omc/wiki")))
REVIEWERS = tuple(f.ENV.get("REVIEWERS", "security,decisions,drift").split(","))


def finding(fid, severity, rule, item, title, evidence, remediation=""):
    return {"id": fid, "severity": severity, "rule": rule, "item": item, "title": title,
            "evidence": evidence, "remediation": remediation}


def write(reviewer, identity, findings, checked, **extra):
    os.makedirs(RUN, exist_ok=True)
    doc = {"reviewer": reviewer, "identity": identity, "workspace": f.WS_NAME, "checked": checked,
           "findings": findings, **extra,
           "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
    json.dump(doc, open(os.path.join(RUN, f"{reviewer}.json"), "w"), indent=2)
    blocking = [x for x in findings if x["severity"] == "blocking"]
    for x in findings:
        print(f"{x['severity'].upper():<9}{x['id']:<9}{x['rule']:<9}{x['item']}: {x['title']}")
    print(f"{reviewer}: {len(blocking)} blocking, {len(findings) - len(blocking)} info "
          f"({', '.join(checked)})")
    return 1 if blocking else 0
