# Gate report: PASSED

2026-10-28 08:00 · workspace FF Ticino Session 2 DEV · 0 blocking, 0 open question(s), 1 info

| Reviewer | Identity | Checked | Blocking |
|---|---|---|---|
| security | reviewer@contoso.example | 1 semantic model(s): definition (getDefinition, TMDL); role members of sm_sales (XMLA, inside Fabric); sm_sales: 1 table(s) with sensitive-looking columns, rows of 1 of them filtered by a role with members (structure, not the filter's effect); sm_sales / Customers: RLS effect tested, probe reads 20 of 60 rows of [dbo].[customers] in lakehouse lh_sales through its SQL analytics endpoint (<sql-endpoint-host>...), none of another user, its own rows: 20 | 0 |
| rules | reviewer@contoso.example | 5 accepted rule(s) from wiki/rules/ (5 with a machine check); 2 item(s), 1 model(s) | 0 |
| drift | reviewer@contoso.example | snapshot signature (ssh-keygen -Y verify); 2 approved item(s) | 0 |

## Info

### SEC-010 · baseline · FF Ticino Session 2 DEV

**workspace roles not readable by the reviewer (least privilege)**

- Evidence: GET roleAssignments as reviewer@contoso.example: HTTP 403 InsufficientWorkspaceRole. RLS does not apply to Admin, Member or Contributor; a human checks who holds those roles.
- Reviewer: security


Next: a human approves; then `./py gate/snapshot.py sign` records the approved state.
