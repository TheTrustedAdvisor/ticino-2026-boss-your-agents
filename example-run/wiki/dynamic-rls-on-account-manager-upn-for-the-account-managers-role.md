---
title: "Dynamic RLS on account manager UPN for the Account Managers role"
tags: ["sales-request", "security", "rls"]
created: 2026-10-28T07:10:32.377Z
updated: 2026-10-28T07:10:32.377Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Dynamic RLS on account manager UPN for the Account Managers role

**Decision:** Semantic-model role `Account Managers` (modelPermission read) with filter `Customers[account_manager_upn] = USERPRINCIPALNAME()`. The filter propagates to Orders through the relationship, so each account manager sees only their own customers and revenue. Every account manager whose UPN is a user of the tenant is added as a role member.

**Why:** "Every account manager should be able to use it" = one model for all AMs, each scoped to their own book. Dynamic RLS needs one role instead of one per person, and the UPN mapping is already in the data. RLS applies only to users with Viewer (read) rights, not to workspace Admin/Member/Contributor.

**Alternatives:** One static role per region (must change when AMs change); no RLS (every AM would see all customers' credit limits and revenue); OneLake security RLS (more admin, not dynamic).

**Open item (needs a workspace admin):** with SSO, Direct Lake on OneLake reads the Delta files under the viewer's identity; workspace Viewers have no OneLake read. Either bind the model to a fixed-identity cloud connection (Microsoft's strong recommendation with RLS) or grant AMs OneLake read on sales_lh; and give AMs the Viewer role (or share the model/app).

**Source:** https://learn.microsoft.com/fabric/security/service-admin-row-level-security , https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options , https://learn.microsoft.com/fabric/fundamentals/direct-lake-fixed-identity
