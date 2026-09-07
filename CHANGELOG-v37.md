# v37 — question fairness and renderer compatibility

5,479 questions; 72 existing records changed, no additions/deletions.

- Set `type: reading` on 57 items whose passages were invisible to the existing app.
- Replace 15 distractors numerically equivalent to the keyed answer. Preserve the keyed answer, prompt, explanation, and ID.
- Add full-bank rendering-contract and equivalent-numeric-option validation, plus five regressions and a CI workflow.
- Existing simplest-form item `g5_v22_064` is intentionally unchanged.

Checks: expanded validator passes with zero errors and 1,095 pre-existing advisories; five tests pass. Human editorial verification remains required. The related iOS PR bundles identical v37 data and documents the full audit implementation scope.

Merging this PR updates the public bank fetched by installed apps. It does not deploy any Swift/UI changes. No merge has been performed.
