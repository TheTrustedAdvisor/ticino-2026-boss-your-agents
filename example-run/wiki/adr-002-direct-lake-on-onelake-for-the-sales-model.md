---
title: "ADR-002 Direct Lake on OneLake for the Sales model"
tags: ["adr"]
created: 2026-10-27T16:23:32.576Z
updated: 2026-10-27T16:23:32.576Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-002 Direct Lake on OneLake for the Sales model

## Status

Accepted. Decided by the session (data engineer, builder@contoso.example) on 2026-10-27.

## Context

The request asks for a Direct Lake semantic model over the sales lakehouse, and the model carries row-level security (see ADR-003).

## Decision

The `Sales` model uses Direct Lake on OneLake. A shared expression, `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws>/<lakehouse>")`, is referenced by one `directLake` partition per table. The partitions have no `schemaName` because the lakehouse has no schemas (ADR-001).

## Why

- Direct Lake on OneLake never falls back to DirectQuery. With Direct Lake on SQL, RLS defined on the SQL endpoint forces a DirectQuery fallback.
- It supports semantic-model RLS, which this model needs.

## Alternatives considered

- Direct Lake on the SQL analytics endpoint: risks falling back to DirectQuery.
- Import: ruled out, because the request asks for Direct Lake.

## Sources

- https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#comparison-of-storage-modes
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop#direct-lake-model-metadata

## Evidence from the review

- Fact F3: model «Sales»: storage mode Direct Lake on OneLake, reads lakehouse «SalesLakehouse». The decisions reviewer marked it as covered by this decision.
- What the reviewer read: the model definition (getDefinition, TMDL), as reviewer@contoso.example, on 2026-10-27.
- Findings: none.

## Decision log

- `decision-direct-lake-on-onelake-storage-mode-for-the-sales-model.md`

## Rule

`rules/ADR-002-direct-lake-onelake.yaml`

