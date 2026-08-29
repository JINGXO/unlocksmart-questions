# AUTHORING — how questions get written

## The goal, which does not change

**Every question must be academically correct and match what a kid in that grade is actually
doing in a NYC public school classroom.**

That is the whole goal. It does not move.

A question earns its place by being right and by being the right question for that grade. Nothing
else qualifies it. In particular:

> **No marketing need ever changes what a question asks.**
>
> Not the channel, not the keyword, not the campaign, not the screenshot. If a topic is good for
> the kid, we write it whether or not it is convenient to advertise. If a topic is good for a post
> but wrong for the grade, we do not write it. There is no version of this where the two trade
> against each other, because they are not the same kind of thing: one is about a child's
> schoolwork and the other is about a picture on the internet.

This is enforced structurally, not by good intentions. `validate.py` sorts its rules into four
tiers, and **only tiers 1–3 can fail a build**. Tier 4 is the marketing tier; it prints advice and
is incapable of blocking a merge or rejecting a question. If a genuinely good question is awkward
to screenshot, we ship the question and find something else to screenshot.

`DO-NOT-SHIP.md` is the companion file. It governs **what we publish**, never what we write.

Measured against `questions.json` v24 (4,879 questions), 2026-08-28.

---

## Tier 1 — Is it correct?

Blocking, applied to the entire bank on every run.

| Code | Rule |
|---|---|
| `WRONG_KEY` | The keyed answer must be the correct one. Arithmetic prompts are recomputed independently. |
| `DUP_OPT` | Options must be distinct. Whitespace is normalized; **case and punctuation are not**, because a capitalization or end-mark question's options differ only by those. |
| `BAD_KEY` | `correct` must resolve to an option. |
| `SCRATCH` | No authoring scratch text in anything a child reads — `Wait:`, `Index 1 →`, `Correct answer index 2`, `TODO`. |
| `SELF_ANS` | The text must not *tell* the reader the answer through instructional meta-language ("Here, the main idea is…"). |

**On `SELF_ANS`, an important calibration.** This is deliberately *not* an "answer appears in the
passage" check. Literal recall (`RL.K.1`, `RL.3.1`) and topic-sentence main idea (`RI.2.2`) are
real, required skills in which the answer is *supposed* to be findable in the text. An overlap
check flagged 69 questions and every one inspected was correct pedagogy. The actual defect was
narrower: a passage that lectured the reader about what the main idea was, then asked for it.

---

## Tier 2 — Does it fit the grade it is filed under?

Blocking. This is the tier that means "matches schoolwork."

| Code | Rule |
|---|---|
| `STD_GRADE` | A question's `standard` must be for the grade it is filed under. Pre-K may cite Kindergarten codes — CCSS has no Pre-K tier. |
| `NUM_RANGE` | Numbers in the **prompt and the correct answer** stay inside the grade's expectation: Pre-K 20 · K 100 · G1 120 · G2 1,000 · G3 10,000 · G4 1,000,000 · G5 10,000,000. |
| `PROMPT_LEN` | Outlier guard on reading load before the question starts. Reading/ELA/literacy are exempt — they carry the text being read. |
| `AGE` | Graphic-violence vocabulary is rejected at every grade in this bank. Heavy history topics warn unless the passage frames them. |
| `DIFF_RANGE` | `difficulty` must fall in the grade's plausible band: Pre-K 1–2 · K 1–3 · G1–G2 2–4 · G3–G5 2–5. Advisory for existing questions, blocking for new. |
| `NO_STD` | Advisory for existing questions, **blocking for new ones** under `--strict`. |
| `TRACE` | Chinese handwriting items need `traceMode`, `pinyin`, `meaning`. |

**On `NUM_RANGE`, the calibration that matters: distractors are exempt.** A first-grade
place-value question offering `503` as a wrong answer for "5 tens and 3 ones" is *good* teaching —
it models a real misconception. Judging the whole option list flagged 30 questions, all of them
correctly written. Only the prompt and the keyed answer describe the arithmetic the child must
actually do.

**The bank currently passes tiers 1 and 2 completely**, including zero standard/grade mismatches
outside the legitimate Pre-K→K case, zero out-of-range numbers, and zero over-long prompts. Its
problems were never systematic grade drift — they were individual broken questions.

---

## Tier 3 — Is it a fair test?

Blocking for **newly authored** questions (`--strict`), not retroactive.

- `LEN_TELL` — the correct option must not be the uniquely longest. Mark genuinely fixed-vocabulary
  option sets (the five boroughs, the seasons, cardinal directions) with `closedSet: true`; there,
  length varies without signalling anything.
- `POS_SKEW` — across a new batch, each of A/B/C/D is correct 20–30% of the time. Bank-wide, D is
  currently correct **5.9%** of the time; "never pick D" is a free exploit and we should not grow it.
- `DIFF_SKEW` — **new questions must spread across the grade's difficulty band, not pile onto one
  level.** No single difficulty may hold more than 55% of what a batch adds to a grade, and the
  batch mean must stay within 0.6 of that grade's existing mean.

  This one is operational, not cosmetic. `AppStore.pickAdaptiveQuestion` tries the child's
  **current** level first and only then widens to ±1 and ±2, while `KidFlow` moves that level by
  one per answer. So a batch written entirely at the top of a band is nearly invisible to the child
  who most needs it: they answer one wrong, drop a level, and fall straight through to the old pool.
  The v25 run failed exactly this way — **19 of its 20 G4 questions were difficulty 4** (bank
  average 3.17) and its G5 questions averaged 4.50 against 3.78. Every question was correct; the
  additions simply landed where they helped least.
