# Gate report: BLOCKED

2026-10-28 07:58 · workspace FF Ticino Session 2 DEV · 2 blocking, 0 open question(s), 1 info

| Reviewer | Identity | Checked | Blocking |
|---|---|---|---|
| security | reviewer@contoso.example | 1 semantic model(s): definition (getDefinition, TMDL); role members of Sales Model (XMLA, inside Fabric); Sales Model: 1 table(s) with sensitive-looking columns, rows of 1 of them filtered by a role with members (structure, not the filter's effect); Sales Model / Customers: RLS effect tested, probe reads 20 of 60 rows of [dbo].[customers] in lakehouse lh_sales through its SQL analytics endpoint (<sql-endpoint-host>...), none of another user, its own rows: 20 | 0 |
| rules | reviewer@contoso.example | 5 accepted rule(s) from wiki/rules/ (5 with a machine check); 2 item(s), 1 model(s) | 1 |
| drift | reviewer@contoso.example | snapshot signature (ssh-keygen -Y verify); 2 approved item(s) | 1 |

## Blocking

### DEC-201 · ADR-005 · Sales Model

**breaks ADR-005 «Item naming with type prefixes»**

- Evidence: SemanticModel «Sales Model» does not match ^sm_[a-z0-9]+(_[a-z0-9]+)*$; the signed snapshot approved it as «sm_sales». Decision: Items use type prefixes lh_, sm_, rpt_, nb_, lower case, underscores, so anyone can tell an item's type from its name. Applies from the next delivery; the deployed sales_lh and Sales are to be renamed then.
- Remediation: rename it back to «sm_sales», or decide a new rule (/decide) and compile the wiki again
- Reviewer: rules

### DRF-003 · - · SemanticModel/Sales Model

**changed since approval**

- Evidence: renamed from «sm_sales» to «Sales Model» (same item id). Signed snapshot of 2026-10-28T07:52, approved by Matthias Falland
- Remediation: rename it back to «sm_sales», or review the change and sign the new state
- Reviewer: drift


## Info

### SEC-010 · baseline · FF Ticino Session 2 DEV

**workspace roles not readable by the reviewer (least privilege)**

- Evidence: GET roleAssignments as reviewer@contoso.example: HTTP 403 InsufficientWorkspaceRole. RLS does not apply to Admin, Member or Contributor; a human checks who holds those roles.
- Reviewer: security


Next: apply each blocking finding's remediation (the builder, or the human who made the change), then every reviewer runs again.
