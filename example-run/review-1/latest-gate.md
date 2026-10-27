# Gate report: PASSED

2026-10-27 16:22 · workspace FF Ticino Session 1 DEV · 0 blocking, 3 open question(s), 2 info

| Reviewer | Identity | Checked | Blocking |
|---|---|---|---|
| security | reviewer@contoso.example | 1 semantic model(s): definition (getDefinition, TMDL); role members of Sales (XMLA, inside Fabric); Sales: 3 sensitive column(s) in 1 table(s) | 0 |
| decisions | reviewer@contoso.example | 7 fact(s) of the deployed state against 4 decision page(s); F2 lakehouse SalesLakehouse: schemas or not: covered by «Decision: Lakehouse load via OneLake (pyarrow) engine, no schemas»; F3 model Sales: storage mode: covered by «Decision: Direct Lake on OneLake storage mode for the Sales model»; F6 model Sales: row-level security: covered by «Decision: Dynamic RLS per account manager (USERPRINCIPALNAME on customers)»; F7 model Sales: who are the role members: covered by «Decision: Role membership limited to in-tenant account managers» | 0 |
| drift | reviewer@contoso.example | signed snapshot | 0 |

## Open questions (a human decides)

### Q-1 · open · how items are named

**Why are the items named SalesLakehouse and Sales, and is that the naming convention you want?**

- Evidence: F1: items built: Lakehouse «SalesLakehouse»; SemanticModel «Sales». Names appear only on pages about other choices. No decision page covers it.
- Remediation: a human decides (one sentence) and the decision goes into the log
- Reviewer: decisions

### Q-2 · open · model Sales: tables and relationships

**Why does the model include exactly these tables and columns (e.g. Credit Limit, Account Manager exposed) and this one relationship?**

- Evidence: F4: model «Sales»: tables Customers (Account Manager, Credit Limit, Customer ID, Customer Name, Region); Orders (Amount, Customer ID, Order Date, Order ID); relationships Orders.'Customer ID' -> Customers.'Customer ID'. No page decides the model's table/column selection; the relationship is only mentioned in the RLS page. No decision page covers it.
- Remediation: a human decides (one sentence) and the decision goes into the log
- Reviewer: decisions

### Q-3 · open · model Sales: which measures

**Why are Customer Count and Revenue the only measures, and how is Revenue defined?**

- Evidence: F5: model «Sales»: measures Customers[Customer Count], Orders[Revenue]. No page decides measures. No decision page covers it.
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


Next: a human answers the open questions (one sentence each) and approves; then `./py gate/snapshot.py sign` records the approved state.
