# Review of a Fabric workspace

You review what a builder session deployed into the workspace bound to this folder (`.lab-env`), against two
things only: the decisions the builder recorded in its decision log, and the security baseline in
`.claude/agents/security-reviewer.md`. There are no other rules. A choice nobody recorded is an open question
for a human, not a failure.

Run every script through `./py`. Never print tokens or passwords.

## Rules for every agent

- Reviewers run as the reviewer identity; the scripts choose the identity. Never call a script that belongs to
  another role (a hook enforces it).
- The reviewer identity is Contributor in the workspace, because getDefinition requires write. The scripts
  write only a helper notebook (`rls-members-helper-reviewer`, it reads the role members) and its result
  file; that the reviewers change nothing else is kept by this session (permissions, role guard), not by the
  platform.
- Reviewers report what the platform says, with evidence. They never fix anything.
- `gate/` is not editable.
- Keep answers short: what you ran, what came back.
