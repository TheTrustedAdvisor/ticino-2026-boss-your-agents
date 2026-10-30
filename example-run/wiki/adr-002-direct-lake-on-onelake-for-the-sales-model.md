---
title: "ADR-002 Direct Lake on OneLake for the Sales model"
tags: ["adr"]
created: 2026-10-28T07:40:35.281Z
updated: 2026-10-28T07:40:35.281Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-002 Direct Lake on OneLake for the Sales model

## Status

Accepted. Decided by the session (data engineer, identity builder@contoso.example), 2026-10-28.

## Context

The semantic model `Sales` has to read the Delta tables of `sales_lh` and support row-level security.

## Decision

The `Sales` model uses Direct Lake on OneLake. Its shared expression is `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws id>/<lakehouse id>")` and its partitions use `mode: directLake`.

## Why

Microsoft recommends Direct Lake on OneLake for new semantic models. It never falls back to DirectQuery, and it supports semantic-model RLS.

## Alternatives considered

- Direct Lake on the SQL analytics endpoint: can fall back to DirectQuery without notice.
- Import: needs refreshes that copy the data, which the request did not ask for.

## Sources

- https://learn.microsoft.com/fabric/fundamentals/direct-lake-how-it-works#directquery-fallback
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop#power-query-connectors

## Evidence from the review

- F3 (both rounds): model «Sales»: storage mode Direct Lake on OneLake, reads lakehouse «sales_lh». It is covered by this decision.
- The reviewer read the model definition through getDefinition (TMDL; `definition/expressions.tmdl` is among the signed parts) and classified the storage as `direct_lake_onelake`.
- The SQL endpoint security policy (ADR-006) leaves the model unaffected because the model reads Delta files, not the endpoint. As the builder, DAX `COUNTROWS(Customers)` still returns 60.
- Findings: none.

## Decision log

- `direct-lake-on-onelake-not-on-sql-endpoint.md`

## Rule

`rules/ADR-002-direct-lake-on-onelake.yaml`

