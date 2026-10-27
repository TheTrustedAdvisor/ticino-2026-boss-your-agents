---
title: "ADR-001 Lakehouse without schemas, loaded through OneLake"
tags: ["adr"]
created: 2026-10-27T16:23:26.970Z
updated: 2026-10-27T16:23:26.970Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-001 Lakehouse without schemas, loaded through OneLake

## Status

Accepted. Decided by the session (data engineer, builder@contoso.example) on 2026-10-27.

## Context

The sales request delivers two small CSV files (`customers.csv` with 60 customers, `orders.csv` with about 300 orders) that have to become Delta tables a Direct Lake model can read. The workspace runs on an F2 capacity.

## Decision

Create the lakehouse `SalesLakehouse` without schemas (default `dbo`). Upload both CSVs to `Files/raw/` and write the Delta tables `customers` and `orders` with `load-table --engine onelake`, where pyarrow writes directly to OneLake.

## Why

- On F2, the Spark-based Load Table API kept a session alive for more than 20 minutes, and later loads failed with HTTP 430 (measured 2026-10-27).
- Direct Lake only needs Delta tables in OneLake. It doesn't matter which engine wrote them.
- A schema-enabled lakehouse brings no benefit for two tables.

## Alternatives considered

- Load Table API (Spark): slow, and throttled on F2.
- A notebook or pipeline: too heavy for a one-off load.
- A schema-enabled lakehouse: no benefit at this size.

## Sources

- https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview

## Evidence from the review

- Fact F2: lakehouse «SalesLakehouse»: schemas off. The decisions reviewer marked it as covered by this decision.
- What the reviewer read: the deployed lakehouse, as reviewer@contoso.example, on 2026-10-27 16:22 UTC.
- Findings: none.

## Decision log

- `decision-lakehouse-load-via-onelake-pyarrow-engine-no-schemas.md`

## Rule

`rules/ADR-001-lakehouse-no-schemas.yaml`

