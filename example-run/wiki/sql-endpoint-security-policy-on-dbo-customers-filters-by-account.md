---
title: "SQL endpoint security policy on dbo.customers filters by account_manager_upn (SEC-020)"
tags: ["SEC-020", "remediation", "rls", "sql-endpoint"]
created: 2026-10-28T07:33:31.880Z
updated: 2026-10-28T07:33:31.880Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# SQL endpoint security policy on dbo.customers filters by account_manager_upn (SEC-020)

# SQL endpoint security policy on dbo.customers filters by account_manager_upn (SEC-020)

- **What changed**: in the SQL analytics endpoint of lakehouse `sales_lh`, created schema `rls`, inline table-valued function `rls.fn_account_manager(@account_manager_upn varchar(256))` (`WITH SCHEMABINDING`, returns a row when `LOWER(@account_manager_upn) = LOWER(USER_NAME())`) and security policy `rls.customers_account_manager` with a FILTER PREDICATE on `dbo.customers(account_manager_upn)`, `STATE = ON`. Script: `work/sql/sec-020-customers-rls.sql`, run with `./py tools/fab.py sql exec sales_lh`.
- **Why**: the human decision «Account-manager rule applies in the model and in the SQL endpoint» (Matthias Falland, 2026-10-28, tag `decided-by-human`) answers blocking finding **SEC-020**: probe viewer@contoso.example read 60 of 60 rows of `[dbo].[customers]` through the SQL endpoint. The predicate is the same rule as the model role `Account Managers` (`Customers[Account Manager] = USERPRINCIPALNAME()`).
- **Choices inside the change**:
  - No exemption for Admin/Member/Contributor or the builder: the decision says the rule applies wherever the table is read and names no exception. Learn: security policies apply to all users, dbo included; an exemption must be written into the predicate. Consequence: the builder (builder@contoso.example) now reads 0 rows of `dbo.customers` in the SQL endpoint.
  - `LOWER()` on both sides: the column collation is `Latin1_General_100_BIN2_UTF8` (case-sensitive); UPN case must not decide access.
  - The model is not touched: it is Direct Lake on OneLake (expression `AzureStorage.DataLake`), so it reads Delta files, not the SQL endpoint, and does not fall back to DirectQuery because of this policy.
- **Alternatives considered**: OneLake security (data access roles) on the table — would also cover Spark/OneLake reads, but is a different mechanism from what the decision's source page describes and is not exposed by the toolkit; giving role members access to the model only (no workspace role) — a workspace-role change, outside the toolkit and not what the human decided; a predicate with an admin exemption — not asked for.
- **Checked**: `sys.security_policies` / `sys.security_predicates` show `customers_account_manager` enabled on `customers`; `SELECT COUNT(*) FROM dbo.customers` as the builder → 0; DAX `COUNTROWS(Customers)` on model Sales → 60 (model unaffected). Not checked: a read as viewer@contoso.example (the toolkit runs only as the builder); the reviewer's probe re-run should show 20 rows.
- **Not covered**: `dbo.orders` has no policy; in the SQL endpoint it is still readable in full (in the model it is filtered through the Customers relationship). The finding and the decision name Customers only; extending to orders is for a human to decide.
- **Source**: https://learn.microsoft.com/fabric/data-warehouse/row-level-security