- `OPT_COUNT` — four options.

---

## Tier 4 — Marketing convenience. Advisory. Cannot block anything.

Reports which questions happen to be easy to publish, and flags NYC claims a local parent could
contest (`NYC_VOLATILE`, `NYC_SUPERLATIVE`, `NYC_NO_SRC`). **A question that fails every check in
this tier is a perfectly good question.** These outputs exist so marketing can *find* material
that already exists — never so marketing can request material that doesn't.

---

## NYC content — a setting, not a quota

NYC context is genuinely valuable: it makes a word problem concrete for a kid who rides that
subway line. It is also our clearest differentiator. But it is a **setting we may choose when it
fits the standard being taught**, and it is explicitly **not** a target to hit.

There are no NYC volume quotas in this file, and there should never be one. An earlier draft of
this document set them (NYC 247→500, NYC math 21→80) by working backwards from a content calendar.
That was the wrong direction of causation: it would have produced questions built to fill a post.

Rules when a question does use NYC:

1. **The standard comes first.** NYC is the wrapper, never the reason. If the setting distorts the
   math or the skill, drop the setting.
2. **Durable facts only.** No fares, prices as civic claims, ride counts, or current officials.
   MetroCard prices already produced two contradictory questions, for a card being retired for OMNY.
   A word problem that stipulates its own price ("a bagel costs $1.00") is a premise, not a claim
   about the city, and is fine.
3. **Superlatives need a stated dimension.** "Smallest borough" is meaningless — by area it's
   Manhattan, by population it's Staten Island. This exact ambiguity shipped a wrong answer.
4. **Cite it.** Fact-bearing NYC questions (social studies, reading, ELA, science) carry a `source`.
   Math word problems that merely use NYC as scenery do not need one.

Extra metadata fields are safe: `Question` in `Models.swift` declares an explicit `CodingKeys`
enum, so the app ignores keys it doesn't know.

---

## What the next bank should actually work on

Driven by measured curriculum coverage, not by channel:

| Grade | Questions | Standards-coded | Biggest uncoded topics |
|---|---|---|---|
| Pre-K | 300 | 79% | Counting, Shapes, Compare |
| K | 1,275 | 75% | Counting, Phonics, Sight Words |
| G1 | 611 | **65%** | Chinese Characters, Word Problem, Subtraction |
| G2 | 801 | 86% | Comprehension, Word Problem |
| G3 | 1,297 | 86% | Multiplication, Fractions |
| G4 | **376** | **54%** | Fractions, Division, Decimals |
| G5 | 291 | 72% | Inference, Word Problem, Algebra |

**1,063 questions (21.8%) carry no standard code.** That is the single largest gap between this
bank and "matches schoolwork," and it is invisible to a parent right up until they look for it.

Priorities, in order:

1. **Backfill standards on existing questions**, worst grades first (G4 at 54%, G1 at 65%).
   Coding an existing good question is cheaper than writing a new one and closes the gap faster.
2. **Introduce an explicit "no standard applies" value** rather than leaving the field empty. The
   Chinese handwriting questions had no CCSS equivalent and never will, and picture/logic items
   are in the same position; today they are indistinguishable from questions nobody has gotten to
   yet. Distinguishing "not applicable" from "not yet reviewed" makes the 1,063 number honest.
3. **Decide G4/G5 deliberately.** They are the thinnest and worst-coded grades, and 86.5% of the
   bank is Pre-K–G3. Either deepen them or state that this is a Pre-K–G3 product. Right now it is
   the second in practice and the first on the label.
4. **Before restoring Chinese handwriting** (disabled in v24, preserved in
   `disabled/chinese-handwriting.json`), fix the 22 items missing `traceMode` — the tracing
   template is the point of those questions, and without it the item silently degrades.
5. **Then** write new questions, against the uncoded topic list above.

---

## Workflow

```bash
python3 validate.py                                   # tiers 1-2 across the bank
python3 validate.py --report                          # + coverage and marketing pool
python3 validate.py --strict --baseline old.json      # + tier 3 on newly written questions
python3 validate.py --cards cards.json                # export publishable pool for marketing
```

`--baseline` grandfathers every existing `id`, so this spec is not retroactive. Produce one with
`git show main:questions.json > old.json`.

**Merging to `main` hot-ships to every installed device** (`AppStore.swift:124` fetches
`raw.githubusercontent.com/.../refs/heads/main/questions.json`) with no rollback and no staged
release. `validate.py` exiting 0 is the gate.

Regression check worth keeping: run the validator against the pre-v23 bank and confirm it still
reports the 13 mechanically detectable defects that release fixed.

---

## When a public number changes

`DO-NOT-SHIP.md` §1 holds the frozen public numbers and the script that regenerates them. If a new
bank moves one, regenerate there first, then update any copy quoting it. Two files disagreeing
about the same count is how three different NYC numbers (293 / 294 / 282) ended up in circulation
when the real figure was 247.
