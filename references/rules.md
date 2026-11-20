# Rule IDs (lookup: search for an ID, don't read the whole file)

What `scripts/check_script.py` prints. Thresholds are calibrated on Harper's five approved scripts (`references/approved/`): none of them FAILs. FAIL = must fix, WARN = fix or say why not, TIP = a nudge, not scored. What the checker cannot see (a vague line 1, line 2 contradicting line 1, synonyms for one thing, a signpost that only announces more setup) is judged in the critique pass in `SKILL.md` and by the examples in `references/approved/notes.md` and `references/rejected.md`.

Budget at 165 wpm: 30 s = 75-85 words · 40 s = 100-115 · 45 s = 110-135 · 60 s = 150-175. Harper's five approved scripts run 101-135 words: 37-49 s by this estimate, but 34-42 s on screen (he speaks and is cut faster than 165 wpm). Take `--target` from the brief; with none, use 45.

- B1 WARN/FAIL: words against the budget for `--target`. Pass within 10%, WARN within 20%, FAIL beyond. Cut whole facts, never "talk faster".
- H6 FAIL: no greeting or intro in the opening ("Hey guys", "In this video", "Today we're", "Did you know", "Let's dive in").
- H2 WARN: hook (first sentence) aim ~13 words, warn above 20.
- H4 TIP: the hook is a question or an extreme claim.
- O1 TIP: a question, bet or open loop in the ~40 words after the hook.
- E0 WARN: never ~80 spoken words without a number, question, "but" or teaser.
- E9 WARN: at least one "but" twist. E9+ WARN: two or more in an Argument-engine script (`--engine argument`).
- T2 WARN: at least one number, or the proof is on screen.
- E13 WARN: at least one felt comparison somewhere (than / like / compared / times).
- P1 WARN: payoff at 50-85% of the runtime (only checked when the payoff line is labelled `ANSWER:`). P2b TIP: the payoff on a line of 8 words or fewer.
- C1 WARN: the last line ends on "…" or ":" and runs into line 1. Optional: fine to skip when the last line lands on its own.
- C4 FAIL: no recap, CTA, "like and subscribe" or outro.
- W1 WARN: one idea per sentence; median 15 words or fewer, none over ~35.
- W2 WARN: with `--engine journey`, "you/your" at least 2.5 per 100 words (INFO otherwise).
- W4 TIP: at least two "this / here / these" pointing at the visuals.
- W6 WARN: at most 3 intensifiers ("crazy", "insane", "wild"...).
- S1 WARN: numbers spelled out as said; years and decades stay digits; a digit after a capitalised word that is not a common sentence starter is read as part of a name ("Voyager 1" is fine). Known blind spot: "On Venus 465 degrees" is exempted too; read the digits yourself.
- S2 WARN: title on the first line, then a blank line.
- S3 WARN: the footer is exactly the one the checker prints.
- Q1 WARN: three or more signpost phrases ("here's the...", "here's how", "let me explain", "there is a catch"). One or two are fine when each leads into real content.
- Q2 WARN: no two lines in a row start with the same And / So / But / Because.
- Q3 TIP: a number with no comparison in its line or the next (number pairs and self-explaining durations can trip it; judge it).
