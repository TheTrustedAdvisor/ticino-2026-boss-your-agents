---
title: "Decision: Role membership limited to in-tenant account managers"
tags: ["sales-request", "security", "rls", "open-issue"]
created: 2026-10-27T16:20:47.787Z
updated: 2026-10-27T16:20:47.787Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: Role membership limited to in-tenant account managers

**Decision:** Only `viewer@contoso.example` (Ticino) was added to the `Account Manager` role. `giulia.bernasconi@example.com` (Lombardia) was refused: "a member must be a user (or group) of this tenant". `luca.ferrari@example.com` (Piemonte) is on the same non-tenant domain, so the add wasn't attempted. Their rows stay in the model, but no one can see them through the role until the UPNs are fixed.

**Why:** The service accepts only Entra users or groups in the tenant. For guests, USERPRINCIPALNAME() can return `user_domain#EXT#@tenant` rather than the email, so even once they're invited, the mapping column must match what USERPRINCIPALNAME() actually returns.

**Alternatives:** Swap in placeholder users, which would be wrong. Change the data, which isn't the builder's call.

**Follow-up for Sales Ops:** Provide the real tenant UPNs (or invite them as B2B guests and confirm the value USERPRINCIPALNAME() returns), fix `account_manager_upn` in customers.csv, reload, and add the users. Better still, add an Entra group of account managers as the role member.

**Source:** https://learn.microsoft.com/fabric/security/service-admin-row-level-security#considerations-and-limitations-for-dynamic-rls
