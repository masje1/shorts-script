"""Score a YouTube Shorts script against the measurable rules in references/rules.md.

Usage:
    python check_script.py Script.txt [--target 40] [--engine journey|argument] [--summary] [--json]

Accepts the user's Script.txt house format:
    <Title>
    <blank line>
    one line per beat / sentence
    ...
    (N lines, about X s at 165 words per minute)     <- footer, ignored when scoring

Also accepted: optional label prefixes ("HOOK: ...", "ANSWER: ..."), "# Name" to hold several
scripts in one file, "@target 40" / "@engine journey" directives, and "//" comment lines.
Label the payoff line "ANSWER:" to get the payoff-position check.

Severity: FAIL = a MUST rule, WARN = a SHOULD rule, TIP = a TRY rule (not scored).
Thresholds are calibrated so Harper's five approved scripts (references/approved/) pass with no FAIL.
"""
import argparse, json, re, statistics as st, sys

try:
    from num2words import num2words
except ImportError:
    num2words = None

PACE_WPM = 165  # the user's delivery pace (2026-11-09; was 180)
LABELS = {'HOOK', 'QUESTION', 'BETS', 'LOOP', 'CONTEXT', 'STEP', 'WOW', 'TWIST', 'STAKES',
          'ANSWER', 'PAYOFF', 'REAL', 'REFLECT', 'REFRAME', 'CLIP', 'CTA'}

NUMBER_WORDS = (r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|"
                r"sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
                r"hundred|thousand|million|billion|trillion|half|percent|times)\b")
BANNED_OPENERS = r"\b(hey|hi|hello|welcome|guys|in this video|today we|today i|let'?s talk|let'?s dive|did you know)\b"
BANNED_ANY = r"(like,? comment|smash (that|the)|don'?t forget to|without further ado|today we learned|to recap|in summary|thanks for watching)"
LOOP_PHRASES = (r"(turns out|weirder than|crazier than|something (crazy|weird)|here'?s (what|the)|let me explain|guess|"
                r"hold on|get this|truly insane|craziest|crazy part|not even close|the catch)")
EXTREME = r"\b(\w+est|ever|most|never|only|insane|really|actually)\b"
MOMENTUM = LOOP_PHRASES + r"|\?|\bbut\b|\d|" + NUMBER_WORDS + r"|\b(option|imagine|compared)\b"
COMPARISON = r"\b(than|like|compared|size of|times|as \w+ as)\b"
DEICTIC = r"\b(this|here|these)\b"
INTENSIFIERS = r"\b(crazy|craziest|insane|insanely|terrifying|whopping|wild|mind-?blowing)\b"
CTA_WORDS = (r"\b(subscribe|follow (me|us|for|along)|watch (the |my |our )?(next|full|part|more|video|episode)"
             r"|(next|longer|full|new) (video|episode)|part (two|2)|link in|smash|hit the (like|bell)"
             r"|like,? (and|&) |comment below)\b")
CTA_LOOP = r"(if you want to (know|see|find)|to (see|find out|know)|what they found|what happens|next|longer video|part two)"
YOU = r"\byou(r|'re|'d|'ll|'ve|rself)?\b"
YEAR = r"^(1[5-9]\d\d|20\d\d)s?$"  # years and decades stay as digits in the house style
TRAIL_OFF = r"(\.\.\.|…|:)\s*$"

MOMENTUM_MAX_WORDS = 80  # longest run of spoken words with no number / question / "but" / teaser
HOOK_MAX_WORDS = 20  # Harper's hooks run from 6 to ~20 words; above this is a WARN, never a FAIL


def spoken_words(tok):
    """Words actually said: digits expanded (1,200 -> one thousand two hundred), hyphenated words split."""
    t = tok.strip('.,?!:;"()\'…').replace(',', '').rstrip('%/')
    if re.fullmatch(r'\d+(\.\d+)?', t):
        if re.fullmatch(YEAR, t):
            return 2  # "twenty twenty-four"
        if not num2words:
            return 3
        if '.' in t:
            a, b = t.split('.')
            return len(num2words(int(a)).replace('-', ' ').split()) + 1 + len(b)
        return len(num2words(int(t)).replace('-', ' ').replace(',', '').split())
    if not re.search(r'[A-Za-z0-9]', tok):
        return 0
    return len([p for p in t.split('-') if p])


def parse(text):
    scripts, cur = [], None

    def new(name):
        s = {'name': name, 'lines': [], 'target': None, 'engine': None, 'title': None, 'footer': None}
        scripts.append(s)
        return s

    raw = text.splitlines()
    for i, line in enumerate(raw):
        ln = line.strip()
        if not ln or ln.startswith('//'):
            continue
        if ln.startswith('# '):
            cur = new(ln[2:].strip())
            continue
        if cur is None:
            cur = new('draft')
        m = re.match(r'@(target|engine)\s+(\S+)', ln)
        if m:
            cur[m.group(1)] = int(m.group(2)) if m.group(1) == 'target' else m.group(2).lower()
            continue
        if re.fullmatch(r'\(.*\)', ln):
            cur['footer'] = ln
            continue
        # house format: the first line, followed by a blank line, is the title
        if not cur['lines'] and cur['title'] is None and i + 1 < len(raw) and not raw[i + 1].strip() \
                and not re.match(r'[A-Z]+\s*:', ln):
            cur['title'] = ln
            if cur['name'] == 'draft':
                cur['name'] = ln
            continue
        lab, txt = None, ln
        m = re.match(r'([A-Z]+)\s*:\s*(.*)', ln)
        if m and m.group(1) in LABELS:
            lab, txt = m.group(1), m.group(2)
        cur['lines'].append((lab, txt))
    return [s for s in scripts if s['lines']]


_SIGN_NOUN = r"the (trick|catch|crazy|weird|best|part|thing|secret|twist|kicker|truth|problem)"
SIGNPOST = (r"(here['’]?s (how|why|" + _SIGN_NOUN + r")|here is (how|why|" + _SIGN_NOUN + r")"
            r"|let me explain|there is a catch|the catch\b|so essentially)")
SIGNPOST_WARN_AT = 3  # Harper's own scripts use up to two; three or more reads as formula
OPENER_WORDS = {'and', 'so', 'but', 'because'}
QUANT_WORDS = {'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
               'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty', 'thirty', 'forty',
               'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred', 'thousand', 'million', 'billion',
               'trillion'}
COMPARISON_EXT = COMPARISON + r"|\b(same|every|out of|per cent|percent|as much|as many)\b|%"
# Capitalised words that usually start a sentence, so a number after them is a quantity, not part of a name
SENTENCE_STARTERS = {'only', 'about', 'nearly', 'over', 'around', 'almost', 'roughly', 'just', 'that', 'it', 'its',
                     'they', 'we', 'so', 'but', 'and', 'the', 'a', 'an', 'in', 'on', 'at', 'by', 'for', 'with',
                     'every', 'each', 'all', 'up', 'more', 'less', 'now', 'then', 'there', 'this', 'these',
                     'after', 'because', 'even', 'since', 'when', 'some', 'today', 'still', 'our', 'you', 'if',
                     'while', 'before', 'during', 'once', 'both', 'another', 'most', 'many', 'few', 'under',
                     'between', 'from', 'to', 'of', 'is', 'are', 'was', 'were', 'has', 'have', 'had', 'as',
                     'not', 'no', 'yes', 'your', 'their', 'his', 'her', 'my', 'what', 'why', 'how', 'where',
                     'who', 'which', 'than', 'or', 'nor', 'yet', 'also', 'soon', 'later', 'next', 'last',
                     'first', 'only', 'until', 'though', 'although', 'whenever', 'unless', 'maybe', 'then'}
DIGIT_RUN = r'\d[\d,.]*'


def count_signposts(low):
    """Signpost phrases ("here's the...", "let me explain", "there is a catch") in lower-cased text."""
    return len(re.findall(SIGNPOST, low))


def repeated_openers(texts):
    """Indices of lines that start with the same And/So/But/Because as the line before."""
    out = []
    for i in range(1, len(texts)):
        a, b = (re.match(r"\w+", t.lower()) for t in (texts[i - 1], texts[i]))
        if a and b and a.group(0) == b.group(0) and b.group(0) in OPENER_WORDS:
            out.append(i)
    return out


def is_name_word(prev):
    """A capitalised word that is probably a proper noun ("Voyager" in "Voyager 1"), not a sentence starter."""
    p = prev.strip('.,?!:;"()…\'')
    return p[:1].isupper() and p.lower() not in SENTENCE_STARTERS


def uncompared_numbers(texts):
    """Indices of lines with a quantity (not a year, not part of a name) and no comparison in that line or the next."""
    flagged = []
    for i, line in enumerate(texts):
        toks = line.split()
        has_quantity = False
        for j, t in enumerate(toks):
            c = t.strip('.,?!:;"()…\'')
            parts = [c] if re.fullmatch(DIGIT_RUN, c) else c.split('-')
            quantity = any((re.fullmatch(DIGIT_RUN, p) and not re.fullmatch(YEAR, p.rstrip('.,')))
                           or p.lower() in QUANT_WORDS for p in parts)
            if quantity and not (j > 0 and is_name_word(toks[j - 1])):
                has_quantity = True
                break
        if has_quantity and not any(re.search(COMPARISON_EXT, texts[k].lower()) for k in range(i, min(i + 2, len(texts)))):
            flagged.append(i)
    return flagged


