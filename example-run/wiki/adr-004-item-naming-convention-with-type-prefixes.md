---
title: "ADR-004 Item naming convention with type prefixes"
tags: ["adr"]
created: 2026-10-27T16:23:48.848Z
updated: 2026-10-27T16:23:48.848Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-004 Item naming convention with type prefixes

## Status

Accepted. Decided by the human: Matthias Falland, project owner, on 2026-10-27, answering open question Q-1 of the gate review.

## Context

The gate review of 2026-10-27 16:22 found that no decision covers how items are named. The deployed items are PascalCase with no type prefix: Lakehouse «SalesLakehouse» and SemanticModel «Sales».

## Decision

Items use type prefixes `lh_`, `sm_`, `rpt_` and `nb_`, in lower case with underscores. The decision applies from the next delivery. Nothing in the workspace changes now, so `SalesLakehouse` and `Sales` don't follow the convention yet.

## Why

So that anyone can tell an item's type from its name (the project owner's stated reason).

## Alternatives considered

The status quo: names without a convention (PascalCase, no type prefix), as the review found them.

## Sources

- https://learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-tenant-level-planning#workspace-naming-conventions

## Evidence from the review

- Fact F1: items built: Lakehouse «SalesLakehouse»; SemanticModel «Sales».
- Finding: Q-1 (open question, "how items are named"), now answered by this decision.
- What the reviewer read: the items in workspace FF Ticino Session 1 DEV.
- The two existing items will fail the naming rule until they are renamed.

## Decision log

- `decision-item-naming-convention-with-type-prefixes-lh-sm-rpt-nb.md` (tagged `decided-by-human`)

## Rule

`rules/ADR-004-item-naming-prefixes.yaml`

