---
title: "SEC-020 RLS bypass through the SQL analytics endpoint"
tags: ["sec"]
created: 2026-10-28T07:41:24.655Z
updated: 2026-10-28T07:41:24.655Z
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
---

# SEC-020 RLS bypass through the SQL analytics endpoint

## What the reviewer found

The finding was blocking, rule `baseline`, on item Sales / Customers, in round 2026-10-28 07:19: "RLS bypass: a role member reads 60 of 60 rows through the SQL endpoint; model RLS applies only inside the model."

## Evidence (the measurement)

- The probe viewer@contoso.example is a member of role Account Managers.
- It read `[dbo].[customers]` in lakehouse `sales_lh` through its SQL analytics endpoint (<sql-endpoint-host>…).
- It got 60 rows, 40 of which belong to other users according to `account_manager_upn`.
- For comparison, the reviewer read 60 rows through the model, 20 of them its own.

## What it means

The model role `Account Managers` (ADR-004) filters only inside the semantic model. Any role member who can reach the SQL endpoint sees every customer, including other account managers' credit limits.

## Decision that answered it

ADR-006: "The account-manager rule applies wherever the table can be read: in the model and in the SQL endpoint." Matthias Falland, project owner, decided it on 2026-10-28 (`decided-by-human`).

The reviewer's remediation options were:

- a SQL endpoint security policy;
- OneLake security;
- access to the model only.

## What changed

In the SQL analytics endpoint of `sales_lh`, the session created:

- the TVF `rls.fn_account_manager`;
- the security policy `rls.customers_account_manager`, a FILTER PREDICATE on `dbo.customers(account_manager_upn)` matching `LOWER(USER_NAME())`, with no exemption.

Script: `work/sql/sec-020-customers-rls.sql`.

## Result of the next round

In round 2026-10-28 07:35 the gate PASSED. The probe read 20 of 60 rows, all its own, with 0 foreign rows. SEC-020 no longer appears.

## Who acts

Nothing is required for this finding. For the open points below, the project owner decides and a workspace admin acts.

## What stays open

- `[dbo].[orders]`: the probe still reads all 600 rows through the SQL endpoint (`probe.json`, "no user column in the role filter"). The table has no policy. The human has to decide whether to extend the rule to it.
- Reads through Spark or OneLake are not covered by the SQL policy.
- SEC-010: who holds workspace roles that bypass model RLS.

