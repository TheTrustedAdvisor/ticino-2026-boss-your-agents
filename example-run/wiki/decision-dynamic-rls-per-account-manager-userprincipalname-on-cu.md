---
title: "Decision: Dynamic RLS per account manager (USERPRINCIPALNAME on customers)"
tags: ["sales-request", "security", "rls"]
created: 2026-10-27T16:13:47.695Z
updated: 2026-10-27T16:13:47.695Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: Dynamic RLS per account manager (USERPRINCIPALNAME on customers)

**Decision:** "Every account manager should be able to use it" is read as: every manager can open the model and sees **only their own customers**. One role, `Account Manager` (modelPermission read), with the filter `customers[account_manager_upn] = USERPRINCIPALNAME()`. The filter reaches orders through the single-direction customers→orders relationship. Account managers are added as role members.

**Why:** customers.csv carries `account_manager_upn` per customer, which is a ready-made user-mapping column. One dynamic role scales to new managers without changing the model. RLS applies only to users without Write on the model, so managers must be workspace Viewers or have item-level Read only, never Contributor or higher.

**Alternatives:** One static role per region, which needs a model change for each new manager. No RLS, where every manager sees every customer's credit limit and revenue; that is a data-exposure risk the request doesn't ask for. OneLake security RLS, which needs workspace Admin/Member and which the builder identity doesn't have.

**Open point:** Docs strongly recommend a fixed-identity cloud connection for Direct Lake with model RLS. Under SSO, users need Read+ReadAll on the lakehouse and could bypass RLS by reading OneLake directly. The toolkit can't create connections; a workspace admin must bind one.

**Source:** https://learn.microsoft.com/fabric/security/service-admin-row-level-security ; https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options
