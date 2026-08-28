# DO-NOT-SHIP — publishing rules & frozen numbers

**Check this file before every asset export, every 小红书 note draft, every screenshot, and every
line of App Store or website copy.** "We'll be careful" is not a control.

> ### Scope — read this first
>
> **This file constrains what we PUBLISH. It has no authority over what we WRITE.**
>
> Nothing here is a reason to change, remove, or avoid a question. If a question is right for the
> kid but awkward to advertise, it stays in the bank and we advertise something else. Question
> authoring is governed by `AUTHORING.md`, whose tiers 1–3 are the only rules that can reject a
> question; everything in this file lives in that document's advisory tier 4 by design.
>
> `python3 validate.py --cards cards.json` exports the screenshot-safe pool so you can *find*
> existing material rather than commission new material to fit a post.

Last verified against `questions.json` v23 (4,951 questions) on 2026-08-28.

**On versions.** v22 was verified live on 2026-08-28 — `origin/main`, the raw URL the app fetches,
the local copy, and the app's bundled fallback were byte-identical at 4,951 questions. The growth
plan's note that `main` was still v17 / 2,201 was stale; that merge happened in `506ac7e`. **v23
(the correction release described in §2) is on a branch and is not live until it is merged**, and
merging hot-ships to every installed device with no rollback.

---

## 1. Frozen numbers — quote these exactly, never round up

Three different NYC counts were in circulation (293 / 294 / 282). None were reproducible.
The numbers below come from a strict word-boundary match over 34 NYC terms across
`prompt` / `options` / `passage` (see §4 to regenerate).

| Fact | Number | Approved public phrasing |
|---|---|---|
| Total questions | 4,951 | 「近5000道」 |
| **NYC questions the kid actually sees** | **247** | **「近250道写纽约的题」** |
| NYC questions incl. explanation text | 255 | *(internal only — do not publish)* |
| Standards-coded (CCSS / NGSS / NY State) | 3,816 (v23) | 「3816道带标准代码」 |
| Pre-K–G3 share of bank | 86.5% | 「最合适5–9岁，K到三年级，题库八成在这个区间」 |
| Chinese handwriting questions | 72 (K–G4) | 「72道田字格写字题」 |
| Default earning rate | 3 questions × 5 min = 15 min | 「答对3题换15分钟」 |

**NYC subject mix** (do not mis-lead on this): `ela 111 · social_studies 71 · reading 27 · math 21`.
The subway word problem is the **thinnest** slice (21 questions), not the widest. Lead with
五个区 / 纽约常识 / 纽约历史; treat the subway math problem as one nice example, not the category.

---

## 2. Repaired in v23 — was a blocklist, now a record

All sixteen questions listed here were **fixed in v23**, not removed. Nothing in this section is a
publishing restriction any more; it is kept so that a bad revert is visible in review and so the
failure modes stay documented. `validate.py` catches every one of these mechanically — run it
against the pre-v23 bank and it still reports thirteen of them.

**Unanswerable or wrongly keyed**

| ID | What was wrong |
|---|---|
| `g5_v4_003` | **Every option was a false comparison** (0.45 = 0.450; 0.309 < 0.31; 1.072 > 1.07; 2.560 = 2.56). Nothing was answerable, and the explanation concluded with an answer that was not among the options. |
| `g5_v22_078` | **Wrong answer key.** 2³ + 4 × (6 − 2) = 24, keyed to 28. The explanation computed 24 correctly and then leaked `Correct answer index 2` — an off-by-one from 1-based counting. |
| `g5_v4_007` | Options `30,000 / 31,000 / 31,000 / 31,000`. |
| `g4_v4_013` | B and C both `1,081`. |
| `g5_v4_010` | A and D both `0.024`. |
| `g1_v6_015` | A and D both `36`. |
| `g1_v6_080` | Asked which **two words** make "can't" but keyed `cannot` — one word — plus a duplicate option. |

**Factually wrong**

| ID | What was wrong |
|---|---|
| `g3_v4_271` | Called Staten Island the smallest borough **by area**. It is the least *populous*; Manhattan is smallest by area, and the question's own `explain` said "by population", contradicting its prompt. The superlative is gone; it now simply asks which borough the ferry reaches. |

**Authoring scratch text shipped to children**

| ID | What was wrong |
|---|---|
| `g2_v19_146` | The **prompt** read *"Wait — this passage sounds different from a story"* to a 2nd grader. |
| `g5_v22_078`, `g5_v22_102`, `g2_v20_021`, `g1_v21_009` | `Wait:` / `Index 1 →` / `Correct answer index 2` in explanations. The last three had correct keys; only the explanations were rewritten. |

**Other**

| ID | What was wrong |
|---|---|
| `g3_v22_040` | The passage lectured the reader — *"Here, the main idea is that solar panels…"* — then asked for the main idea. Passage removed; the prompt quotes its own paragraph. |
| `g5_v22_058` | Passage described *"the epidemic of lynching — racial terrorist murder"* to a 10-year-old, in a passage the prompt never referenced. Passage removed. |
| `g2_v2_004`, `g12_money_003` | Contradictory MetroCard prices ($1.00 vs $3), neither accurate, for a card being retired for OMNY. Now a bodega bagel and a Brooklyn farmers market; the money math is unchanged. |

---

## 3. NYC questions verified safe to publish

