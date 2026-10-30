---
title: "Direct Lake on OneLake (not on SQL endpoint)"
tags: ["sales-request", "semantic-model", "direct-lake"]
created: 2026-10-28T07:09:24.091Z
updated: 2026-10-28T07:09:24.091Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Direct Lake on OneLake (not on SQL endpoint)

**Decision:** The semantic model `Sales` uses Direct Lake on OneLake: shared expression `AzureStorage.DataLake("https://onelake.dfs.fabric.microsoft.com/<ws id>/<lakehouse id>")`, partitions `mode: directLake`.

**Why:** Microsoft recommends Direct Lake on OneLake for new semantic models; it never falls back to DirectQuery, and semantic-model RLS is supported.

**Alternatives:** Direct Lake on SQL analytics endpoint (can silently fall back to DirectQuery); Import (requires data refresh copies, not what was asked).

**Source:** https://learn.microsoft.com/fabric/fundamentals/direct-lake-how-it-works#directquery-fallback , https://learn.microsoft.com/fabric/fundamentals/direct-lake-develop#power-query-connectors
