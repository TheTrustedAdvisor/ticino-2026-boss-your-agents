---
title: "Lakehouse sales_lh without schemas, tables loaded over OneLake"
tags: ["sales-request", "lakehouse"]
created: 2026-10-28T07:09:20.844Z
updated: 2026-10-28T07:09:20.844Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Lakehouse sales_lh without schemas, tables loaded over OneLake

**Decision:** Create lakehouse `sales_lh` (no schemas), upload `customers.csv` and `orders.csv` to `Files/raw/`, load them as Delta tables `customers` and `orders` with the default OneLake engine (pyarrow, no Spark).

**Why:** Two small tables need no schema separation; the lakehouse auto-discovers Delta tables written under Tables/. The Load Table API (Spark) blocks the F2 capacity for 20+ min (measured 2026-10-27).

**Alternatives:** schema-enabled lakehouse (unneeded for two tables); Load Table API on Spark (capacity contention); notebook/pipeline (overkill for a one-off load).

**Source:** https://learn.microsoft.com/fabric/data-engineering/lakehouse-overview#automatic-table-discovery-and-registration , https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table