`g3_v4_271` is repaired as of v23 and may be quoted again. These are independently verified:

- **`g3_v4_268`** — *"Which NYC borough is an island completely surrounded by water?"* → **Manhattan** ✅
- **`g12_nyc_001`** — *"New York City has 5 boroughs. Which of these is NOT one of them?"* → **Newark** ✅
- `k_v5_088` (Coney Island → Brooklyn) · `g2_v2_019` (the other two boroughs) ·
  `g3_v22_148` (Chinatown / Little Italy / Harlem as immigrant neighborhoods) · `g3_v22_138` (Lenape)

⚠️ **Two previously-listed items carry details that will age.** They are fine as questions and are
staying in the bank — this is a publishing note only:

- `g35_infer_001` — the passage has Kenji packing a **MetroCard**, which is being retired for OMNY.
- `g12_read_009` — the passage asserts **"472 stations"**, a count that varies by how station
  complexes are counted and that changes over time. Its keyed answer (runs 24/7) is durable; the
  station count is the exposed detail.

Prefer the borough and neighborhood questions for anything with a long shelf life.

---

## 4. Screenshot safety rule

Two measured biases, both real, one smaller than previously claimed:

- **Option D is correct only 5.9% of the time.** Reproduced exactly. "Never pick D" is a free
  exploit and the more serious of the two.
- **29.2% of MC questions have the correct answer as the uniquely longest option.** The figure of
  ~70% that circulated earlier does not reproduce under any definition that excludes ties, and a
  tie carries no signal to a guesser. 29.2% is still well above the 25% chance rate — and among
  text-option questions the key is longest-or-tied 64% of the time — so the tell is real, but it
  is not the one-glance giveaway the earlier note implied.

New questions are held to `LEN_TELL` in `AUTHORING.md` tier 3, so this does not grow.

**Only ever publish questions whose options are:**
- numeric (e.g. `13 / 14 / 15 / 16`), or
- picture-type, or
- handwriting/tracing, or
- drawn from one fixed vocabulary — the five boroughs, the seasons, cardinal directions
  (tagged `closedSet: true`; length varies without signalling anything), or
- visibly equal in length.

`python3 validate.py --cards cards.json` applies exactly this filter and exports the pool —
**2,579 questions, 52% of the bank.** Pick from it rather than hand-picking screenshots. This is a
selection rule for publishing, never a reason to alter or reject a question.

**Never make a claim of the form** 「防猜」 / 「答不对就过不了」 / "learning-gated access".
The anti-guessing claim is scoped **only** to the 2–4s option lock, which is 100% true and demoable:
> 选项要等 2–4 秒才亮起来，逼孩子先把题读完。 ← anti-**impulse**, not anti-guessing.

**Prepared reply if someone catches it:**
> 你说得对，一部分题的正确选项确实偏长，我在一批批改。选项锁 2–4 秒是防瞎点，不是防会读题的娃。

---

## 5. Features that DO NOT EXIST — never claim these

Verified absent from the shipping source:

- per-app allowlisting (blocking is all-or-nothing: `shield.applicationCategories = .all()`)
- time-of-day / bedtime / school-hours schedules
- multiple child profiles
- iCloud or multi-device sync
- sound effects or haptics
- AI question generation
- **a working daily cap** — the "Daily cap" slider exists in the parent UI and is referenced by
  **zero** earning logic. **Crop it out of every settings screenshot.**
  If asked: 「那个滑杆目前没接上逻辑，我下版会处理。」
- a Chinese kid-facing UI (parent area is bilingual; kid side is deliberately English-only)
- **「完全离线 / 零联网」** — the bank is fetched from `raw.githubusercontent.com` on launch

---

## 6. Regenerating the frozen numbers

```bash
python3 - <<'PY'
import json, re
d = json.load(open('questions.json')); qs = d['questions']
terms = ["New York","NYC","Brooklyn","Manhattan","Bronx","Queens","Staten Island","borough","boroughs",
"subway","MTA","MetroCard","OMNY","Central Park","Prospect Park","Brooklyn Bridge","Statue of Liberty",
"Ellis Island","Coney Island","Times Square","Empire State","Rockefeller","Harlem","Chinatown",
"Hudson River","East River","Yankee","Mets","Broadway","bodega","Lenape","Flushing","Astoria","Bushwick"]
pat = re.compile(r'(?i)(?<![A-Za-z])(' + "|".join(map(re.escape, terms)) + r')(?![A-Za-z])')
def txt(q, fields):
    s = []
    for f in fields:
        v = q.get(f)
        if isinstance(v, str): s.append(v)
        elif isinstance(v, list): s += [x for x in v if isinstance(x, str)]
    return " ".join(s)
kid = [q for q in qs if pat.search(txt(q, ["prompt","options","passage"]))]
print("version", d['version'], "total", len(qs))
print("NYC visible to kid:", len(kid))
print("NYC incl. explain:", len([q for q in qs if pat.search(txt(q, ["prompt","options","passage","explain"]))]))
print("standards-coded:", sum(1 for q in qs if q.get('standard')))
kg3 = sum(1 for q in qs if q['grade'] in ('prek','k','g1','g2','g3'))
print("preK-G3 share:", kg3, f"{100*kg3/len(qs):.1f}%")
PY
```

**If the terms list changes, the number changes.** Do not re-scan with a different list and quote a
different number — the frozen number is 247, and consistency matters more than precision here.
