# Recordings

Six terminal recordings of one continuous real run on 28 October 2026. Long agent work is sped up (the cuts
are visible as jumps in the timer); the panel on the right explains each scene.

| Video | Length | Shows |
|---|---|---|
| [step-1.mp4](step-1.mp4) | 2:12 | Step 0 and 1: the empty folder, `CLAUDE.md`, `.mcp.json`; `/build`; two decision pages |
| [step-2.mp4](step-2.mp4) | 1:11 | Step 2: `/review`, three reviewers in parallel; BLOCKED: SEC-020 (a role member reads 60 of 60 rows through the SQL endpoint) and the open question Q-1 on item names |
| [step-3.mp4](step-3.mp4) | 2:34 | Step 3: two `/decide` sentences, `/remediate` adds the rule in the SQL endpoint, `/review` passes (20 of 60 rows, none of another user), `snapshot.py sign` |
| [step-4.mp4](step-4.mp4) | 1:27 | Step 4: `/compile-wiki`, `publish-wiki.sh`, the index, the SEC-020 page and the naming ADR |
| [step-5.mp4](step-5.mp4) | 2:07 | Step 5: `handover.sh`, `/governed-build` to PASSED, `approve` with the confirmation of the ask rule; the plan citing the ADRs and SEC-020 |
| [step-6.mp4](step-6.mp4) | 1:42 | Step 6, Monday morning: the model renamed by hand, `/review` blocks with DEC-201 and DRF-003, renamed back, `/review` passes |

In this run session 1 named its items `sales_lh` and `Sales`, and session 2 built `lh_sales` and
`sm_sales`. The files in [../example-run/](../example-run/) come from a separate run of the same engine, so
their item names differ.

The sign-in names of the demo tenant are replaced in the picture by `builder@contoso.example`,
`reviewer@contoso.example` and `viewer@contoso.example`. The replacement runs on the emulated screen, so
where a name was longer than its placeholder the rest of its cells stay blank. The demo identities' short
names (for example «ff-demo-contributor») and the workspace names are as they were.
