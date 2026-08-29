#!/usr/bin/env python3
"""Gate for question-bank changes. See AUTHORING.md for the rules behind each code.

    python3 validate.py                          # whole bank
    python3 validate.py --strict --baseline old.json   # + authoring rules on questions not in baseline
    python3 validate.py --report                 # coverage + marketing-pool report (never fails)
    python3 validate.py --cards cards.json       # export the screenshot-safe pool for marketing

THE ONE STRUCTURAL RULE OF THIS FILE:
    Tiers 1-3 judge whether a question is good for the kid. They set the exit code.
    Tier 4 judges whether a question is convenient to advertise. It NEVER sets the exit code
    and never blocks a merge. If a great question is hard to screenshot, we ship the question
    and find something else to screenshot.
"""

import argparse
import collections
import json
import re
import sys

# ── grade model ──────────────────────────────────────────────────────────────

GRADES = ["prek", "k", "g1", "g2", "g3", "g4", "g5"]
GRADE_LEVEL = {"prek": -1, "k": 0, "g1": 1, "g2": 2, "g3": 3, "g4": 4, "g5": 5}

# Largest number a kid at this grade should meet in the QUESTION or the CORRECT ANSWER.
# Distractors are deliberately exempt: an out-of-range distractor is usually good pedagogy
# (503 as a distractor for "5 tens and 3 ones" models a real place-value misconception).
NUM_CAP = {"prek": 20, "k": 100, "g1": 120, "g2": 1000, "g3": 10000,
           "g4": 1000000, "g5": 10000000}

# Extreme-outlier guard on how much a kid must read before the question begins.
# Reading/ELA prompts are exempt: they legitimately carry the text being read.
PROMPT_WORD_CAP = {"prek": 20, "k": 30, "g1": 35, "g2": 45, "g3": 55, "g4": 65, "g5": 75}
TEXT_SUBJECTS = ("reading", "ela", "literacy")

# Difficulty band each grade may plausibly use, as (min, max) inclusive.
#
# This is a *pedagogical* plausibility check, not a reachability one. `AppStore.pickAdaptiveQuestion`
# searches `target → ±1 → ±2`, and `KidFlow` walks the target up and down with the child's
# performance, so almost any level is reachable eventually via the widening fallback. What the band
# encodes is that a difficulty-5 question filed under Pre-K is far more likely mis-graded content
# than a deliberate stretch item.
#
# The batch-spread rules below are the ones that matter operationally: the engine tries the child's
# CURRENT level first, so a batch written entirely at the top of a grade's band is nearly invisible
# to the child who most needs the practice — they get one wrong, drop a level, and fall straight
# through to the old pool.
DIFFICULTY_BAND = {"prek": (1, 2), "k": (1, 3), "g1": (2, 4), "g2": (2, 4),
                   "g3": (2, 5), "g4": (2, 5), "g5": (2, 5)}

# A new batch may not pile into one level: no single difficulty may exceed this share of the
# questions added to a grade, once the batch is big enough for the share to mean anything.
DIFFICULTY_MAX_SHARE = 0.55
DIFFICULTY_MIN_BATCH = 6
# ...and the batch's mean difficulty must stay within this much of the grade's existing mean,
# so a run cannot quietly ratchet a grade harder or easier over time.
DIFFICULTY_MEAN_TOLERANCE = 0.6

# ── patterns ─────────────────────────────────────────────────────────────────

NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")
NUMERIC_OPT = re.compile(r"^[\s$]*[-+]?[\d,]*\.?\d+\s*(%|¢|cm|in|ft|kg|lb|°F|°C)?\s*$")
STD_LEVEL = re.compile(r"^(?:(?:RL|RI|RF|L|W|SL)\.)?(?:(K)|(\d))\.")

# Authoring scratch that leaked into shipped text. This class of defect put
# "Wait - this passage sounds different from a story" in front of a 2nd grader.
SCRATCH = re.compile(
    r"(?i)(correct answer index|\bindex \d|\blet me\b|as an ai|\bTODO\b|\bFIXME\b"
    r"|\bwait\s*[:,—–-]|\bhmm\b|\bactually,\s*(the|it|we)\b)"
)

