---
title: "Decision: Direct Lake on OneLake storage mode for the Sales model"
tags: ["sales-request", "semantic-model", "direct-lake"]
created: 2026-10-27T16:13:42.065Z
updated: 2026-10-27T16:13:42.065Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: Direct Lake on OneLake storage mode for the Sales model

**Decision:** Model `Sales` uses Direct Lake on OneLake. The shared expression `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws>/<lakehouse>")` is referenced by a `directLake` partition per table, with no `schemaName` because the lakehouse has no schemas.

**Why:** Direct Lake on OneLake never falls back to DirectQuery. That matters because the model carries RLS, and with Direct Lake on SQL, RLS defined on the SQL endpoint forces DirectQuery fallback. It also supports semantic-model RLS.

**Alternatives:** Direct Lake on SQL analytics endpoint, which has fallback risk. Import, which the request rules out because it asks for Direct Lake.

**Source:** https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview#comparison-of-storage-modes ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop#direct-lake-model-metadata
