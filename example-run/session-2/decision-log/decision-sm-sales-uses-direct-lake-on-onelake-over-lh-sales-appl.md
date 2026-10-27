---
title: "Decision: sm_sales uses Direct Lake on OneLake over lh_sales (applies ADR-002)"
tags: ["sales-request", "session-2", "semantic-model", "direct-lake", "ADR-002"]
created: 2026-10-27T16:26:42.368Z
updated: 2026-10-27T16:26:42.368Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: sm_sales uses Direct Lake on OneLake over lh_sales (applies ADR-002)

# Decision: sm_sales uses Direct Lake on OneLake over lh_sales (applies ADR-002)

**Decision:** `sm_sales` has one shared expression `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<workspace-2-id>/<lakehouse-2-id>")` (workspace and lakehouse by GUID) and one `directLake` partition per table (`customers`, `orders`), without `schemaName`. Tables Customers (Customer Name, Region, Account Manager, Credit Limit; measure Number of Customers = COUNTROWS(Customers)) and Orders (measure Revenue = SUM(Orders[Amount])); keys hidden; Orders→Customers many-to-one, single direction.

**Why:** Direct Lake on OneLake never falls back to DirectQuery and supports semantic-model RLS (needed, see the RLS decision). The lakehouse has no schemas, so Learn says to drop `schemaName`.

**Alternatives:** Direct Lake on SQL endpoint: fallback risk. Import: the request asks for Direct Lake. Bidirectional relationship: unnecessary and widens RLS propagation.

**Source:** https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#comparison-of-storage-modes ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop#direct-lake-model-metadata ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-power-bi-desktop#migrate-direct-lake-on-sql-semantic-models-to-direct-lake-on-onelake

