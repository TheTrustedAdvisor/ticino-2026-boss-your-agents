"""Decision reviewer: does the deployed state match the decisions the builder recorded, and
which properties of what was built has nobody decided?

    ./py gate/check_decisions.py facts     # the facts of the deployed state + every decision page, in full
    ./py gate/check_decisions.py record    # validates reports/run/decisions.draft.json -> decisions.json

`facts` reads the state (state.py, the reviewer's own identity) and numbers its properties F1, F2, ... The
decision pages come from the builder's decision log (DECISIONS in .lab-env). The reviewer agent judges each
fact against the pages and writes its verdicts to reports/run/decisions.draft.json:

    {"facts": [{"fact": "F1", "verdict": "covered", "page": "<file>.md", "note": "..."},
               {"fact": "F2", "verdict": "contradicts", "page": "<file>.md", "note": "page says X, state is Y"},
               {"fact": "F3", "verdict": "open", "question": "...?", "note": "..."}]}

`record` checks the draft (every fact judged once, pages exist, contradicts and open carry a note or a
question) and turns it into findings: contradicts -> DEC-1nn blocking, open -> Q-n info (an open question
for a human, never blocking). Covered facts are listed as checked.
"""
import glob
import json
import os
import re
import sys

import yaml

import fabric as f
import findings as F
import state

ME = f.WHO["reviewer"]["upn"]
FACTS = os.path.join(F.RUN, "facts.json")
DRAFT = os.path.join(F.RUN, "decisions.draft.json")
SYSTEM = {"index.md", "log.md", "environment.md"}


def facts(st):
    out = []

    def add(subject, text):
        out.append({"id": f"F{len(out) + 1}", "subject": subject, "text": text})

    add("how items are named", "items built: " + "; ".join(f"{i['type']} «{i['name']}»" for i in st["items"]))
    for lh in st["lakehouses"]:
        add(f"lakehouse {lh['name']}: schemas or not", f"lakehouse «{lh['name']}»: schemas {'enabled' if lh['schemas'] else 'off'}")
    for m in st["models"]:
        n = m["name"]
        mode = {"direct_lake_onelake": "Direct Lake on OneLake", "direct_lake_sql": "Direct Lake on SQL endpoint",
                "import": "Import"}.get(m["storage"], m["storage"])
        add(f"model {n}: storage mode", f"model «{n}»: storage mode {mode}"
            + (f", reads lakehouse «{m['source_lakehouse']}»" if m["source_lakehouse"] else ""))
        rels = [f"{r['from']} -> {r['to']}" for r in m["relationships"]]
        add(f"model {n}: tables and relationships", f"model «{n}»: tables "
            + "; ".join(f"{t} ({', '.join(x['columns'])})" for t, x in m["tables"].items())
            + (f"; relationships {', '.join(rels)}" if rels else "; no relationships"))
        ms = [f"{t}[{x}]" for t, v in m["tables"].items() for x in v["measures"]]
        add(f"model {n}: which measures", f"model «{n}»: measures " + (", ".join(ms) if ms else "none"))
        if m["roles"]:
            add(f"model {n}: row-level security", f"model «{n}»: roles " + "; ".join(
                f"{r} ({x['modelPermission']}): " + (", ".join(f"{t} = {e}" for t, e in x["filters"].items()) or "no filter")
                for r, x in m["roles"].items()))
            mem = ("; ".join(f"{r}: {', '.join(v) or 'none'}" for r, v in m["members"].items())
                   if m["members"] is not None else f"NOT READ ({m['members_error']})")
            add(f"model {n}: who are the role members", f"model «{n}»: role members {mem}")
        else:
            add(f"model {n}: row-level security", f"model «{n}»: no row-level security roles")
    return out


