---
title: "SEC-010 Workspace roles not readable by the reviewer"
tags: ["sec"]
created: 2026-10-27T16:23:53.170Z
updated: 2026-10-27T16:23:53.170Z
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
---

# SEC-010 Workspace roles not readable by the reviewer

## What the reviewer found

The security reviewer (reviewer@contoso.example) couldn't read the workspace role assignments of FF Ticino Session 1 DEV.

- Severity: info
- Rule: baseline
- Review run: 2026-10-27 16:22 UTC

## Evidence

- `GET roleAssignments` as reviewer@contoso.example returned HTTP 403 InsufficientWorkspaceRole.
- The same run checked:
  - the definition of 1 semantic model (getDefinition, TMDL)
  - the role members of Sales (XMLA, inside Fabric)
  - 3 sensitive columns in 1 table of Sales

## What it means

The reviewer runs with least privilege on purpose, so the 403 is expected and doesn't block the gate. But RLS does not apply to workspace Admins, Members or Contributors. Anyone in those roles sees every customer, including credit limits and revenue, whatever the `Account Manager` role says (ADR-003). The review can't prove that no account manager holds such a role.

## Who acts

A human with workspace Admin checks who holds Admin, Member or Contributor on FF Ticino Session 1 DEV. That person confirms that account managers get only Viewer or item-level Read.

