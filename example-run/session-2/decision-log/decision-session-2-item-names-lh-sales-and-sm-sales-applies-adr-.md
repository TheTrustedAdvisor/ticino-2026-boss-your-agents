---
title: "Decision: Session 2 item names lh_sales and sm_sales (applies ADR-004)"
tags: ["sales-request", "session-2", "naming", "ADR-004"]
created: 2026-10-27T16:25:31.086Z
updated: 2026-10-27T16:25:31.086Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: Session 2 item names lh_sales and sm_sales (applies ADR-004)

# Decision: Session 2 item names lh_sales and sm_sales (applies ADR-004)

**Decision:** In workspace FF Ticino Session 2 DEV (empty at start) the lakehouse is named `lh_sales` and the semantic model `sm_sales`. No report or notebook is built.

**Why:** ADR-004 (decided by the project owner) requires type prefixes `lh_`, `sm_`, `rpt_`, `nb_`, lower case with underscores, from the next delivery on; this is that delivery. The rule `rules/ADR-004-item-naming-prefixes.yaml` checks `^lh_[a-z0-9_]+$` and `^sm_[a-z0-9_]+$`.

**Alternatives:** Reuse the session 1 names `SalesLakehouse` / `Sales`: violates ADR-004. Longer names like `lh_sales_operations`: no extra information for one lakehouse.

**Source:** https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-tenant-level-planning#workspace-naming-conventions

