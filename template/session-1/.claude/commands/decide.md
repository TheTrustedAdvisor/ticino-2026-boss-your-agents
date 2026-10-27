---
description: Record a decision of the project owner, given in one sentence, in the decision log.
argument-hint: <the decision in one sentence>
disable-model-invocation: true
---
The project owner decided: "$ARGUMENTS"

1. Read the latest review report, `../review/reports/latest-gate.md`, and find the open question(s) (Q-*)
   this decision answers.
2. Find the Microsoft Learn page that supports the decision (one search, one URL).
3. Record it with `wiki_add` as one page (the wiki adds the title as heading), category `decision`, tags
   `decided-by-human` and the question ids:
   - **Decision**: the sentence, verbatim.
   - **Decided by**: the project owner (the name in `APPROVED_BY` of `.lab-env`, if set), today; answers which open question of which review.
   - **Why**: the reason if one was given; otherwise "decision of the project owner". Never invent a reason.
   - **Alternatives**: what the review found deployed for this question, if it differs.
   - **Consequence**: the deployed items that do not follow it yet, from the question's evidence. Nothing in
     the workspace changes now; the decision applies from the next delivery.
   - **Source**: the Microsoft Learn URL.
4. Answer in two lines: the page you created and the question(s) it closes.
