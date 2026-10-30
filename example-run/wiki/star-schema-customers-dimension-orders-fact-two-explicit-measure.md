---
title: "Star schema: customers dimension, orders fact, two explicit measures"
tags: ["sales-request", "semantic-model"]
created: 2026-10-28T07:10:26.612Z
updated: 2026-10-28T07:10:26.612Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Star schema: customers dimension, orders fact, two explicit measures

**Decision:** Two tables: `Customers` (customer name, region, account manager UPN, credit limit) and `Orders` (order id, date, amount). Relationship Orders[customer_id] many-to-one Customers[customer_id], single direction. Measures in Orders/Customers: `Revenue = SUM(Orders[amount])`, `Customer Count = COUNTROWS(Customers)`. Key columns hidden; numeric source columns set `summarizeBy: none` so users use the measures.

**Why:** Star schema with one-directional filtering from dimension to fact is the recommended Power BI design; it also lets an RLS filter on Customers propagate to Orders. All 60 customer ids in orders exist in customers (checked), so referential integrity holds.

**Alternatives:** One flat denormalized table (duplicates customer attributes per order, Customer Count needs DISTINCTCOUNT); bidirectional relationship (unneeded, ambiguity risk).

**Source:** https://learn.microsoft.com/power-bi/guidance/star-schema , https://learn.microsoft.com/power-bi/guidance/relationships-bidirectional-filtering
