"""Tests for check_script.py, calibrated on Harper's five approved scripts.

Run from the skill folder:  python -m unittest discover -s scripts -p "test_*.py" -v
"""
import glob
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import subprocess  # noqa: E402

from check_script import (parse, check, count_signposts, repeated_openers,  # noqa: E402
                          uncompared_numbers, QUANT_WORDS)

APPROVED = sorted(glob.glob(os.path.join(SKILL, 'references', 'approved', '*.txt')))


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def load(path):
    return parse(read(path))[0]


def script_of(*lines, title='T'):
    return parse(title + '\n\n' + '\n'.join(lines))[0]


def row(script, rule, target=None):
    return next(r for r in check(script, target=target)['results'] if r['rule'] == rule)


def words(n):
    return ' '.join(['word'] * n) + '.'


class Calibration(unittest.TestCase):
    def test_hook_over_20_words_is_warn_not_fail(self):
        self.assertEqual(row(script_of(words(21), 'Next.'), 'H2')['status'], 'WARN')

    def test_hook_of_20_words_passes(self):
        self.assertEqual(row(script_of(words(20), 'Next.'), 'H2')['status'], 'PASS')

    def test_no_loop_is_warn(self):
        self.assertEqual(row(script_of('Hook line.', 'And that is why.'), 'C1')['status'], 'WARN')

    def test_loop_passes(self):
        self.assertEqual(row(script_of('Hook line.', 'And it is already so far away that…'), 'C1')['status'], 'PASS')

    def test_cta_is_fail(self):
        s = script_of('Hook line.', 'Middle.', 'If you want to see more, subscribe.')
        self.assertEqual(row(s, 'C4')['status'], 'FAIL')
        self.assertNotEqual(row(s, 'C1')['status'], 'PASS')


class Budget(unittest.TestCase):
    # Target 40 s = 110 words at 165 wpm. Within 10% passes, within 20% warns, beyond 20% fails.
    def test_b1_bands(self):
        for n, status in ((110, 'PASS'), (120, 'PASS'), (126, 'WARN'), (140, 'FAIL'), (95, 'WARN'), (80, 'FAIL')):
            with self.subTest(words=n):
                self.assertEqual(row(script_of(words(n), 'Next.'), 'B1', target=40)['status'], status)

    def test_approved_scripts_pass_b1_at_45_s(self):
        # 45 s is the default target in SKILL.md; Harper's approved scripts run 101-135 words.
        for path in APPROVED:
            with self.subTest(script=os.path.basename(path)):
                self.assertNotEqual(row(load(path), 'B1', target=45)['status'], 'FAIL')


class QualityChecks(unittest.TestCase):
    def test_digits_after_sentence_starters_are_still_flagged(self):
        for line in ('After 47 years, it still works.', 'Because 3 engines failed.', 'Even 2 degrees matters.',
                     'Today 5 probes are flying.', 'Our 3 rovers are old.', 'If 4 fail, it stops.'):
            with self.subTest(line=line):
                self.assertEqual(row(script_of('Hook line.', line, 'Last.'), 'S1')['status'], 'WARN')
                self.assertEqual(uncompared_numbers([line]), [0])

    def test_signposts_are_counted(self):
        self.assertEqual(count_signposts("but here's the trick. here's how it works. let me explain."), 3)

    def test_two_signposts_pass_three_warn(self):
        two = script_of('Hook line.', "Let me explain.", "Here's the part people miss.", 'Last.')
        three = script_of('Hook line.', "Let me explain.", "Here's the part people miss.", "Here's how it works.")
        self.assertEqual(row(two, 'Q1')['status'], 'PASS')
        self.assertEqual(row(three, 'Q1')['status'], 'WARN')

    def test_repeated_openers(self):
        self.assertEqual(repeated_openers(['So it works.', 'So it flies.']), [1])
        self.assertEqual(repeated_openers(['So it works.', 'But it flies.']), [])

    def test_repeated_openers_is_a_warn(self):
        s = script_of('Hook line.', 'So it works.', 'So it flies.')
        self.assertEqual(row(s, 'Q2')['status'], 'WARN')

    def test_uncompared_numbers(self):
        self.assertEqual(uncompared_numbers(['It moves at seventeen kilometres per second.',
                                             "That's about twenty times faster than a bullet."]), [])
        self.assertEqual(uncompared_numbers(['It weighs nine hundred kilos.', 'It was built in a lab.']), [0])
        self.assertEqual(uncompared_numbers(['Only ten people were picked.', 'It was a lab.']), [0])

    def test_names_and_years_are_not_quantities(self):
        self.assertEqual(uncompared_numbers(['Voyager 1 launched in 1977.']), [])
        self.assertEqual(uncompared_numbers(['Artemis two flew in 2025.']), [])

    def test_uncompared_numbers_is_a_tip_not_a_warn(self):
        # It warns on 3 of the 5 approved scripts (number pairs and self-explaining durations), so it is a nudge only.
        s = script_of('Hook line.', 'It weighs nine hundred kilos.', 'It was built in a lab.', 'Last.')
        self.assertEqual(row(s, 'Q3')['status'], 'TIP')

    def test_pointers_and_open_loop_are_tips_not_warns(self):
        for path in APPROVED:
            with self.subTest(script=os.path.basename(path)):
                for rule in ('W4', 'O1'):
                    self.assertNotEqual(row(load(path), rule)['status'], 'WARN')

    def test_s1_ignores_digits_in_names(self):
        voyager = [p for p in APPROVED if p.endswith('voyager.txt')][0]
        self.assertEqual(row(load(voyager), 'S1')['status'], 'PASS')


class Robustness(unittest.TestCase):
    def test_empty_text_parses_to_nothing(self):
        self.assertEqual(parse(''), [])

    def test_one_line_script_scores(self):
        res = check(script_of('One line only.'))
        self.assertTrue(res['results'])

    def test_stdin_and_multi_script(self):
        text = ''.join('# %s\n%s\n' % (os.path.basename(p), read(p)) for p in APPROVED)
        out = subprocess.run([sys.executable, os.path.join(HERE, 'check_script.py'), '-', '--summary'],
                             input=text.encode('utf-8'), capture_output=True)
        self.assertEqual(out.returncode, 0, out.stderr.decode('utf-8', 'replace'))
        self.assertEqual(len(out.stdout.decode('utf-8').strip().splitlines()), 5)


def run_cli(text, *args):
    return subprocess.run([sys.executable, os.path.join(HERE, 'check_script.py'), '-', *args],
                          input=text.encode('utf-8'), capture_output=True)


def documented_ids(text):
    bullets = ' '.join(line for line in text.splitlines() if line.startswith('- '))
    return set(re.findall(r'(?<![A-Za-z0-9])([A-Z]\d{1,2}(?:\+|b)?)(?![A-Za-z0-9+])', bullets))


class Minors(unittest.TestCase):
    def test_answer_label_with_no_words_does_not_crash(self):
        check(script_of('ANSWER: …'))  # zero spoken words in total

    def test_empty_input_is_an_error_not_silence(self):
        for text in ('', 'Title only\n\n'):
            with self.subTest(text=text):
                out = run_cli(text)
                self.assertEqual(out.returncode, 1)
                self.assertIn('no script', out.stderr.decode('utf-8').lower())

    def test_cta_detection_needs_a_real_call_to_action(self):
        for last, is_cta in (('And we can still follow it…', False), ('This video was filmed in 1999.', False),
                             ('Watch the next video.', True), ('Follow for more.', True), ('Subscribe.', True),
                             ('If you want to see what happened, subscribe.', True)):
            with self.subTest(last=last):
                s = script_of('Hook line.', 'Middle.', last)
                self.assertEqual(row(s, 'C4')['status'] == 'FAIL', is_cta)

    def test_signposts_versus_content(self):
        for text, n in (("here's the water they drink.", 0), ("here is the trick.", 1), ("so essentially, it works.", 1),
                        ("here's the crazy part.", 1), ("here's the part most people miss.", 1),
                        ("there is a catch.", 1), ("here's how it works.", 1), ("let me explain.", 1)):
            with self.subTest(text=text):
                self.assertEqual(count_signposts(text), n)

    def test_summary_seconds_match_the_footer(self):
        out = run_cli('T\n\n' + words(102) + '\nLast.\n').stdout.decode('utf-8')  # 103 words = 37.45 s
        head = next(line for line in out.splitlines() if 'spoken words' in line and 'pass' in line)
        self.assertIn('103 spoken words · ~37 s at 165 WPM', head)
        self.assertIn('about 37 s at 165 words per minute', out)

    def test_quantity_words_are_an_explicit_list(self):
        self.assertIn('seventeen', QUANT_WORDS)
        for w in ('one', 'times', 'half', 'percent', 'b'):
            self.assertNotIn(w, QUANT_WORDS)


class Docs(unittest.TestCase):
    def test_documented_ids_helper(self):
        self.assertEqual(documented_ids('- Z9 WARN: x. Z9b TIP.\nnot a bullet A1'), {'Z9', 'Z9b'})

    def test_every_documented_rule_id_is_printed_by_the_checker(self):
        rules = read(os.path.join(SKILL, 'references', 'rules.md'))
        scripts = [load(p) for p in APPROVED] + [script_of('Hook line.', 'ANSWER: The answer.', 'And so on…')]
        printed = set()
        for s in scripts:
            for eng in (None, 'journey', 'argument'):
                printed |= {r['rule'] for r in check(s, target=40, engine=eng)['results']}
        self.assertEqual(documented_ids(rules) - printed, set())

    def test_every_rule_id_is_documented(self):
        rules = read(os.path.join(SKILL, 'references', 'rules.md'))
        scripts = [load(p) for p in APPROVED] + [script_of('Hook line.', 'ANSWER: The answer.', 'And so on…')]
        ids = set()
        for s in scripts:
            for eng in (None, 'journey', 'argument'):
                ids |= {r['rule'] for r in check(s, target=40, engine=eng)['results']}
        for rule_id in sorted(ids):
            with self.subTest(rule=rule_id):
                self.assertRegex(rules, r'(?<![A-Za-z0-9+])' + re.escape(rule_id) + r'(?![A-Za-z0-9+])')


class ApprovedScripts(unittest.TestCase):
    # WARN rule IDs the checker gives each approved script today. If a checker change makes a script of
    # Harper's warn on something new, this fails so the change is noticed (and the rule re-judged).
    WARN_BASELINE = {
        'astronauts.txt': [],
        'hottest.txt': ['E13'],
        'iss-air.txt': ['C1'],
        'moon.txt': ['C1', 'E13', 'T2'],
        'voyager.txt': [],
    }

    def test_approved_scripts_exist(self):
        self.assertEqual(len(APPROVED), 5)

    def test_approved_warn_lists_are_stable(self):
        got = {os.path.basename(p): sorted(r['rule'] for r in check(load(p))['results'] if r['status'] == 'WARN')
               for p in APPROVED}
        self.assertEqual(got, self.WARN_BASELINE)

    def test_approved_scripts_have_no_fail(self):
        for path in APPROVED:
            with self.subTest(script=os.path.basename(path)):
                res = check(load(path))
                fails = [r['rule'] for r in res['results'] if r['status'] == 'FAIL']
                self.assertEqual(fails, [])


if __name__ == '__main__':
    unittest.main()
