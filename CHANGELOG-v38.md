# v38 — question fairness and renderer compatibility

5,529 questions; 79 existing records changed, no additions/deletions.

- Set `type: reading` on 64 items whose passages were invisible to the existing app: 57 found by the original audit, plus 7 that arrived in the v37 auto-batch (`g1_v37_012`–`014`, `g4_v37_012`–`014`, `g5_v37_006`).
- Replace 15 distractors numerically equivalent to the keyed answer. Preserve the keyed answer, prompt, explanation, and ID.
- Add full-bank rendering-contract and equivalent-numeric-option validation, plus five regressions and a CI workflow.
- Existing simplest-form item `g5_v22_064` is intentionally unchanged.

## Why this is v38 and not v37

This work branched from v36. While it was open, `auto/questions-v37-20260908` merged to `main` and published v37 (5,529 questions), which included 7 more passage questions with the same missing-`type` defect. Shipping these fixes as a second v37 would have left two different banks under one version number, and `AppStore.fetchRemoteQuestions()` only accepts a bank when `version > local`, so devices that had already cached the first v37 would never have picked the fixes up. The bump to 38 is what makes the fix reachable.

Checks: expanded validator passes with zero errors and 1,095 pre-existing advisories; five tests pass, including a full-bank contract assertion over all 5,529 questions. Human editorial verification remains required.

Merging this PR updates the public bank fetched by installed apps. It does not deploy any Swift/UI changes. The companion iOS PR must re-sync its bundled copy to this v38 before it is merged — it currently bundles the superseded 5,479-question build.
