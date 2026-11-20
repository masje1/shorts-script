---
name: shorts-script
description: Write, check, score or rewrite a YouTube Shorts script in the user's Script.txt house format (a claim-first hook, a question with the answer withheld, one step per line, an everyday comparison for every number, a late reframe, a 165 wpm budget, an ending that can loop back into the hook), with a checker script that scores drafts. Use whenever the user wants a script, hook or voiceover text for a short or reel, gives a topic "for a short", or points at a Script.txt or draft to check, tighten, shorten or fix, even without naming the skill. Not for shot lists, animation or video editing.
---

# Shorts script

Harper's taste, taught by his own shorts: `references/approved/` holds five he likes (`notes.md` says why each works) and `references/rejected.md` what he threw out and why. Imitate the shape, never the phrases or the facts. A brief that gives its own structure wins over the defaults here.

## Script.txt format
```
<Title>

<line 1>
<line 2>
...
<last line>

(N lines, about X s at 165 words per minute)
```
- One beat per line (each line becomes one shot); fragments fine.
- Numbers spelled out as said ("seventeen kilometres per second"); years and names with numbers stay digits (2024, Voyager 1). Metric, British spelling.
- No labels, notes or stage directions in the file. Footer exactly as the checker prints it.
- The last line may end on "…" or ":" and run straight into line 1 when the seam reads naturally. Never a CTA, outro or closing question.

## Eight rules
1. Line 1 is the claim, concrete from the first word: not a scene-setter, no greeting, no "did you know".
2. Line 2 makes it a question the viewer wants answered. The answer is withheld; each line after it is one step of the how and follows from the last.
3. Every big number gets an everyday comparison (17 km/s = twenty times a sniper rifle bullet). No room for the comparison: cut the number, never leave it bare.
4. Name each thing plainly and keep calling it that: no synonyms, no decoration.
5. A signpost ("Let me explain", "here's the crazy part") only where the next line is the real turn or answer; two at most.
6. A late line reframes it (what it means, what is surprising). Never a recap.
7. Budget at 165 wpm (an estimate, not a reading pace): Harper's approved scripts run 101-135 words, 34-42 s on screen. Take the target in seconds from the brief (45 if none): 45 s is about 110-135 words. Over budget: cut whole facts.
8. End on the idea, or loop back into line 1 when it reads naturally.

Write it so a ten-year-old follows it, told as a story: each line adds something new and follows from the last.

## Workflow
1. Read `references/approved/*.txt`, `references/approved/notes.md` and `references/rejected.md` before drafting.
2. Research 3-6 facts (NASA, ESA, journals, major outlets); unverifiable: cut or flag. Round as people speak. When the brief gives a `research.md` or figures, use them and check every comparison against them.
3. Draft in the format. Take the hook shape the idea already has (a flat claim, "this is X, but...", a myth flip, "X, but not Y"); never a template, and never the skeleton of the last script.
4. Run `python <skill>/scripts/check_script.py "<path>/Script.txt" --target <seconds from the brief, 45 if none> [--summary] [--json]` (`-` reads stdin; `pip install num2words` if missing). Fix every FAIL; fix each WARN or say why not. Rule IDs are in `references/rules.md`: search for an ID, don't read it whole.
5. Critique once, in this context, fix what you find, and don't show it. Does line 1 hit, or set a scene? Does line 2 undo line 1? Is anything called by two names? Does a signpost only announce more setup? Does every number land a comparison? Does each line follow from the last? Could a ten-year-old follow it? Could it be made from the last script by swapping nouns? Time-sensitive facts get a ready-to-paste after-date line.
6. Save to the path the brief gives, else `Script.txt` in the working folder.

## Editing or checking a draft
Run the checker, list problems worst first (rule ID, the quoted line, the fix), then edit that draft, changing as little as needed and keeping Harper's voice and facts. Never redo the research or rewrite the whole script. Give both scores.

## Reply
The script (or its path); checker result and kept WARNs with reasons; each fact and its source, flagging anything unverified; the loop seam if there is one (last line + line 1); two alternative hooks of different shapes. About 300 words around the script.
