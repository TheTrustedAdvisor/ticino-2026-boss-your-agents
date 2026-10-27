---
title: "Decision: sm_sales dynamic RLS role Account Manager (applies ADR-003)"
tags: ["sales-request", "session-2", "security", "rls", "ADR-003"]
created: 2026-10-27T16:26:47.277Z
updated: 2026-10-27T16:26:47.277Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: sm_sales dynamic RLS role Account Manager (applies ADR-003)

# Decision: sm_sales dynamic RLS role Account Manager (applies ADR-003)

**Decision:** One role `Account Manager` (modelPermission read) with table filter `Customers[Account Manager] = USERPRINCIPALNAME()`; it reaches Orders through the single-direction relationship. Every account manager can open the model and sees only their own customers, credit limits and revenue.

**Why:** ADR-003. `account_manager_upn` is a ready mapping column; one dynamic role covers new managers without a model change. Credit Limit and Revenue are sensitive. RLS applies only to users without Write on the model, so managers must be workspace Viewer or item Read only (SEC-010: a workspace admin verifies). Learn strongly recommends a fixed-identity cloud connection (SSO off) for semantic-model RLS on Direct Lake; the toolkit cannot create one, so that stays an open point for a workspace admin, and users get no permission on `lh_sales`.

**Alternatives:** Static role per region (model change per manager); no RLS (every manager sees all credit limits); OneLake security RLS (needs workspace Admin/Member, and doesn't support dynamic definitions).

**Source:** https://learn.microsoft.com/fabric/security/service-admin-row-level-security ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#considerations-and-limitations

