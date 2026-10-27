
## Governed delivery

`/governed-build`: the **builder** agent builds, three reviewer agents check the deployed state with their own
identity (the reviewer identity): security (the security baseline), rules (the project's machine-checkable rules,
`wiki/rules/`) and drift (the signed snapshot). The gate decides, a human approves. **The agent that builds
never approves.** Each agent runs only its own scripts (a hook enforces it); only the builder edits, and only
in `work/`. Nobody signs a snapshot (`gate/snapshot.py sign`) without an explicit "approve" from the human.
