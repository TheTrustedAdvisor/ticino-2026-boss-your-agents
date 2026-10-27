---
title: "Decision: lh_sales without schemas, CSVs loaded through OneLake (applies ADR-001)"
tags: ["sales-request", "session-2", "lakehouse", "ingestion", "ADR-001"]
created: 2026-10-27T16:25:50.447Z
updated: 2026-10-27T16:25:50.447Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: lh_sales without schemas, CSVs loaded through OneLake (applies ADR-001)

# Decision: lh_sales without schemas, CSVs loaded through OneLake (applies ADR-001)

**Decision:** Create lakehouse `lh_sales` without schemas. Upload `customers.csv` (60 rows) and `orders.csv` (600 rows) to `Files/raw/` and write Delta tables `customers` and `orders` with `load-table --engine onelake` (pyarrow, no Spark).

**Why:** ADR-001: on the F2 capacity the Spark Load Table API stays up 20+ minutes and further loads get HTTP 430; Direct Lake only needs Delta tables in OneLake. Two tables gain nothing from schemas, and without schemas the Direct Lake partitions carry no `schemaName`.

**Alternatives:** Load Table API (Spark): throttled on F2. Notebook / pipeline: too heavy for a one-off load. Schema-enabled lakehouse: no benefit at this size.

**Source:** https://learn.microsoft.com/rest/api/fabric/lakehouse/tables/load-table ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview

