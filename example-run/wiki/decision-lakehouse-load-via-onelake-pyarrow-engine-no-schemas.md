---
title: "Decision: Lakehouse load via OneLake (pyarrow) engine, no schemas"
tags: ["sales-request", "lakehouse", "ingestion"]
created: 2026-10-27T16:12:37.278Z
updated: 2026-10-27T16:12:37.278Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: Lakehouse load via OneLake (pyarrow) engine, no schemas

**Decision:** Create lakehouse `SalesLakehouse` (no schemas, default `dbo`), upload `customers.csv` and `orders.csv` to Files/raw/, and write Delta tables `customers` and `orders` with `load-table --engine onelake` (pyarrow writes directly to OneLake).

**Why:** Two small CSVs (60 customers, about 300 orders). On the F2 capacity, the Spark-based Load Table API keeps a session alive for 20+ minutes and later loads fail with HTTP 430 (measured 2026-10-27). Direct Lake only needs Delta tables in OneLake, whatever wrote them. A schema-enabled lakehouse gives no benefit for two tables.

**Alternatives:** Load Table API (Spark), which is slow and throttled on F2. A notebook or pipeline, which is too heavy for a one-off load.

**Source:** https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview
