# shorts-script

A Claude skill that writes, checks and rewrites YouTube Shorts scripts for one specific voice: the "harper." space and science channel. A script is 34-42 s of spoken lines, told so a ten-year-old follows it. It opens on a concrete claim, asks the question the viewer wants answered, builds the answer one step per line, gives every number an everyday comparison, and ends on a reframe.

The taste is the point, not a setting: `references/approved/` holds five of the channel's own shorts, `references/approved/notes.md` says why each works, and `references/rejected.md` lists what the author threw out and why.

## Reads
- A topic or brief ("a short on how Voyager still has power, 52-56 s, spend most of it on the generator"), optionally with a research file of figures to use.
- Or an existing `Script.txt` to check, tighten or fix. A fix edits that draft; it never redoes the research or the whole script.

## Writes
`Script.txt` (or the path the brief gives): a title, a blank line, one spoken line per line, and a footer exactly as the checker prints it. Numbers are spelled out as said (years stay digits), British spelling, no labels or stage directions. The last line may run on into line 1 when the seam reads naturally; never a call to action.

Sample brief: *a short on how Voyager still has power, no solar panels, about 54 s.* Sample output:

```
How Voyager still has power

Voyager's three generators have worked for forty-nine years with no moving parts.
So where does the electricity come from?
Not solar panels. At Neptune, sunlight is like a desk lamp at the far end of a football field.
The generators run on plutonium, whose atoms keep breaking apart and giving off heat.
That keeps one side of each generator near a thousand degrees, four times hotter than your oven.
The other side faces space, seven hundred degrees cooler but still hotter than boiling water.
Between them sit hundreds of pairs of metal strips.
In each pair, one end is hot, one is cold, and that gap pushes electricity through the metal.
But only six per cent of the heat becomes power, enough for eight old light bulbs at launch.
The plutonium is fading, so Voyager has less than half its launch power.
So for now, the cold of empty space is what keeps Voyager alive.

(11 lines, about 57 s at 165 words per minute)
```

## Install
Copy this folder to `~/.claude/skills/shorts-script`. Needs Python 3 and `pip install num2words`.

## The checker
```
python scripts/check_script.py Script.txt --target 45 [--summary] [--json]
```
`--target` is the length in seconds from the brief (45 if none). FAIL means fix it, WARN means fix it or say why not, TIP is a nudge. Rule IDs are explained in `references/rules.md`. The checker only measures what code can see (length, hook, signpost count, repeated openers, spelling of numbers, the ending); whether line 1 really hits, or whether a signpost earns its place, is judged by the skill's critique pass against the examples.

## Tests and evals
- Tests: `python -m unittest discover -s scripts -p "test_*.py"`. They pin the checker's rules and check that none of the five approved scripts FAILs.
- Evals: `evals/` holds five cases (a prompt, input files and graders each): new scripts, a fix of a flawed draft, a draft with forced signposts.

## Layout
```
SKILL.md                  the workflow and eight rules
references/approved/      five approved scripts + notes.md
references/rejected.md    what was thrown out, and why
references/rules.md       what each checker rule ID means
scripts/                  check_script.py and its tests
evals/                    test cases
```

## What it does not do
Shot lists, animation, video editing, or sourcing real footage. It makes the script and nothing else.
