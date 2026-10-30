---
title: "ADR-001 Lakehouse without schemas, tables loaded over OneLake"
tags: ["adr"]
created: 2026-10-28T07:40:29.267Z
updated: 2026-10-28T07:40:29.267Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-001 Lakehouse without schemas, tables loaded over OneLake

## Status

Accepted. Decided by the session (data engineer, identity builder@contoso.example), 2026-10-28.

## Context

The sales request delivers two small CSV files (`customers.csv`, `orders.csv`) that must become tables a semantic model can read. The workspace runs on an F2 capacity.

## Decision

Lakehouse `sales_lh` is created without schemas. The CSVs are uploaded to `Files/raw/` and written as Delta tables `customers` and `orders` under `Tables/` with the OneLake engine (pyarrow, no Spark).

## Why

- Two tables need no schema separation.
- The lakehouse discovers and registers Delta tables written under `Tables/` on its own.
- The Load Table API runs on Spark and blocked the F2 capacity for more than 20 minutes (measured 2026-10-27).

## Alternatives considered

- Schema-enabled lakehouse: not needed for two tables.
- Load Table API (Spark): competes for the capacity.
- Notebook or pipeline: too much for a one-off load.

## Sources

- https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview#automatic-table-discovery-and-registration
- https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table

## Evidence from the review

- F2 (round 07:19 and round 07:35): lakehouse «sales_lh»: schemas off. The decisions reviewer marked it covered by this decision in both rounds.
- The reviewer read the lakehouse item (`state.json`: `schemas: false`, SQL endpoint `93386dcd-…`). The tables are `[dbo].[customers]` (60 rows) and `[dbo].[orders]` (600 rows), according to `probe.json`.
- Findings: none.

## Decision log

- `lakehouse-sales-lh-without-schemas-tables-loaded-over-onelake.md`

## Rule

`rules/ADR-001-lakehouse-without-schemas.yaml`

