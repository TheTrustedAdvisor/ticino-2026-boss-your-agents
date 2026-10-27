# Gate report: PASSED

2026-10-27 16:30 · workspace FF Ticino Session 2 DEV · 0 blocking, 0 open question(s), 2 info

| Reviewer | Identity | Checked | Blocking |
|---|---|---|---|
| security | reviewer@contoso.example | 1 semantic model(s): definition (getDefinition, TMDL); role members of sm_sales (XMLA, inside Fabric); sm_sales: 3 sensitive column(s) in 1 table(s) | 0 |
| rules | reviewer@contoso.example | 4 accepted rule(s) from wiki/rules/ (4 with a machine check); 2 item(s), 1 model(s) | 0 |
| drift | reviewer@contoso.example | signed snapshot | 0 |

## Info

### SEC-010 · baseline · FF Ticino Session 2 DEV

**workspace roles not readable by the reviewer (least privilege)**

- Evidence: GET roleAssignments as reviewer@contoso.example: HTTP 403 InsufficientWorkspaceRole. RLS does not apply to Admin, Member or Contributor; a human checks who holds those roles.
- Reviewer: security

### DRF-000 · - · FF Ticino Session 2 DEV

**no baseline yet**

- Evidence: no signed snapshot for this workspace; 2 item(s) read, one is signed after human approval
- Reviewer: drift


Next: a human approves; then `./py gate/snapshot.py sign` records the approved state.
