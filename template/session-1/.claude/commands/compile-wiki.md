---
description: Compile the project wiki from the decision log, the review and the human decisions.
disable-model-invocation: true
---
Compile the project wiki of this delivery. Your inputs, and nothing else:

- the decision log: every page in the wiki (`wiki_list`, `wiki_read`), including the pages tagged
  `decided-by-human`
- the review: `../review/reports/latest-gate.md`, and `../review/reports/run/*.json` for the facts and the
  evidence
- the signed baseline: `../review/reports/baseline.json`

Write every text yourself, from these inputs only. Page content starts with its first section: the wiki adds
the title as heading. Issue independent tool calls in parallel.

1. **ADR pages**, one per accepted decision: decision pages that decide the same thing become one ADR; every
   decision page goes into exactly one ADR. `wiki_add`, title `ADR-001 <short title>` (numbered), category
   `architecture`, tags `adr`. Sections: Status (accepted, decided by whom), Context, Decision, Why,
   Alternatives considered, Sources (Microsoft Learn URLs), Evidence from the review (fact ids, what the
   reviewer read, finding ids), Decision log (page files), Rule (`rules/<file>` or "no machine check").
2. **SEC pages**, one per security finding of the review (SEC-*): `wiki_add`, title `SEC-nnn <short title>`,
   category `reference`, tags `sec`. What the reviewer found, the evidence, what it means, who acts.
3. **DRF page**, one per drift finding of the review (DRF-*), with the signed baseline: `wiki_add`, title
   `DRF-nnn <short title>`, category `reference`, tags `drf`. What was signed, by whom, when, which items and
   how many definition parts; how drift is detected.
4. **Rules** for the next review: one file `rules/<ADR id>-<slug>.yaml` (Write tool) per ADR whose decision
   one of these check kinds expresses. An ADR that none expresses gets no rule file.

   ```yaml
   id: ADR-001
   title: <as on the page>
   status: accepted
   decided_by: <the session, or the human>
   decision: <one paragraph>
   page: <the ADR page's file name>
   sources: [<Microsoft Learn URL>]
   check:                             # one or more of these kinds, nothing else
     item_names: {<Fabric item type, e.g. Lakehouse, SemanticModel, Report, Notebook>: <regex for the whole name>}
     storage_mode: direct_lake_onelake | direct_lake_sql | import
     rls: {table_with_columns: [<column>], filter_contains: <text the filter contains>, min_members: <n>}
     lakehouse_schemas: true | false
   ```
5. Run `./py ../review/gate/check_rules.py --lint rules` and fix the files until it reports 0 errors.

End with one line per page and per rule file.
