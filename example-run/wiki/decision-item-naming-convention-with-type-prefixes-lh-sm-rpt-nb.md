---
title: "Decision: Item naming convention with type prefixes (lh_, sm_, rpt_, nb_)"
tags: ["decided-by-human", "Q-1"]
created: 2026-10-27T16:22:36.909Z
updated: 2026-10-27T16:22:36.909Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: Item naming convention with type prefixes (lh_, sm_, rpt_, nb_)

**Decision**: "Items use type prefixes: lh_, sm_, rpt_, nb_, lower case, underscores, so anyone can tell an item's type from its name"

**Decided by**: Matthias Falland, project owner, 2026-10-27. Answers open question Q-1 (how items are named) of the gate review of 2026-10-27 16:22 (`review/reports/latest-gate.md`, workspace FF Ticino Session 1 DEV).

**Why**: so anyone can tell an item's type from its name (the project owner's stated reason).

**Alternatives**: The review found the items deployed without a convention: PascalCase names with no type prefix, Lakehouse «SalesLakehouse» and SemanticModel «Sales» (finding F1).

**Consequence**: Two deployed items do not follow the convention yet: Lakehouse «SalesLakehouse» and SemanticModel «Sales». Nothing in the workspace changes now. The decision applies from the next delivery.

**Source**: https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-tenant-level-planning#workspace-naming-conventions

