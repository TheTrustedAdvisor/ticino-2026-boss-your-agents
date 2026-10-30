---
title: "Account-manager rule applies in the model and in the SQL endpoint"
tags: ["decided-by-human", "SEC-020"]
created: 2026-10-28T07:31:42.542Z
updated: 2026-10-28T07:31:42.542Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Account-manager rule applies in the model and in the SQL endpoint

- **Decision**: "The account-manager rule applies wherever the table can be read: in the model and in the SQL endpoint"
- **Decided by**: Matthias Falland, project owner, 2026-10-28; answers blocking finding **SEC-020** (RLS bypass through the SQL endpoint) of the gate review of 2026-10-28 07:19 (`../review/reports/latest-gate.md`, workspace FF Ticino Session 1 DEV).
- **Why**: decision of the project owner.
- **Alternatives**: deployed today is the rule in the model only (dynamic RLS on `account_manager_upn`, role Account Managers, see «Dynamic RLS on account manager UPN for the Account Managers role»); the SQL analytics endpoint of `sales_lh` has no filter. Other remediations the review named: OneLake security, or giving role members access to the model only (no workspace role).
- **Applies**: now (answers a blocking finding; applied with `/remediate` before signing).
- **Consequence**: the SQL analytics endpoint of lakehouse `sales_lh` does not follow it yet: the probe viewer@contoso.example (member of Account Managers) read 60 of 60 rows of `[dbo].[customers]`, 40 of them belonging to other account managers. A security policy with a filter predicate on `account_manager_upn` is still to be created there. Nothing was changed in the workspace with this decision.
- **Source**: https://learn.microsoft.com/fabric/data-warehouse/row-level-security

