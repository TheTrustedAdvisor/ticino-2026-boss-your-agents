# Gate report: PASSED

2026-10-28 07:35 · workspace FF Ticino Session 1 DEV · 0 blocking, 0 open question(s), 2 info

| Reviewer | Identity | Checked | Blocking |
|---|---|---|---|
| security | reviewer@contoso.example | 1 semantic model(s): definition (getDefinition, TMDL); role members of Sales (XMLA, inside Fabric); Sales: 1 table(s) with sensitive-looking columns, rows of 1 of them filtered by a role with members (structure, not the filter's effect); Sales / Customers: RLS effect tested, probe reads 20 of 60 rows of [dbo].[customers] in lakehouse sales_lh through its SQL analytics endpoint (<sql-endpoint-host>...), none of another user, its own rows: 20 | 0 |
| decisions | reviewer@contoso.example | 7 fact(s) of the deployed state against 8 decision page(s); F1 how items are named: covered by «Item naming: type prefixes lh_, sm_, rpt_, nb_, lower case, underscores»; F2 lakehouse sales_lh: schemas or not: covered by «Lakehouse sales_lh without schemas, tables loaded over OneLake»; F3 model Sales: storage mode: covered by «Direct Lake on OneLake (not on SQL endpoint)»; F4 model Sales: tables and relationships: covered by «Star schema: customers dimension, orders fact, two explicit measures»; F5 model Sales: which measures: covered by «Star schema: customers dimension, orders fact, two explicit measures»; F6 model Sales: row-level security: covered by «Dynamic RLS on account manager UPN for the Account Managers role»; F7 model Sales: who are the role members: covered by «RLS role members: only tenant users added; example.com AMs pending» | 0 |
| drift | reviewer@contoso.example | signed snapshot | 0 |

## Info

### SEC-010 · baseline · FF Ticino Session 1 DEV

**workspace roles not readable by the reviewer (least privilege)**

- Evidence: GET roleAssignments as reviewer@contoso.example: HTTP 403 InsufficientWorkspaceRole. RLS does not apply to Admin, Member or Contributor; a human checks who holds those roles.
- Reviewer: security

### DRF-000 · - · FF Ticino Session 1 DEV

**no baseline yet**

- Evidence: no signed snapshot for this workspace; 2 item(s) read, one is signed after human approval
- Reviewer: drift


Next: a human approves; then `./py gate/snapshot.py sign` records the approved state.
