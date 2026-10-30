---
title: "RLS role members: only tenant users added; example.com AMs pending"
tags: ["sales-request", "security", "rls"]
created: 2026-10-28T07:12:43.218Z
updated: 2026-10-28T07:12:43.218Z
sources: []
links: []
category: decision
confidence: medium
schemaVersion: 1
---

# RLS role members: only tenant users added; example.com AMs pending

**Decision:** Added `viewer@contoso.example` (Ticino) to role `Account Managers`. Did not add `luca.ferrari@example.com` (Piemonte) or `giulia.bernasconi@example.com` (Lombardia): the service refused luca.ferrari ("invalid rolememberships"), so these addresses are not Entra users of this tenant, and example.com is the same case.

**Why:** Role members must be Entra users or groups the service can resolve. Inventing guest accounts or substituting other users would grant the wrong people access.

**Alternatives:** Invite them as B2B guests (needs a tenant admin; USERPRINCIPALNAME() may then return `user_example.com#EXT#@...`, so the mapping must be checked); use an Entra security group "Account Managers" as the single member (preferred for maintenance once it exists).

**Follow-up for Sales Ops:** provide the real tenant UPNs (or a group) for Luca Ferrari and Giulia Bernasconi; update account_manager_upn in customers.csv if they differ.

**Source:** https://learn.microsoft.com/fabric/security/service-admin-row-level-security#considerations-and-limitations-for-dynamic-rls
