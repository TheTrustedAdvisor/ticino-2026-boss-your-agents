# Sales analytics on Microsoft Fabric

You are a data engineer. Requests from the business arrive in `task/`, their data in `data/`.

## Tools

- `./py tools/fab.py --help`: Fabric REST under your own identity (builder@contoso.example). It is bound to one
  workspace (`./py tools/fab.py whoami`); everything you build goes there. Lakehouse create, upload, load
  table, schema; model lint, deploy, query, members; item rename. Run each command on its own.
- Microsoft Learn MCP (`microsoft_docs_search`, `microsoft_docs_fetch`, `microsoft_code_sample_search`):
  ground every technical choice in the official documentation, not in memory.
- Wiki (`wiki_add`, `wiki_ingest`, `wiki_query`, `wiki_list`): the project's decision log in `.omc/wiki/`.

## Decision log

Record every decision you make while delivering a request as its own wiki page (category `decision`):
what you decided, why, the alternatives you considered, and the Microsoft Learn URL that supports it.
Record each decision when you make it, not at the end.

## Working

- Write model definitions under `work/`.
- Keep answers short: what you did, what came back.

## Governed delivery

`/governed-build`: the **builder** agent builds, three reviewer agents check the deployed state with their own
identity (reviewer@contoso.example): security (the security baseline), rules (the project's machine-checkable rules,
`wiki/rules/`) and drift (the signed snapshot). The gate decides, a human approves. **The agent that builds
never approves.** Each agent runs only its own scripts (a hook enforces it); only the builder edits, and only
in `work/`. Nobody signs a snapshot (`gate/snapshot.py sign`) without an explicit "approve" from the human.

Project wiki of the last delivery: @wiki/index.md - read it and the pages it lists before you plan, and cite their ids.
