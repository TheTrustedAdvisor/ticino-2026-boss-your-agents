# Recordings

Five terminal recordings of one continuous real run on 27 October 2026. Long agent work is sped up (the cuts
are visible as jumps in the timer); the panel on the right explains each scene.

| Video | Length | Shows |
|---|---|---|
| [step-1.mp4](step-1.mp4) | 2:01 | Step 0 and 1: the empty folder, `CLAUDE.md`, `.mcp.json`; `/build`; two decision pages |
| [step-2.mp4](step-2.mp4) | 1:02 | Step 2: `/review`, three reviewers in parallel, the gate report with Q-1, SEC-010 and DRF-000 |
| [step-3.mp4](step-3.mp4) | 0:56 | Step 3: `/decide` answers Q-1, then `snapshot.py sign` |
| [step-4.mp4](step-4.mp4) | 1:12 | Step 4: `/compile-wiki`, `publish-wiki.sh`, the index and ADR-005 |
| [step-5.mp4](step-5.mp4) | 1:35 | Step 5: `handover.sh`, `/governed-build` to PASSED and the question whether to approve; the plan with the ADR ids |

In this run session 1 named its items `sales_lh` and `Sales`, and session 2 built `lh_sales` and
`sm_sales`. The files in [../example-run/](../example-run/) come from a separate run of the same engine, so
their item names differ.

The sign-in names of the demo tenant are replaced in the picture by `builder@contoso.example`,
`reviewer@contoso.example` and `viewer@contoso.example`. The replacement runs on the emulated screen, so
where a name was longer than its placeholder the rest of its cells stay blank. The demo identities' short
names (for example «ff-demo-contributor») and the workspace names are as they were.
