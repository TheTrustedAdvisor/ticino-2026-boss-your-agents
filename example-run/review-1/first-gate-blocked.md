# Gate report: BLOCKED

2026-10-28 07:19 · workspace FF Ticino Session 1 DEV · 1 blocking, 1 open question(s), 2 info

| Reviewer | Identity | Checked | Blocking |
|---|---|---|---|
| security | reviewer@contoso.example | 1 semantic model(s): definition (getDefinition, TMDL); role members of Sales (XMLA, inside Fabric); Sales: 1 table(s) with sensitive-looking columns, rows of 1 of them filtered by a role with members (structure, not the filter's effect) | 1 |
| decisions | reviewer@contoso.example | 7 fact(s) of the deployed state against 5 decision page(s); F2 lakehouse sales_lh: schemas or not: covered by «Lakehouse sales_lh without schemas, tables loaded over OneLake»; F3 model Sales: storage mode: covered by «Direct Lake on OneLake (not on SQL endpoint)»; F4 model Sales: tables and relationships: covered by «Star schema: customers dimension, orders fact, two explicit measures»; F5 model Sales: which measures: covered by «Star schema: customers dimension, orders fact, two explicit measures»; F6 model Sales: row-level security: covered by «Dynamic RLS on account manager UPN for the Account Managers role»; F7 model Sales: who are the role members: covered by «RLS role members: only tenant users added; example.com AMs pending» | 0 |
| drift | reviewer@contoso.example | signed snapshot | 0 |

## Blocking

### SEC-020 · baseline · Sales / Customers

**RLS bypass: a role member reads 60 of 60 rows through the SQL endpoint; model RLS applies only inside the model**

- Evidence: probe viewer@contoso.example (member of role Account Managers) read [dbo].[customers] in lakehouse sales_lh through its SQL analytics endpoint (<sql-endpoint-host>...): 60 rows, 40 of them belong to other users (account_manager_upn); the reviewer reviewer@contoso.example read 60 rows through the model, its own rows: 20
- Remediation: Apply the same rule wherever the table can be read: a security policy in the SQL analytics endpoint (filter predicate on the user column), or OneLake security; or give role members access to the model only (no workspace role)
- Reviewer: security


## Open questions (a human decides)

### Q-1 · open · how items are named

**What naming convention should items follow (why sales_lh and Sales, no prefix/suffix or environment tag)?**

- Evidence: F1: items built: Lakehouse «sales_lh»; SemanticModel «Sales». Names appear only on pages about other choices. No decision page covers it.
- Remediation: a human decides (one sentence) and the decision goes into the log
- Reviewer: decisions


## Info

### SEC-010 · baseline · FF Ticino Session 1 DEV

**workspace roles not readable by the reviewer (least privilege)**

- Evidence: GET roleAssignments as reviewer@contoso.example: HTTP 403 InsufficientWorkspaceRole. RLS does not apply to Admin, Member or Contributor; a human checks who holds those roles.
- Reviewer: security

### DRF-000 · - · FF Ticino Session 1 DEV

**no baseline yet**

- Evidence: no signed snapshot for this workspace; 2 item(s) read, one is signed after human approval
- Reviewer: drift


Next: apply each blocking finding's remediation (the builder, or the human who made the change), then every reviewer runs again.