def check(script, target=None, engine=None):
    lines = script['lines']
    target = target or script['target']
    engine = engine or script['engine']
    texts = [t for _, t in lines]
    full = ' '.join(texts)
    low = full.lower()
    sw = [sum(spoken_words(t) for t in tx.split()) for tx in texts]
    total = sum(sw)
    est = total / PACE_WPM * 60
    starts, acc = [], 0  # spoken-word offset where each line starts
    for s in sw:
        starts.append(acc); acc += s
    slen = [len(s.split()) for s in re.split(r'(?<=[.?!…])\s+', full) if s.strip()]
    res = []

    def add(rule, ok, msg, sev):
        res.append({'rule': rule, 'status': 'PASS' if ok else sev, 'msg': msg})

    footer = f"({len(texts)} lines, about {est:.0f} s at {PACE_WPM} words per minute)"
    if target:
        budget = target * PACE_WPM / 60
        dev = abs(total - budget) / budget
        # Harper's approved scripts run 101-135 words, so 10% passes, up to 20% warns, beyond that fails
        add('B1', dev <= 0.10,
            f'{total} spoken words vs ~{budget:.0f} budget for {target} s (pass within 10%, warn within 20%)',
            'WARN' if dev <= 0.20 else 'FAIL')

    # Hook
    hook = ' '.join(t for l, t in lines if l == 'HOOK') or re.split(r'(?<=[.?!])\s+', texts[0])[0]
    hw = sum(spoken_words(t) for t in hook.split())
    add('H6', not re.search(BANNED_OPENERS, ' '.join(texts[:2]).lower()), 'no greeting / intro phrase in the opening', 'FAIL')
    add('H2', hw <= HOOK_MAX_WORDS, f'hook is {hw} words, ~{hw / PACE_WPM * 60:.1f} s (aim ~13, warn above {HOOK_MAX_WORDS})', 'WARN')
    add('H4', '?' in hook or bool(re.search(EXTREME, hook.lower())), 'hook is a question or an extreme claim', 'TIP')
    early = ' '.join(t for t, s0 in zip(texts[1:], starts[1:]) if s0 < 40).lower()
    add('O1', '?' in early or bool(re.search(LOOP_PHRASES + r'|\bimagine\b', early)),
        'bets or an open loop in the first ~40 words after the hook', 'TIP')

    # Engine
    marks = [s0 for t, s0 in zip(texts, starts) if re.search(MOMENTUM, t.lower())] + [total]
    longest = max(b - a for a, b in zip([0] + marks, marks))
    add('E0', longest <= MOMENTUM_MAX_WORDS,
        f'longest run with no number / question / "but" / teaser: {longest} words, ~{longest / PACE_WPM * 60:.0f} s '
        f'(aim ≤{MOMENTUM_MAX_WORDS} words)', 'WARN')
    nbut = len(re.findall(r'\bbut\b', low))
    add('E9', nbut >= 1, f'{nbut} "but" twist(s) (aim ≥1)', 'WARN')
    if engine == 'argument':
        add('E9+', nbut >= 2, 'Argument engine: ≥2 "but" twists', 'WARN')
    add('T2', bool(re.search(r'\d|' + NUMBER_WORDS, low)), 'at least one number (or make sure the proof is on screen)', 'WARN')
    add('E13', bool(re.search(COMPARISON, low)), 'at least one felt comparison (than / like / compared / times)', 'WARN')

    # Payoff
    ans = [i for i, (l, _) in enumerate(lines) if l in ('ANSWER', 'PAYOFF')]
    if ans and total:
        pos = starts[ans[0]] / total
        add('P1', 0.5 <= pos <= 0.9 or pos < 0.1, f'first payoff at {pos * 100:.0f}% (aim 50-85%, or answer-first + re-open)', 'WARN')
        add('P2b', any(len(texts[i].split()) <= 8 for i in ans), 'a payoff line of ≤8 words', 'TIP')
    else:
        res.append({'rule': 'P1', 'status': 'INFO', 'msg': 'label the payoff line "ANSWER:" to check its position'})

    # Ending: may loop back into line 1 when the seam reads naturally (WARN if not); never a CTA (FAIL)
    last = texts[-1].lower()
    is_cta = bool(re.search(CTA_WORDS, last) or re.search(CTA_LOOP, last) and re.search(r'\bif you want\b', last))
    loops = bool(re.search(TRAIL_OFF, texts[-1]))
    if is_cta:
        msg = 'last line is a CTA; no CTA, end on the idea or loop back into line 1'
    elif not loops:
        msg = 'no loop ending (ends on "…" or ":" and runs into line 1); fine if the last line lands on its own'
    else:
        msg = 'ends on a loop back into line 1 (read the last line + line 1 together to check the seam)'
    add('C1', loops and not is_cta, msg, 'WARN')
    add('C4', not is_cta and not re.search(BANNED_ANY, low), 'no recap, no CTA, no "like, comment & subscribe", no outro', 'FAIL')

    # Language
    add('W1', st.median(slen) <= 15 and max(slen) <= 35,
        f'sentence length median {st.median(slen):.0f}, max {max(slen)} (aim 10-15, max ~30)', 'WARN')
    nw = max(1, len([w for w in full.split() if re.search(r'[A-Za-z0-9]', w)]))
    you = len(re.findall(YOU, low)) / nw * 100
    if engine == 'journey':
        add('W2', you >= 2.5, f'"you/your" {you:.1f} per 100 words (journey: aim ≥2.5)', 'WARN')
    else:
        res.append({'rule': 'W2', 'status': 'INFO', 'msg': f'"you/your" {you:.1f} per 100 words (≥2.5 if this is a hypothetical/journey short)'})
    dei = len(re.findall(DEICTIC, low))
    add('W4', dei >= 2, f'{dei} this/here/these pointers to visuals (aim ≥2)', 'TIP')
    inten = len(re.findall(INTENSIFIERS, low))
    add('W6', inten <= 3, f'{inten} intensifier(s) (aim ~1, max 3)', 'WARN')

    # House style
    digits = [t for prev, t in re.findall(r"(?:([A-Za-z]+)\s+)?(" + DIGIT_RUN + ")", full)
              if not re.fullmatch(YEAR, t.rstrip('.,')) and not (prev and is_name_word(prev))]

    # Quality checks (mechanical only; the rest is judged in the critique pass)
    n_sign = count_signposts(low)
    add('Q1', n_sign < SIGNPOST_WARN_AT,
        f'{n_sign} signpost phrase(s) ("here\'s the…", "let me explain"…); aim for at most 2, each leading into real content', 'WARN')
    rep = repeated_openers(texts)
    add('Q2', not rep, 'no two lines in a row start with the same And/So/But/Because'
        + (f' — lines {", ".join(str(i + 1) for i in rep)}' if rep else ''), 'WARN')
    unc = uncompared_numbers(texts)
    add('Q3', not unc, 'every number has a comparison in its line or the next'
        + (f' — check lines {", ".join(str(i + 1) for i in unc)}' if unc else ''), 'TIP')
    add('S1', not digits, 'numbers spelled out as spoken (years/decades may stay as digits)'
        + (f' — found: {", ".join(digits[:6])}' if digits else ''), 'WARN')
    add('S2', script['title'] is not None, 'title on the first line, then a blank line', 'WARN')
    if script['footer'] is not None:
        add('S3', script['footer'] == footer, f'footer matches the script: {footer}', 'WARN')
    else:
        add('S3', False, f'add the footer: {footer}', 'WARN')
    return {'name': script['name'], 'lines': len(texts), 'spoken_words': total, 'seconds': round(est, 1),
            'footer': footer, 'results': res}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file', help='Script.txt, or - to read from stdin')
    ap.add_argument('--target', type=int, help='target length in seconds')
    ap.add_argument('--engine', choices=['journey', 'argument'])
    ap.add_argument('--summary', action='store_true', help='one line per script')
    ap.add_argument('--json', action='store_true', help='machine-readable output')
    a = ap.parse_args()
    if a.file == '-':
        sys.stdin.reconfigure(encoding='utf-8')
        text = sys.stdin.read()
    else:
        text = open(a.file, encoding='utf-8').read()
    reps = [check(s, a.target, a.engine) for s in parse(text)]
    if not reps:
        print('no script found in the input (an empty file, or a title with no lines)', file=sys.stderr)
        sys.exit(1)
    if a.json:
        print(json.dumps(reps, indent=1, ensure_ascii=False))
        return
    for r in reps:
        scored = [x for x in r['results'] if x['status'] in ('PASS', 'WARN', 'FAIL')]
        fails = [x['rule'] for x in scored if x['status'] == 'FAIL']
        warns = [x['rule'] for x in scored if x['status'] == 'WARN']
        secs = re.search(r'about (\d+) s', r['footer']).group(1)  # same figure as the footer, no double rounding
        head = (f"{r['name']}: {sum(x['status'] == 'PASS' for x in scored)}/{len(scored)} pass · {len(fails)} fail · "
                f"{len(warns)} warn · {r['spoken_words']} spoken words · ~{secs} s at {PACE_WPM} WPM")
        if a.summary:
            print(head + (f" · FAIL {','.join(fails)}" if fails else '') + (f" · WARN {','.join(warns)}" if warns else ''))
            continue
        print('\n' + head)
        for x in r['results']:
            print(f"  {x['status']:4s} {x['rule']:6s} {x['msg']}")
        print(f"  Footer: {r['footer']}")


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
