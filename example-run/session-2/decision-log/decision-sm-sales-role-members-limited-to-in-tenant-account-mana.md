---
title: "Decision: sm_sales role members limited to in-tenant account managers (applies ADR-003)"
tags: ["sales-request", "session-2", "security", "rls", "open-issue", "ADR-003"]
created: 2026-10-27T16:27:43.823Z
updated: 2026-10-27T16:27:43.823Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# Decision: sm_sales role members limited to in-tenant account managers (applies ADR-003)

# Decision: sm_sales role members limited to in-tenant account managers (applies ADR-003)

**Decision:** Add only `viewer@contoso.example` (Ticino, 20 customers) to role `Account Manager` of `sm_sales`. `giulia.bernasconi@example.com` (Lombardia) and `luca.ferrari@example.com` (Piemonte) are not tenant users; they are not attempted (session 1 got "a member must be a user (or group) of this tenant" for the same domain). Their 40 customers stay in the model but are visible through the role to no one until Sales Ops fixes the UPNs.

**Why:** ADR-003: only Entra users/groups of the tenant can be role members, and for guests USERPRINCIPALNAME() may return `user_domain#EXT#@tenant`, so the mapping column must hold the value the function returns.

**Alternatives:** Placeholder users (wrong); editing the data (not the builder's call); an Entra group of account managers (preferred long term, needs Sales Ops / an admin to create it).

**Follow-up:** Sales Ops: real tenant UPNs or a group; workspace admin: fixed-identity cloud connection and confirm managers are Viewer / item Read only (SEC-010).

**Source:** https://learn.microsoft.com/fabric/security/service-admin-row-level-security#considerations-and-limitations-for-dynamic-rls

