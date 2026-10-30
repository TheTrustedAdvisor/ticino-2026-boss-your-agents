---
title: "SEC-010 Workspace roles not readable by the reviewer"
tags: ["sec"]
created: 2026-10-28T07:41:16.598Z
updated: 2026-10-28T07:41:16.598Z
sources: []
links: []
category: reference
confidence: medium
schemaVersion: 1
---

# SEC-010 Workspace roles not readable by the reviewer

## What the reviewer found

Severity info, rule `baseline`, item workspace FF Ticino Session 1 DEV. It was reported in both rounds (2026-10-28 07:19 and 07:35). The security reviewer cannot list who holds workspace roles.

## Evidence

`GET roleAssignments` as reviewer@contoso.example returned HTTP 403 InsufficientWorkspaceRole ("Workspace role is not sufficient to perform the operation"; `state.json`: `workspace_roles: null`).

## What it means

The reviewer works with least privilege, so this is expected. However, RLS does not apply to workspace Admin, Member or Contributor (ADR-004). Anyone holding one of those roles reads every row in the model. The SQL endpoint policy of ADR-006 has no exemption, so it is not bypassed by those roles. Whether an account manager holds such a role is therefore not machine-checked.

## Decision that answered it

None. It is info, not a blocking finding.

## What changed, result of the next round

Nothing changed. It is reported unchanged in round 07:35.

## Who acts

A human with workspace admin rights checks the role assignments of FF Ticino Session 1 DEV. Account managers must hold Viewer at most, or have access only through sharing or an app.

## What stays open

Who holds Admin, Member or Contributor in the workspace.

