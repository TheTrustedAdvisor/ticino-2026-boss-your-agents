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
`sm_sales`. The files in [../example-run/](../example-run/) come from this same run.

Since 30 October 2026 the recordings are the versions shown on stage: each one zooms in on the
evidence and marks it with a frame. They show the demo identities with their real sign-in names in the
demo tenant (for example ff-demo-viewer@matthiasgessenay.onmicrosoft.com); it is a lab tenant used
only for this demo.

## The Fabric side

Four short clips show in the Fabric portal what the agents built. They are silent and zoom in on the
evidence.

| File | Length | What it shows |
|---|---|---|
| [fabric-step-1.mp4](fabric-step-1.mp4) | 0:35 | Step 1: workspace one, the model in TMDL view, the role Account Managers with its filter on Customers and its one member |
| [fabric-step-3.mp4](fabric-step-3.mp4) | 0:37 | Step 3: the SQL analytics endpoint of the lakehouse, a query on sys.security_policies shows the new policy, enabled, on dbo.customers with its predicate |
| [fabric-step-5.mp4](fabric-step-5.mp4) | 0:37 | Step 5: workspace two built by session 2, the same role and filter in the model and the same policy in the SQL endpoint |
| [fabric-step-6.mp4](fabric-step-6.mp4) | 0:23 | Monday morning: the model renamed by hand in the portal, from sm_sales to Sales Model |
