---
title: "Item naming: type prefixes lh_, sm_, rpt_, nb_, lower case, underscores"
tags: ["decided-by-human", "Q-1"]
created: 2026-10-28T07:31:10.088Z
updated: 2026-10-28T07:31:10.088Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Item naming: type prefixes lh_, sm_, rpt_, nb_, lower case, underscores

**Decision**: "Items use type prefixes: lh_, sm_, rpt_, nb_, lower case, underscores, so anyone can tell an item's type from its name"

**Decided by**: Matthias Falland, project owner, 2026-10-28; answers open question **Q-1** (how items are named) of the gate review of 2026-10-28 07:19 (`../review/reports/latest-gate.md`, workspace FF Ticino Session 1 DEV).

**Why**: so anyone can tell an item's type from its name.

**Alternatives**: deployed today (review fact F1): Lakehouse «sales_lh» (type as suffix, not prefix) and SemanticModel «Sales» (no type tag, capitalised). No prefix/suffix convention or environment tag was decided before.

**Applies**: from the next delivery (the sentence says nothing about timing; Q-1 is an open question, not a blocking finding).

**Consequence**: the deployed items do not follow it yet: «sales_lh» would be «lh_sales», «Sales» would be «sm_sales». Nothing in the workspace is changed now; renaming is left to a later delivery.

**Source**: https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-tenant-level-planning#workspace-naming-conventions (naming conventions can convey the item types; consistent, predictable names help users and administrators).
