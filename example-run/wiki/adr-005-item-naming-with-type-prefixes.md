---
title: "ADR-005 Item naming with type prefixes"
tags: ["adr"]
created: 2026-10-28T07:40:59.949Z
updated: 2026-10-28T07:40:59.949Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-005 Item naming with type prefixes

## Status

Accepted. Decided by the human: Matthias Falland, project owner, 2026-10-28 (tag `decided-by-human`). Applies from the next delivery.

## Context

Open question Q-1 of the gate review of 2026-10-28 07:19 asked: "What naming convention should items follow (why sales_lh and Sales, no prefix/suffix or environment tag)?" The items had been built as Lakehouse «sales_lh» (type as suffix) and SemanticModel «Sales» (no type tag, capitalised). No convention had been decided.

## Decision

"Items use type prefixes: lh_, sm_, rpt_, nb_, lower case, underscores, so anyone can tell an item's type from its name."

## Why

So anyone can tell an item's type from its name. Consistent, predictable names help users and administrators.

## Alternatives considered

Keep the names as deployed (`sales_lh`, `Sales`): type as suffix or missing, mixed case, no environment tag.

## Sources

- https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-tenant-level-planning#workspace-naming-conventions

## Evidence from the review

- F1: items built: Lakehouse «sales_lh» and SemanticModel «Sales».
  - Round 07:19: no decision page covered it, so it was raised as open question **Q-1**.
  - Round 07:35: covered by this decision. The reviewer noted that the page applies from the next delivery, so the existing names do not contradict it.
- Consequence: the deployed items do not follow the convention yet. They would be `lh_sales` and `sm_sales`, and renaming is left to a later delivery. Until then, the rule below will report both deployed items.

## Decision log

- `item-naming-type-prefixes-lh-sm-rpt-nb-lower-case-underscores.md`

## Rule

`rules/ADR-005-item-naming-type-prefixes.yaml`

