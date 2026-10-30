---
title: "ADR-006 Account-manager rule in every engine (model and SQL endpoint)"
tags: ["adr"]
created: 2026-10-28T07:41:11.198Z
updated: 2026-10-28T07:41:11.198Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-006 Account-manager rule in every engine (model and SQL endpoint)

## Status

Accepted. Decided by the human: Matthias Falland, project owner, 2026-10-28 (tag `decided-by-human`), in answer to blocking finding SEC-020. Implemented by the session (builder@contoso.example) the same day.

## Context

The review of 2026-10-28 07:19 blocked on **SEC-020**. Model RLS (ADR-004) applies only inside the model. The probe viewer@contoso.example, a member of Account Managers, read all 60 rows of `[dbo].[customers]` through the SQL analytics endpoint of `sales_lh`, and 40 of those rows belong to other account managers.

## Decision

"The account-manager rule applies wherever the table can be read: in the model and in the SQL endpoint."

The session implemented it in the SQL analytics endpoint of `sales_lh` with the script `work/sql/sec-020-customers-rls.sql`:

- schema `rls`;
- the inline TVF `rls.fn_account_manager(@account_manager_upn varchar(256))` `WITH SCHEMABINDING`, which matches when `LOWER(@account_manager_upn) = LOWER(USER_NAME())`;
- the security policy `rls.customers_account_manager` with a FILTER PREDICATE on `dbo.customers(account_manager_upn)`, `STATE = ON`.

Choices made inside the change:

- No exemption for Admin, Member, Contributor or the builder, because the decision names none. As a result, the builder now reads 0 rows.
- `LOWER()` on both sides, because the column collation `Latin1_General_100_BIN2_UTF8` is case-sensitive.
- The model is unchanged.

## Why

This is the project owner's decision. A rule that holds only in one engine leaves the data open in the others.

## Alternatives considered

- Keep the rule in the model only (as deployed before): rejected by SEC-020.
- OneLake security data access roles: would also cover Spark and OneLake reads, but it is a different mechanism and the toolkit does not expose it.
- Give role members access to the model only (no workspace role): a workspace-role change, which the human did not choose.
- A predicate with an admin exemption: nobody asked for one.

## Sources

- https://learn.microsoft.com/fabric/data-warehouse/row-level-security

## Evidence from the review

- **SEC-020**, round 07:19 (blocking): the probe read 60 of 60 rows, 40 of other users. The reviewer read 60 rows through the model, 20 of them its own.
- Round 07:35 (passed): the probe read 20 of 60 rows of `[dbo].[customers]` through the SQL endpoint (<sql-endpoint-host>…), with 0 foreign rows (`probe.json`: `probe_rows 20`, `probe_own_rows 20`, `foreign_rows 0`). SEC-020 no longer appears.
- The session checked `sys.security_policies` and `sys.security_predicates` (policy enabled), `COUNT(*)` as the builder (0), and DAX `COUNTROWS(Customers)` (60).

## Open items

- `[dbo].[orders]` has no policy. In the 07:35 round the probe still read all 600 rows through the SQL endpoint (`probe.json`: `foreign_rows 600`, "no user column in the role filter"). The reviewer raised no finding for it. Extending the rule to orders, for example with a predicate through `customer_id`, is for the human to decide.
- Spark and OneLake reads of `sales_lh` are not covered by a SQL endpoint policy.

## Decision log

- `account-manager-rule-applies-in-the-model-and-in-the-sql-endpoin.md`
- `sql-endpoint-security-policy-on-dbo-customers-filters-by-account.md`

## Rule

`rules/ADR-006-account-manager-rule-every-engine.yaml`

