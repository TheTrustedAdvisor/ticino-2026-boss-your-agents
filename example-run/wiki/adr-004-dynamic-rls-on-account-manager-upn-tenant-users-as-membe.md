---
title: "ADR-004 Dynamic RLS on account manager UPN, tenant users as members"
tags: ["adr"]
created: 2026-10-28T07:40:53.776Z
updated: 2026-10-28T07:40:53.776Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-004 Dynamic RLS on account manager UPN, tenant users as members

## Status

Accepted. Decided by the session (data engineer, identity builder@contoso.example), 2026-10-28.

## Context

The request says: "every account manager should be able to use it." That means one model for all account managers, with each one seeing only their own customers. The customer data already maps every customer to an account manager UPN (`account_manager_upn`).

## Decision

- **Role:** semantic-model role `Account Managers` (modelPermission read) with the filter `Customers[account_manager_upn] = USERPRINCIPALNAME()`. In the model, the column shows as `Customers[Account Manager]`. The filter reaches Orders through the relationship (ADR-003).
- **Members:** every account manager whose UPN is a user of the tenant is added. Today that is `viewer@contoso.example` (Ticino).
- **Not added:** `luca.ferrari@example.com` (Piemonte) and `giulia.bernasconi@example.com` (Lombardia). The service rejected them as "invalid rolememberships" because they are not Entra users of this tenant.

## Why

- Dynamic RLS needs one role instead of one per person, and the data already holds the UPN mapping.
- Role members must be Entra users or groups the service can resolve. Inventing guest accounts or substituting other users would give the wrong people access.
- RLS applies only to users with read (Viewer) rights, not to workspace Admin, Member or Contributor.

## Alternatives considered

- One static role per region: has to change whenever account managers change.
- No RLS: every account manager would see all credit limits and all revenue.
- OneLake security RLS: more administration and not dynamic.
- B2B guest invites for the example.com addresses: need a tenant admin, and USERPRINCIPALNAME() may return `user_example.com#EXT#@…`.
- An Entra security group "Account Managers" as the only member: preferred once the group exists.

## Sources

- https://learn.microsoft.com/fabric/security/service-admin-row-level-security
- https://learn.microsoft.com/fabric/security/service-admin-row-level-security#considerations-and-limitations-for-dynamic-rls
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-fixed-identity

## Evidence from the review

- F6 (both rounds): role Account Managers (read) filters `Customers[Account Manager] = USERPRINCIPALNAME()`. The reviewer noted that the column appears under its display name (source `account_manager_upn`), which is not a real difference. Covered.
- F7 (both rounds): the only member of Account Managers is viewer@contoso.example. Covered.
- The reviewer read the TMDL (`roles/Account Managers.tmdl`) and the role members over XMLA.
- The probe in round 07:35 confirmed the effect: through the model, the reviewer reads 60 rows of Customers and owns 20 of them.
- Findings: SEC-020 (round 07:19) showed that this rule applied only inside the model. See ADR-006.
- SEC-010: workspace roles are not readable by the reviewer, so whether RLS is bypassed by Admin, Member or Contributor roles is still for a human to check.

## Decision log

- `dynamic-rls-on-account-manager-upn-for-the-account-managers-role.md`
- `rls-role-members-only-tenant-users-added-example-com-ams-pending.md`

## Open items

- Sales Ops: provide the tenant UPNs (or a group) for Luca Ferrari and Giulia Bernasconi.
- Workspace admin: choose between a fixed-identity cloud connection for the model or OneLake read on `sales_lh` for account managers, and give account managers the Viewer role or share the model/app.

## Rule

`rules/ADR-004-dynamic-rls-account-managers.yaml`