# Instructional meta-language that hands the reader the answer, rather than a passage the
# reader has to work from. Distinct from "the answer appears in the text", which is fine.
META_TEXT = re.compile(
    r"(?i)(here,? the main idea is|the main idea is that|the correct answer is"
    r"|the answer is|the other answer choices|the other options are|this question asks)"
)

GRAPHIC = re.compile(r"(?i)\b(lynch\w*|murder\w*|rape[ds]?|massacre\w*|suicide|terrorist)\b")
HEAVY = re.compile(r"(?i)\b(slaver\w+|enslav\w+|\bwar\b|killed|died|death)\b")
FRAMING = re.compile(r"(?i)\b(long ago|in the past|history|today|now|laws?|changed|freedom|rights)\b")

# Tier 4 only. NYC facts that expire or that a local parent can contest.
NYC_TERMS = ["New York", "NYC", "Brooklyn", "Manhattan", "Bronx", "Queens", "Staten Island",
             "borough", "boroughs", "subway", "MTA", "MetroCard", "OMNY", "Central Park",
             "Prospect Park", "Brooklyn Bridge", "Statue of Liberty", "Ellis Island",
             "Coney Island", "Times Square", "Empire State", "Rockefeller", "Harlem",
             "Chinatown", "Hudson River", "East River", "Yankee", "Mets", "Broadway",
             "bodega", "Lenape", "Flushing", "Astoria", "Bushwick"]
NYC_RE = re.compile(r"(?i)(?<![A-Za-z])(" + "|".join(map(re.escape, NYC_TERMS)) + r")(?![A-Za-z])")
VOLATILE = re.compile(
    r"(?i)(metrocard|omny|\bmayor\b|\bgovernor\b|population of"
    r"|\d[\d,]*\s+(stations|stops|residents)"
    r"|(fare|subway|bus|ferry|train|ticket|ride)\b[^.?!]{0,40}\$\s?\d"
    r"|\$\s?\d[^.?!]{0,40}\b(fare|per ride|each ride|to ride)\b)"
)
SUPERLATIVE = re.compile(r"(?i)\b(smallest|largest|biggest|longest|oldest|tallest)\b")
DIMENSION = re.compile(r"(?i)\b(in area|by area|by population|in population|square miles|by length)\b")

