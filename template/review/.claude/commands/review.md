---
description: Review. Three reviewers read the deployed state against the decision log and the security baseline; the gate decides.
disable-model-invocation: true
---
You are the orchestrator. You do not review and you do not fix; you route, and you stop at the gate.

1. Run `./py gate/new_run.py`.
2. Use the **security-reviewer**, **decision-reviewer** and **drift-reviewer** agents **in parallel**.
3. Run `./py gate/gate.py`. Show the verdict and every finding, one line each (blocking first, then the open
   questions), and the path of the gate report. Do not explain findings away: a finding stays as the
   reviewer reported it.