def pages():
    out = {}
    for p in sorted(glob.glob(os.path.join(F.DECISIONS, "*.md"))):
        if os.path.basename(p) in SYSTEM:
            continue
        raw = open(p, encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        fm = {}
        if m:
            try:
                fm = yaml.safe_load(m.group(1)) or {}
            except yaml.YAMLError:
                fm = {}
        title = str(fm.get("title") or os.path.basename(p)[:-3])
        out[os.path.basename(p)] = {"title": title, "text": (m.group(2) if m else raw).strip()}
    return out


def cmd_facts():
    st = state.read()
    fs = facts(st)
    json.dump(fs, open(FACTS, "w"), indent=2)
    ps = pages()
    print(f"# Deployed state of {st['workspace']} (read as {st['read_by']})\n")
    for x in fs:
        print(f"{x['id']}  [{x['subject']}] {x['text']}")
    print(f"\n# Decision log: {len(ps)} page(s) in {F.DECISIONS}\n")
    for name, p in ps.items():
        print(f"=== {name}\n{p['text']}\n")
    print(f"Next: write your verdict per fact to {os.path.relpath(DRAFT, F.ROOT)}, then run "
          "./py gate/check_decisions.py record")


def cmd_record():
    if not os.path.exists(FACTS):
        sys.exit("no facts yet: run ./py gate/check_decisions.py facts first")
    fs = {x["id"]: x for x in json.load(open(FACTS))}
    ps = pages()
    try:
        draft = json.load(open(DRAFT))["facts"]
    except (OSError, ValueError, KeyError, TypeError) as e:
        sys.exit(f"draft not readable ({type(e).__name__}: {e}); expected {os.path.relpath(DRAFT, F.ROOT)} "
                 'as {"facts": [{"fact", "verdict", "page", "question", "note"}, ...]}')
    errors, seen = [], set()
    for v in draft:
        fid, verdict = v.get("fact"), v.get("verdict")
        if fid not in fs:
            errors.append(f"{fid}: no such fact")
            continue
        if fid in seen:
            errors.append(f"{fid}: judged twice")
        seen.add(fid)
        if verdict not in ("covered", "contradicts", "open"):
            errors.append(f"{fid}: verdict must be covered, contradicts or open")
        if verdict in ("covered", "contradicts") and v.get("page") not in ps:
            errors.append(f"{fid}: page «{v.get('page')}» is not in the decision log ({', '.join(ps) or 'empty'})")
        if verdict == "contradicts" and not v.get("note"):
            errors.append(f"{fid}: contradicts needs a note (what the page says, what the state is)")
        if verdict == "open" and not (v.get("question") or "").strip().endswith("?"):
            errors.append(f"{fid}: open needs a question for a human (ending in ?)")
    errors += [f"{fid}: not judged" for fid in fs if fid not in seen]
    if errors:
        sys.exit("draft rejected, fix it and run record again:\n  " + "\n  ".join(errors))
    out, covered, nd, nq = [], [], 100, 0
    for v in sorted(draft, key=lambda v: int(v["fact"][1:])):
        x = fs[v["fact"]]
        if v["verdict"] == "covered":
            covered.append(f"{x['id']} {x['subject']}: covered by «{ps[v['page']]['title']}»")
        elif v["verdict"] == "contradicts":
            nd += 1
            out.append(F.finding(f"DEC-{nd}", "blocking", v["page"][:40], x["subject"],
                                 f"deployed state contradicts the recorded decision «{ps[v['page']]['title']}»",
                                 f"{x['id']}: {x['text']}. {v['note'].rstrip('. ')}.",
                                 "change the deployment to match the decision, or record a new decision"))
        else:
            nq += 1
            out.append(F.finding(f"Q-{nq}", "info", "open", x["subject"], v["question"].strip(),
                                 f"{x['id']}: {x['text']}. "
                                 + (f"{v['note'].rstrip('. ')}. " if v.get("note") else "")
                                 + "No decision page covers it.",
                                 "a human decides (one sentence) and the decision goes into the log"))
    checked = [f"{len(fs)} fact(s) of the deployed state against {len(ps)} decision page(s)"] + covered
    sys.exit(F.write("decisions", ME, out, checked, facts=list(fs.values())))


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action not in ("facts", "record"):
        sys.exit("usage: ./py gate/check_decisions.py facts|record")
    try:
        cmd_facts() if action == "facts" else cmd_record()
    except SystemExit:
        raise
    except Exception as e:   # a crash must become a finding, not a missing reviewer
        sys.exit(F.write("decisions", ME, [F.finding("DEC-000", "blocking", "-", f.WS_NAME,
                                                     "decision review failed", f"{type(e).__name__}: {str(e)[:300]}")],
                         ["decision log"]))


if __name__ == "__main__":
    main()
