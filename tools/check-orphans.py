#!/usr/bin/env python3
"""Warn about orphan lines and over-long bullets in a built resume or cover letter PDF.

Two rules, both about the shape of a bullet rather than its content:

  Orphan line  A wrapped bullet or paragraph whose LAST line carries almost
               nothing: one or two stray words trailing under a full line of
               text. It reads as a typo at a glance and it burns a whole line
               on a page that has no slack.

  Line budget  One bullet carries one point. One line is the target, two lines
               is acceptable, three or more is not: a three-line bullet is two
               points wearing one bullet, so split it or cut it. This one
               applies to bullets only, since a summary paragraph or a wrapped
               Skills line is legitimately longer.

Why measure the PDF and not the .tex source: where a line breaks depends on
font metrics and the text width, so a tidy 100-column source line says nothing
about where it actually lands on the page. This reads the real geometry out of
`pdftotext -bbox-layout`, which reports every word's bounding box in points.

This is a WARNING, never a gate. The detection is a heuristic and a bullet is
sometimes legitimately short, so the judgement stays with the human: the script
prints the offending line with its context and exits 0. Pass --strict to make it
exit 1 instead, for a hook or CI that wants enforcement.

Two fixes exist for an orphan and they are not equal. DEFAULT TO CUTTING a word
or two: the page has no slack, so the reclaimed line is nearly always worth more
somewhere else. ADD INFORMATION only when the line genuinely cannot be cut
further, and then add real substance (a metric, a scope, a system name), never
filler that pads the measure without adding a fact. Never reach for a spacing
knob in resumestyle.sty, which reflows every other entry on the page.

Usage:
    tools/check-orphans.py [options] file.pdf [file.pdf ...]

Options:
    --min-fill F   flag a last line occupying less than F of the text width
                   (default 0.25)
    --min-words N  flag a last line of N words or fewer (default 2)
    --max-lines N  flag a BULLET wrapping to more than N lines (default 2;
                   0 disables the line-budget check). Paragraphs and Skills
                   lines are exempt from the budget; the orphan check still
                   covers them.
    --strict       exit 1 when anything is flagged (default: always exit 0)
    --quiet        print only the flagged lines, not the per-file ok lines
"""

import argparse
import html
import re
import shutil
import subprocess
import sys

# Leading glyphs that start a new list item rather than continuing one.
BULLET_CHARS = {"•", "◦", "▪", "–", "⁃", "-", "*"}

# Below this width a "line" is a right-aligned date or location column, not
# prose that could orphan.
MIN_MEASURE_PT = 120.0

LINE_RE = re.compile(r"<line ([^>]*)>(.*?)</line>", re.S)
BLOCK_RE = re.compile(r"<block [^>]*>.*?</block>", re.S)
WORD_RE = re.compile(r"<word[^>]*>(.*?)</word>", re.S)


def attr(attrs, name):
    m = re.search(name + r'="([-\d.]+)"', attrs)
    return float(m.group(1)) if m else 0.0


def parse_lines(block_xml):
    """Return [(xMin, xMax, [words])] for one block, in document order."""
    out = []
    for attrs, body in LINE_RE.findall(block_xml):
        words = [html.unescape(w) for w in WORD_RE.findall(body)]
        if words:
            out.append((attr(attrs, "xMin"), attr(attrs, "xMax"), words))
    return out


def segments(lines):
    """Split a block's lines into list items / paragraphs.

    pdftotext groups a whole bullet list into one block, so the block's last
    line is only the last bullet's last line. Splitting on the bullet glyph
    recovers each item, and a block with no bullets stays one segment.
    """
    out, cur = [], []
    for line in lines:
        if cur and line[2][0] in BULLET_CHARS:
            out.append(cur)
            cur = []
        cur.append(line)
    if cur:
        out.append(cur)
    return out


def check_pdf(path, min_fill, min_words, max_lines):
    try:
        xml = subprocess.run(
            ["pdftotext", "-bbox-layout", path, "-"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        return None, f"could not read {path}: {e.stderr.strip() or e}"

    findings = []
    for block in BLOCK_RE.findall(xml):
        lines = parse_lines(block)
        if len(lines) < 2:
            continue
        right_edge = max(x1 for _, x1, _ in lines)
        for seg in segments(lines):
            if len(seg) < 2:
                continue  # never wrapped, so nothing can be orphaned
            # The budget is a rule about BULLETS. A summary paragraph or a
            # wrapped Skills line is legitimately three lines, and the
            # right-aligned date column is not prose at all.
            if max_lines and len(seg) > max_lines and seg[0][2][0] in BULLET_CHARS:
                findings.append({
                    "reason": f"{len(seg)} lines, budget is {max_lines}",
                    "orphan": " ".join(seg[0][2])[:100],
                    "prev": "(bullet runs long: split it or cut it)",
                })
            x0, x1, words = seg[-1]
            measure = right_edge - x0
            if measure < MIN_MEASURE_PT:
                continue
            fill = (x1 - x0) / measure
            reasons = []
            if len(words) <= min_words:
                reasons.append(f"{len(words)} word{'s' if len(words) != 1 else ''}")
            if fill < min_fill:
                reasons.append(f"fills {fill:.0%} of the line")
            if reasons:
                findings.append({
                    "reason": " and ".join(reasons),
                    "orphan": " ".join(words),
                    "prev": " ".join(seg[-2][2]),
                })
    return findings, None


def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--min-fill", type=float, default=0.25)
    ap.add_argument("--min-words", type=int, default=2)
    ap.add_argument("--max-lines", type=int, default=2)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not shutil.which("pdftotext"):
        print("warn  check-orphans: pdftotext not found, skipping "
              "(brew install poppler)", file=sys.stderr)
        return 0

    total = 0
    for path in args.pdfs:
        findings, err = check_pdf(path, args.min_fill, args.min_words,
                                  args.max_lines)
        if err:
            print(f"warn  {err}", file=sys.stderr)
            continue
        if not findings:
            if not args.quiet:
                print(f"ok   {path} (no orphan lines, no over-long bullets)")
            continue
        total += len(findings)
        n = len(findings)
        print(f"WARN {path}: {n} issue{'s' if n != 1 else ''}")
        for f in findings:
            prev = f["prev"]
            if len(prev) > 76:
                prev = "..." + prev[-73:]
            print(f"       ...{prev}")
            print(f"       > {f['orphan']}   <-- {f['reason']}")
        print("       prefer cutting a word or two; add information only when "
              "the line cannot be cut further")

    if total and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
