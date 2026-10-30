---
title: "DRF-000 No baseline yet; signed baseline of 2026-10-28"
tags: ["drf"]
created: 2026-10-28T07:41:31.566Z
updated: 2026-10-28T07:41:31.566Z
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
---

# DRF-000 No baseline yet; signed baseline of 2026-10-28

## What the reviewer found

The finding is info, in both rounds (2026-10-28 07:19 and 07:35; drift read at 07:34:18 UTC): "no baseline yet". There was no signed snapshot for workspace FF Ticino Session 1 DEV. The reviewer read 2 items, and one snapshot is signed after human approval.

## What was signed

After the passed gate of 07:35, `baseline.json` was signed:

- **Approved by:** Matthias Falland, at 2026-10-28T07:35:56Z.
- **Read by:** reviewer@contoso.example.
- **Signed with:** `ssh-keygen -Y sign`, namespace `zero-to-hero`.

| Item | Id | Definition parts |
|---|---|---|
| Lakehouse/sales_lh | <lakehouse-1-id> | 0 |
| SemanticModel/Sales | <model-1-id> | 8 |

The 8 parts of Sales are:

- `definition.pbism`
- `definition/database.tmdl`
- `definition/expressions.tmdl`
- `definition/model.tmdl`
- `definition/relationships.tmdl`
- `definition/roles/Account Managers.tmdl`
- `definition/tables/Customers.tmdl`
- `definition/tables/Orders.tmdl`

The signed hashes are identical to those the drift reviewer read at 07:34 (`drift.json`).

## How drift is detected

1. In each review, the drift reviewer reads every item's definition (getDefinition) and hashes each part with SHA-256.
2. It verifies the snapshot's SSH signature.
3. It compares the items and hashes against the snapshot. An added, removed or renamed item, or a part whose hash changed, is drift.

The lakehouse has no definition parts, so only its existence and id are signed. Changes outside item definitions are not covered:

- table data;
- the SQL endpoint security policy of ADR-006;
- role members.

## What stays open

Renaming the items under ADR-005 (`lh_sales`, `sm_sales`) will show as drift and needs a new signature after approval.

