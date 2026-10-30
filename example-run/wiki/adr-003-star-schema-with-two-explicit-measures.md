---
title: "ADR-003 Star schema with two explicit measures"
tags: ["adr"]
created: 2026-10-28T07:40:41.994Z
updated: 2026-10-28T07:40:41.994Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-003 Star schema with two explicit measures

## Status

Accepted. Decided by the session (data engineer, identity builder@contoso.example), 2026-10-28.

## Context

The business needs revenue and customer figures for each account manager. The data has a customer list and an order list.

## Decision

- Two tables: `Customers` (dimension: customer name, region, account manager UPN, credit limit) and `Orders` (fact: order id, date, amount).
- One relationship: Orders[customer_id] many-to-one Customers[customer_id], filtering in a single direction.
- Two explicit measures: `Revenue = SUM(Orders[amount])` and `Customer Count = COUNTROWS(Customers)`.
- Key columns are hidden, and numeric source columns use `summarizeBy: none`.

## Why

- A star schema that filters one way, from dimension to fact, is the recommended Power BI design.
- It lets an RLS filter on Customers reach Orders.
- Referential integrity holds: all 60 customer ids in orders exist in customers (checked).

## Alternatives considered

- One flat table: repeats the customer attributes on every order, and Customer Count would need DISTINCTCOUNT.
- Bidirectional relationship: not needed and risks ambiguity.

## Sources

- https://learn.microsoft.com/power-bi/guidance/star-schema
- https://learn.microsoft.com/power-bi/guidance/relationships-bidirectional-filtering

## Evidence from the review

- F4 (both rounds): tables Customers (Account Manager, Credit Limit, Customer Name, Region, customer_id) and Orders (Order Date, amount, customer_id, order_id); relationship Orders.customer_id -> Customers.customer_id. Covered.
- F5 (both rounds): measures Customers[Customer Count] and Orders[Revenue]. Covered.
- The reviewer read the TMDL parts `tables/Customers.tmdl`, `tables/Orders.tmdl` and `relationships.tmdl`.
- Findings: none.

## Decision log

- `star-schema-customers-dimension-orders-fact-two-explicit-measure.md`

## Rule

No machine check. None of the rule kinds can express table design or measures.

