---
title: "ADR-003 Dynamic RLS per account manager, members from the tenant only"
tags: ["adr"]
created: 2026-10-27T16:23:43.766Z
updated: 2026-10-27T16:23:43.766Z
sources: []
links: []
category: architecture
confidence: medium
schemaVersion: 1
---

# ADR-003 Dynamic RLS per account manager, members from the tenant only

## Status

Accepted. Decided by the session (data engineer, builder@contoso.example) on 2026-10-27. One follow-up is open for Sales Ops and one for a workspace admin.

## Context

The request says "every account manager should be able to use it". `customers.csv` maps each customer to an account manager through `account_manager_upn`. The model exposes sensitive columns, such as Credit Limit and revenue. Two of the three account managers in the data have UPNs that are not in the tenant (`@example.com`).

## Decision

- Every account manager can open the model, and each one sees **only their own customers**.
- There is one role, `Account Manager` (modelPermission read), with the filter `Customers[Account Manager] = USERPRINCIPALNAME()`. The filter reaches Orders through the single-direction Customers→Orders relationship.
- Only users or groups of this tenant become role members. The only member added was `viewer@contoso.example` (Ticino).
- `giulia.bernasconi@example.com` (Lombardia) was refused by the service. `luca.ferrari@example.com` (Piemonte) was not attempted, because the address is on the same non-tenant domain.
- Their customers' rows stay in the model, but no one sees them through the role until the UPNs are fixed.

## Why

- The mapping column already exists, and one dynamic role covers new managers without a model change.
- The service accepts only Entra users or groups from the tenant.
- For guests, USERPRINCIPALNAME() can return `user_domain#EXT#@tenant`, so the mapping column must hold the value the function actually returns.
- RLS applies only to users without Write on the model. Account managers must therefore be workspace Viewers or have item-level Read only, never Contributor or higher.

## Alternatives considered

- One static role per region: needs a model change for each new manager.
- No RLS: every manager would see every customer's credit limit and revenue.
- OneLake security RLS: needs workspace Admin or Member, which the builder identity doesn't have.
- Placeholder users in place of the non-tenant managers: wrong.
- Changing the data: not the builder's call.

## Open points

- Sales Ops: provide the real tenant UPNs, or invite the managers as B2B guests and confirm what USERPRINCIPALNAME() returns. Then fix `account_manager_upn`, reload, and add the users. Better still, make an Entra group of account managers the role member.
- Workspace admin: bind a fixed-identity cloud connection for Direct Lake. Under SSO, users need Read+ReadAll on the lakehouse and could bypass RLS by reading OneLake directly.

## Sources

- https://learn.microsoft.com/fabric/security/service-admin-row-level-security
- https://learn.microsoft.com/fabric/security/service-admin-row-level-security#considerations-and-limitations-for-dynamic-rls
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-security-integration#data-access-rule-options

## Evidence from the review

- Fact F6: model «Sales»: roles Account Manager (read): Customers = Customers[Account Manager] = USERPRINCIPALNAME(). Marked as covered by the RLS decision.
- Fact F7: role members of Account Manager: viewer@contoso.example. Marked as covered by the membership decision.
- What the reviewer read:
  - the model definition (getDefinition, TMDL)
  - the role members of Sales (XMLA, inside Fabric)
  - 3 sensitive columns in 1 table
- Findings: SEC-010 (info). The reviewer can't read the workspace roles, so a human checks who holds Admin, Member or Contributor, because RLS does not apply to those roles.

## Decision log

- `decision-dynamic-rls-per-account-manager-userprincipalname-on-cu.md`
- `decision-role-membership-limited-to-in-tenant-account-managers.md`

## Rule

`rules/ADR-003-dynamic-rls-account-manager.yaml`