# Repaired in v23. Kept so a bad revert is visible in review.
FIXED_IN_V23 = {
    "g3_v4_271", "g3_v22_040", "g5_v22_058", "g5_v4_007", "g4_v4_013", "g5_v4_010",
    "g1_v6_015", "g1_v6_080", "g2_v2_004", "g12_money_003", "g5_v22_078", "g5_v4_003",
    "g2_v20_021", "g1_v21_009", "g5_v22_102", "g2_v19_146",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def norm(s):
    """Whitespace only. Case and punctuation are load-bearing — a capitalization or
    end-mark question's options differ *only* by those and are not duplicates."""
    return re.sub(r"\s+", " ", str(s)).strip()


def loose(s):
    return norm(s).lower()


def options(q):
    o = q.get("options")
    return o if isinstance(o, list) and len(o) >= 2 else None


def key_index(q):
    o = options(q)
    if o is None:
        return None
    c = q.get("correct")
    if isinstance(c, bool):
        return None
    if isinstance(c, int):
        return c if 0 <= c < len(o) else None
    if isinstance(c, str):
        for i, opt in enumerate(o):
            if norm(opt) == norm(c):
                return i
    return None


def keyed_answer(q):
    i = key_index(q)
    return str(options(q)[i]) if i is not None else ""


def text_of(q, fields=("prompt", "options", "passage")):
    out = []
    for f in fields:
        v = q.get(f)
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            out += [x for x in v if isinstance(x, str)]
    return " ".join(out)


def words(s):
    return len(re.findall(r"[A-Za-z']+", str(s or "")))


def max_number(text):
    v = [float(m.group(0).replace(",", "")) for m in NUM.finditer(str(text))]
    return max(v) if v else None


def is_nyc(q):
    return bool(NYC_RE.search(text_of(q)))


def is_chinese(q):
    return bool(re.search(r"[一-鿿]", str(q.get("word") or ""))) or q.get("language") == "zh-Hans"


def is_screenshot_safe(q):
    """Tier 4 only. Whether a card can be published without showing an answer-length tell.
    Never a reason to reject a question."""
    if q.get("type") in ("handwriting", "picture") or q.get("subject") == "picture":
        return True
    o = options(q)
    if o is None:
        return False
    s = [str(x) for x in o]
    if len({norm(x) for x in s}) < len(s):
        return False
    if all(NUMERIC_OPT.match(x) for x in s):
        return True
    # Options drawn from one fixed vocabulary (the five boroughs, the seasons, the cardinal
    # directions) vary in length without that length signalling anything.
    if q.get("closedSet"):
        return True
    lens = [len(x) for x in s]
    return max(lens) - min(lens) <= 2


def uniquely_longest(q):
    i = key_index(q)
    o = options(q)
    if i is None or o is None:
        return False
    lens = [len(str(x)) for x in o]
    return lens[i] == max(lens) and lens.count(max(lens)) == 1


# ── Tier 1: is the question correct? ─────────────────────────────────────────

ARITH = [
    (re.compile(r"^What is (\d+)\s*[x×*]\s*(\d+)\?$"), lambda a, b: a * b),
    (re.compile(r"^What is (\d+)\s*\+\s*(\d+)\?$"), lambda a, b: a + b),
    (re.compile(r"^What is (\d+)\s*-\s*(\d+)\?$"), lambda a, b: a - b),
    (re.compile(r"^What is ([\d.]+)\s*[x×*]\s*([\d.]+)\?$"), lambda a, b: a * b),
]


def tier1_correctness(q):
    errs = []
    qid = q.get("id", "<no id>")

    o = options(q)
    if o is None:
        if q.get("type") != "handwriting":
            errs.append(("NO_OPT", f"{qid} has no usable options list"))
        return errs

    if len({norm(x) for x in o}) < len(o):
        errs.append(("DUP_OPT", f"{qid} has duplicate options: {o}"))

    i = key_index(q)
    if i is None:
        errs.append(("BAD_KEY", f"{qid} correct={q.get('correct')!r} does not resolve to an option"))
        return errs

    # Arithmetic the bank asserts and we can recompute independently.
    p = str(q.get("prompt", "")).strip()
    for rx, fn in ARITH:
        m = rx.match(p)
        if not m:
            continue
        want = fn(float(m.group(1)), float(m.group(2)))
        got = max_number(o[i]) if NUMERIC_OPT.match(str(o[i])) else None
        if got is not None and abs(got - want) > 1e-9:
            errs.append(("WRONG_KEY", f"{qid} '{p}' = {want:g} but the key says {o[i]}"))
        break

    # Authoring scratch that leaked into text a child reads.
    for field in ("prompt", "passage", "explain"):
        if q.get(field) and SCRATCH.search(str(q[field])):
            errs.append(("SCRATCH", f"{qid} `{field}` contains authoring scratch text: "
                                    f"{SCRATCH.search(str(q[field])).group(0)!r}"))

    # The question must not TELL the reader the answer. Note this is deliberately not an
    # "answer text appears in the passage" check: literal recall (RL.K.1, RL.3.1) and
    # topic-sentence main idea (RI.2.2) are real skills where the answer is *supposed* to be
    # findable in the text. The defect is instructional meta-language addressed to the reader
    # — g3_v22_040's passage said "Here, the main idea is that solar panels convert sunlight
    # to electricity", then asked for the main idea.
    for field in ("passage", "prompt"):
        v = q.get(field)
        if v and META_TEXT.search(str(v)):
            errs.append(("SELF_ANS", f"{qid} `{field}` tells the reader the answer: "
                                     f"{META_TEXT.search(str(v)).group(0)!r}"))

    return errs


def tier1_advisory(q):
    """Signals worth a look that are too noisy to block on."""
    warns = []
    qid = q.get("id", "<no id>")
    i = key_index(q)
    if i is None or q.get("subject") != "math":
        return warns
    ex = str(q.get("explain") or "")
    key = str(options(q)[i])
    if ex and NUMERIC_OPT.match(key):
        kv = max_number(key)
        vals = [float(m.group(0).replace(",", "")) for m in NUM.finditer(ex)]
        if kv is not None and vals and not any(abs(v - kv) < 1e-9 for v in vals):
            warns.append(("EXPLAIN", f"{qid} explanation never states the keyed answer {key!r}"))
    return warns


# ── Tier 2: does it fit the grade it is filed under? ─────────────────────────

def tier2_grade_fit(q, strict=False):
    errs, warns = [], []
    qid = q.get("id", "<no id>")
    g = q.get("grade")
    if g not in GRADE_LEVEL:
        errs.append(("BAD_GRADE", f"{qid} unknown grade {g!r}"))
        return errs, warns

    std = q.get("standard")
    if not std:
        (errs if strict else warns).append(("NO_STD", f"{qid} has no `standard` code"))
    else:
        m = STD_LEVEL.match(str(std))
        if m:
            lvl = 0 if m.group(1) else int(m.group(2))
            # Pre-K legitimately cites Kindergarten codes: CCSS has no Pre-K tier.
            allowed = {GRADE_LEVEL[g]} | ({0} if g == "prek" else set())
            if lvl not in allowed:
                errs.append(("STD_GRADE", f"{qid} is filed as {g} but cites a grade-{lvl} standard {std!r}"))

    if q.get("subject") == "math":
        span = str(q.get("prompt", "")) + " " + keyed_answer(q)
        mx = max_number(span)
        if mx is not None and mx > NUM_CAP[g]:
            errs.append(("NUM_RANGE", f"{qid} uses {mx:g} in the question or answer; {g} tops out at {NUM_CAP[g]}"))

    if q.get("subject") not in TEXT_SUBJECTS and words(q.get("prompt")) > PROMPT_WORD_CAP[g]:
        errs.append(("PROMPT_LEN", f"{qid} prompt is {words(q.get('prompt'))} words; cap for {g} is {PROMPT_WORD_CAP[g]}"))

    lo, hi = DIFFICULTY_BAND[g]
    d = q.get("difficulty")
    if not isinstance(d, int) or isinstance(d, bool):
        errs.append(("DIFF_RANGE", f"{qid} difficulty={d!r} is not an integer"))
    elif not lo <= d <= hi:
        # Strict-only: 27 legacy G1/G2 items sit at difficulty 1 and are grandfathered. They are
        # still servable through the widening fallback, so this is a plausibility flag, not a bug.
        (errs if strict else warns).append(
            ("DIFF_RANGE", f"{qid} difficulty {d} is outside {g}'s plausible band {lo}-{hi}"))

    body = (q.get("passage") or "") + " " + (q.get("prompt") or "")
    if GRAPHIC.search(body):
        errs.append(("AGE", f"{qid} contains graphic-violence vocabulary: {GRAPHIC.search(body).group(0)!r}"))
    elif q.get("passage") and HEAVY.search(q["passage"]) and not FRAMING.search(q["passage"]):
        warns.append(("AGE", f"{qid} heavy history topic with no framing language"))

    if is_chinese(q):
        for f in ("traceMode", "pinyin", "meaning"):
            if not q.get(f):
                (errs if strict else warns).append(("TRACE", f"{qid} Chinese handwriting item missing `{f}`"))

    return errs, warns


# ── Tier 3: is it a fair test? ───────────────────────────────────────────────

def tier3_fairness(q):
    """Per-question fairness. Applied to new questions only — see tier3_batch for the bank."""
    errs = []
    if options(q) and uniquely_longest(q) and not q.get("closedSet"):
        errs.append(("LEN_TELL", f"{q.get('id')} correct option is the uniquely longest — "
                                 f"give the distractors equal weight"))
    o = options(q)
    if o is not None and len(o) != 4 and q.get("type") not in ("handwriting", "picture"):
        errs.append(("OPT_COUNT", f"{q.get('id')} has {len(o)} options, expected 4"))
    return errs


def tier3_batch(new_qs, baseline_qs=None):
    errs, warns = [], []
    mc = [q for q in new_qs if options(q) and key_index(q) is not None]
    if len(mc) < 40:
        if mc:
            warns.append(("POS_SKEW", f"only {len(mc)} new MC questions — position balance not checked"))
    else:
        pos = collections.Counter(key_index(q) for q in mc)
        for i, letter in enumerate("ABCD"):
            share = 100 * pos.get(i, 0) / len(mc)
            if not 20 <= share <= 30:
                errs.append(("POS_SKEW", f"answer {letter} is correct {share:.1f}% of the batch (want 20-30%)"))

    # Difficulty spread, per grade. A batch that clusters at one level adds nothing usable for
    # the child sitting at any other level — see DIFFICULTY_BAND for why that matters.
    by_grade = collections.defaultdict(list)
    for q in new_qs:
        if q.get("grade") in DIFFICULTY_BAND:
            by_grade[q["grade"]].append(q)

    base_by_grade = collections.defaultdict(list)
    for q in (baseline_qs or []):
        if q.get("grade") in DIFFICULTY_BAND:
            base_by_grade[q["grade"]].append(q)

    for g, qs_g in sorted(by_grade.items()):
        ds = [q["difficulty"] for q in qs_g if isinstance(q.get("difficulty"), int)]
        if len(ds) < DIFFICULTY_MIN_BATCH:
            continue
        counts = collections.Counter(ds)
        top_d, top_n = counts.most_common(1)[0]
        share = top_n / len(ds)
        if share > DIFFICULTY_MAX_SHARE:
            errs.append(("DIFF_SKEW", f"{g}: {top_n}/{len(ds)} ({share:.0%}) of the new questions "
                                      f"are difficulty {top_d}; max {DIFFICULTY_MAX_SHARE:.0%} at "
                                      f"one level. Spread them across {g}'s band "
                                      f"{DIFFICULTY_BAND[g][0]}-{DIFFICULTY_BAND[g][1]}"))
        base_ds = [q["difficulty"] for q in base_by_grade.get(g, [])
                   if isinstance(q.get("difficulty"), int)]
        if base_ds:
            new_mean = sum(ds) / len(ds)
            base_mean = sum(base_ds) / len(base_ds)
            if abs(new_mean - base_mean) > DIFFICULTY_MEAN_TOLERANCE:
                direction = "harder" if new_mean > base_mean else "easier"
                errs.append(("DIFF_SKEW", f"{g}: new questions average difficulty {new_mean:.2f} vs "
                                          f"{base_mean:.2f} in the existing bank — {direction} by "
                                          f"{abs(new_mean-base_mean):.2f}, over the "
                                          f"{DIFFICULTY_MEAN_TOLERANCE} tolerance"))
    return errs, warns


# ── Tier 4: marketing convenience. ADVISORY ONLY. ────────────────────────────

def tier4_advisory(q):
    """Never blocks. Flags things that would make a question awkward to publish, or an NYC
    claim a local parent could contest. A question failing every check here is still fine."""
    notes = []
    qid = q.get("id", "<no id>")
    if not is_nyc(q):
        return notes
    body = text_of(q, ("prompt", "options", "passage", "explain"))
    if VOLATILE.search(body):
        notes.append(("NYC_VOLATILE", f"{qid} states an NYC fare/official/count that expires"))
    if SUPERLATIVE.search(body) and not DIMENSION.search(body):
        notes.append(("NYC_SUPERLATIVE", f"{qid} NYC superlative with no stated dimension (area vs population)"))
    if q.get("subject") in ("social_studies", "reading", "ela", "science") and not q.get("source"):
        notes.append(("NYC_NO_SRC", f"{qid} asserts an NYC fact with no `source` field"))
    return notes


# ── reporting ────────────────────────────────────────────────────────────────

def coverage_report(qs):
    print("\nCurriculum coverage — the number that matters")
    hdr = f"  {'grade':<6}{'n':>6}{'coded':>8}{'%':>7}   top uncoded topics"
    print(hdr)
    for g in GRADES:
        sub = [q for q in qs if q.get("grade") == g]
        if not sub:
            continue
        coded = sum(1 for q in sub if q.get("standard"))
        un = collections.Counter(q.get("topic") for q in sub if not q.get("standard"))
        tops = ", ".join(f"{t} ({n})" for t, n in un.most_common(3)) or "-"
        print(f"  {g:<6}{len(sub):>6}{coded:>8}{100*coded/len(sub):>6.0f}%   {tops}")

    print("\nDifficulty spread — the adaptive engine needs supply at every level")
    print(f"  {'grade':<6}{'band':>6}" + "".join(f"{'d'+str(d):>8}" for d in range(1, 6)) + f"{'avg':>7}")
    for g in GRADES:
        sub = [q for q in qs if q.get("grade") == g and isinstance(q.get("difficulty"), int)]
        if not sub:
            continue
        c = collections.Counter(q["difficulty"] for q in sub)
        lo, hi = DIFFICULTY_BAND[g]
        cells = ""
        for d in range(1, 6):
            share = 100 * c.get(d, 0) / len(sub)
            mark = "" if lo <= d <= hi else "!"   # outside the band the engine can reach
            cells += f"{(f'{share:.0f}%' + mark):>8}"
        avg = sum(q["difficulty"] for q in sub) / len(sub)
        print(f"  {g:<6}{f'{lo}-{hi}':>6}{cells}{avg:>7.2f}")


def marketing_report(qs):
    nyc = [q for q in qs if is_nyc(q)]
    zh = [q for q in qs if is_chinese(q)]
    safe = sum(1 for q in qs if is_screenshot_safe(q))
    print("\nTier 4 — marketing pool (advisory; never gates a merge)")
    print(f"  screenshot-safe        {safe} ({100*safe/len(qs):.0f}%)")
    print(f"  NYC-flavored           {len(nyc)}  (of which screenshot-safe: "
          f"{sum(1 for q in nyc if is_screenshot_safe(q))})")
    print(f"  Chinese handwriting    {len(zh)}")
    notes = [n for q in qs for n in tier4_advisory(q)]
    by = collections.Counter(c for c, _ in notes)
    print(f"  NYC claims to review   {len(notes)} {dict(by) if by else ''}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bank", nargs="?", default="questions.json")
    ap.add_argument("--baseline", help="previous questions.json; ids present there are grandfathered")
    ap.add_argument("--strict", action="store_true", help="apply authoring rules to new questions")
    ap.add_argument("--report", action="store_true", help="coverage + marketing report")
    ap.add_argument("--cards", help="export the screenshot-safe pool for marketing")
    args = ap.parse_args()

    bank = json.load(open(args.bank, encoding="utf-8"))
    qs = bank["questions"]

    baseline_ids, baseline_qs = set(), []
    if args.baseline:
        baseline_qs = json.load(open(args.baseline, encoding="utf-8"))["questions"]
        baseline_ids = {q.get("id") for q in baseline_qs}
    new_qs = [q for q in qs if q.get("id") not in baseline_ids] if args.baseline else []

    errors, warnings = [], []

    # Tiers 1-2 apply to the whole bank, always.
    for q in qs:
        errors += tier1_correctness(q)
        warnings += tier1_advisory(q)
        e, w = tier2_grade_fit(q, strict=args.strict and q.get("id") not in baseline_ids)
        errors += e
        warnings += w

    # Tier 3 applies to newly authored questions only.
    if args.strict and new_qs:
        for q in new_qs:
            errors += tier3_fairness(q)
        e, w = tier3_batch(new_qs, baseline_qs)
        errors += e
        warnings += w

    scope = f"{len(new_qs)} new vs baseline" if args.baseline else "no baseline"
    print(f"bank v{bank.get('version')} — {len(qs)} questions ({scope}"
          + (", strict" if args.strict else "") + ")")

    if args.report:
        coverage_report(qs)
        marketing_report(qs)

    if warnings:
        grouped = collections.defaultdict(list)
        for code, msg in warnings:
            grouped[code].append(msg)
        print(f"\n{len(warnings)} advisory (does not fail the build)")
        for code in sorted(grouped, key=lambda c: -len(grouped[c])):
            msgs = grouped[code]
            print(f"  [{code}] x{len(msgs)}")
            for m in msgs[:3]:
                print(f"      {m}")
            if len(msgs) > 3:
                print(f"      ... and {len(msgs)-3} more")

    if args.cards:
        pool = [q for q in qs if is_screenshot_safe(q)]
        json.dump({"cards": pool}, open(args.cards, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\nwrote {len(pool)} screenshot-safe questions to {args.cards}")

    if errors:
        print(f"\n{len(errors)} ERROR(s) — tiers 1-3 only; Tier 4 never fails a build")
        for code, msg in errors[:60]:
            print(f"  [{code}] {msg}")
        if len(errors) > 60:
            print(f"  ... and {len(errors)-60} more")
        return 1

    print("\nOK — no errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
