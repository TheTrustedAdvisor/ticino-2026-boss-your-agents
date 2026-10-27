---
title: "DRF-000 No baseline at review time, signed afterwards"
tags: ["drf"]
created: 2026-10-27T16:23:59.798Z
updated: 2026-10-27T16:23:59.798Z
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
---

# DRF-000 No baseline at review time, signed afterwards

## What the reviewer found

The drift reviewer (reviewer@contoso.example) found no signed snapshot for workspace FF Ticino Session 1 DEV at 2026-10-27 16:21 UTC.

- Severity: info
- It read 2 items: Lakehouse/SalesLakehouse and SemanticModel/Sales.
- There was nothing to compare them against, so no drift could be reported.

## What was signed

After the gate passed, the reviewed state was approved and signed. The baseline is `review/reports/baseline.json`.

| Field | Value |
|---|---|
| Approved by | Matthias Falland |
| Approved at | 2026-10-27T16:22:46Z |
| Read by | reviewer@contoso.example |
| Workspace | FF Ticino Session 1 DEV |
| Signed with | `ssh-keygen -Y sign`, namespace `zero-to-hero` |

The baseline covers these items:

| Item | Id | Definition parts |
|---|---|---|
| Lakehouse/SalesLakehouse | <lakehouse-1-id> | 0 |
| SemanticModel/Sales | <model-1-id> | 8 |

The 8 signed parts of Sales are:

- `definition.pbism`
- `definition/database.tmdl`
- `definition/expressions.tmdl`
- `definition/model.tmdl`
- `definition/relationships.tmdl`
- `definition/roles/Account Manager.tmdl`
- `definition/tables/Customers.tmdl`
- `definition/tables/Orders.tmdl`

Every hash in the baseline matches the hash the drift reviewer read, so the signed state is exactly the reviewed state.

## How drift is detected

1. The next drift review verifies the SSH signature of the baseline.
2. It reads every item's definition again and computes a SHA-256 hash per part.
3. It compares these hashes with the signed ones.

Any of these is drift:

- a changed hash
- a part that was added or removed
- an item that was added or removed
- a changed item id

Each change needs a new review and a new human approval before it is signed.

