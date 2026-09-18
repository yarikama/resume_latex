#!/usr/bin/env python3
"""Score a built resume PDF for ATS parseability (0-100 + letter grade).

This is the PDF-native sibling of career-ops' `verify-ats.mjs`, which scores the
same eight things but only reads the HTML that career-ops' own `pdf` mode
emits. This repo builds PDFs straight out of XeLaTeX, so that checker never
sees the real artefact. Same weights, same grade bands, same 0/1 exit contract,
measured against the PDF an ATS would actually receive.

Where the two differ, the PDF is the better evidence: font embedding and text
extraction are facts about the file rather than predictions from markup. The
one check that does not carry over is "UTF-8 declared", a markup concern with
no PDF equivalent; its 5 points go to the thing that actually breaks extraction
here, ToUnicode coverage. That is not hypothetical: without
`\\XeTeXgenerateactualtext` the sourcesanspro CMap maps every hyphen to U+2011
and `pdftotext` returns zero ASCII hyphens, so `real-time`, `scikit-learn` and
the phone number all come out unmatchable while looking perfect on the page.

Like the page-count check this is deterministic and offline; unlike it, and
like `check-orphans.py`, it is ADVISORY. A score is a heuristic read of how a
parser will behave, so it reports and exits 0. Pass --strict for the 0/1
contract (exit 1 below --min-score or on any critical issue).

Scores RESUMES. The rubric expects Experience / Education / Skills headings, so
pointing it at a cover letter scores a document it was never meant to judge.

Alongside the score it reports Greenhouse's OWN published parse-failure causes
as a separate pass/fail list. That list is the only part of this tool with an
external source, so it is never folded into the score: a vendor's documented
failure mode is worth more than a weighting nobody has validated, and averaging
the two would hide that difference.
  https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse

Requires poppler: pdftotext, pdffonts, pdfimages (brew install poppler).

Usage:
    tools/check-ats.py [options] file.pdf [file.pdf ...]

Options:
    --keywords "a,b,c"  advisory keyword coverage; never changes the score
    --min-score N       pass threshold for --strict (default 70)
    --strict            exit 1 when a file fails; default always exits 0
    --json              machine-readable result on stdout
    --checklist         show every Greenhouse row, not only the failures
    --quiet             print only the failures
"""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import zlib

REQUIRED_HEADINGS = ["experience", "education", "skills"]
BONUS_HEADINGS = ["summary", "projects", "certifications", "awards"]

# A right-aligned date or location shares a baseline with its title in every
# normal resume, so "two things on one line" cannot be the test. A real second
# column is instead a STACK of wide lines starting well right of the main left
# margin. A date column fails both halves: its lines are narrow and there are
# never many of them at one x.
COLUMN_MIN_INDENT = 0.35   # of the text measure, right of the main left margin
COLUMN_MIN_WIDTH = 0.35    # of the text measure
COLUMN_MIN_LINES = 3       # a stack, not a stray right-aligned row

# Greenhouse publishes the things that make ITS OWN parser fail. Unlike the
# score above, every entry here traces to that page, so it is reported as a
# separate pass/fail list with a citation rather than folded into a number.
# https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse
GH_DOC = ("https://support.greenhouse.io/hc/en-us/articles/"
          "200989175-Unsuccessful-resume-parse")
GH_MAX_BYTES = 2_500_000
GH_PLACEHOLDERS = ["first last", "john doe", "jane doe", "your name",
                   "lorem ipsum", "company 1", "company name", "[company]",
                   "job title here", "todo", "xxxx"]
# Abbreviated titles are called out by name; these are the forms that show up
# in a title line rather than in a company name like "Co., Ltd.".
# Single-character tokens that stand alone legitimately in an English resume.
# Anything else appearing alone is a glyph from a font with no ToUnicode CMap
# leaking into the text layer. Known blind spot: an icon that happens to
# extract as "a" or a digit hides inside this allowlist, so the check can miss
# one. It is here to stop the warning firing on en dashes and bullets, not to
# be exhaustive.
SAFE_SINGLE_TOKENS = set("aAI0123456789&|-/+\u2013\u2014\u2022\u00d7")

GH_TITLE_ABBREV = re.compile(
    r"\b(Sr|Jr|Eng|Engr|Mgr|Dev|Devel|Admin|Asst|Dir|Coord|Spec|Tech)\.",
    re.I)

LINE_RE = re.compile(r"<line ([^>]*)>(.*?)</line>", re.S)
WORD_RE = re.compile(r"<word[^>]*>(.*?)</word>", re.S)
STREAM_RE = re.compile(rb"stream\r?\n(.*?)endstream", re.S)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout


def attr(attrs, name):
    m = re.search(name + r'="([-\d.]+)"', attrs)
    return float(m.group(1)) if m else 0.0


def bbox_lines(path):
    xml = run(["pdftotext", "-bbox-layout", path, "-"])
    out = []
    for attrs, body in LINE_RE.findall(xml):
        words = [html.unescape(w) for w in WORD_RE.findall(body)]
        if words:
            out.append({
                "x0": attr(attrs, "xMin"), "x1": attr(attrs, "xMax"),
                "y": attr(attrs, "yMin"), "words": words,
            })
    return out


def greenhouse_checklist(path, text, lines, images, raw):
    """Greenhouse's own published parse-failure causes, as pass / fail / unknown.

    Deliberately NOT scored and NOT merged into the rubric above. The rubric is
    one person's weighting with no external basis; every row here comes from the
    vendor's documentation, so it is worth more and should not be averaged into
    something worth less. Two rows report `unknown` on purpose: a PDF carries no
    table or page-header semantics unless it is tagged, so claiming to check
    them would be inventing a result.
    """
    rows = []

    def row(name, state, detail=""):
        rows.append({"check": name, "state": state, "detail": detail})

    size = len(raw)
    row("file under 2.5MB", "pass" if size <= GH_MAX_BYTES else "fail",
        f"{size / 1000:.0f}KB")

    lower = text.lower()
    hits = [p for p in GH_PLACEHOLDERS if p in lower]
    row("no placeholder / fake data", "fail" if hits else "pass",
        ", ".join(hits) if hits else "")

    spaced = re.findall(r"\b(?:[A-Za-z] ){3,}[A-Za-z]\b", text)
    row("no spaces between letters", "fail" if spaced else "pass",
        spaced[0] if spaced else "")

    row("no graphics, photos or word art", "fail" if images else "pass",
        f"{len(images)} image(s)" if images else "")

    row("not an image-only upload", "pass" if len(text.strip()) >= 300 else "fail",
        f"{len(text.strip())} chars of text")

    abbrev = sorted(set(GH_TITLE_ABBREV.findall(text)))
    row("no abbreviated job titles", "fail" if abbrev else "pass",
        ", ".join(a + "." for a in abbrev) if abbrev else "")

    # Reuses the scored layout check; same evidence, but reported here against
    # the vendor's wording rather than as 20 points.
    multi = column_stack(lines)
    row("no columned layout", "fail" if multi else "pass",
        f"{len(multi)} wide lines right of the margin" if multi else "")

    tagged = b"/StructTreeRoot" in raw
    row("no tables, headers or footers",
        "fail" if tagged and b"/Table" in raw else "unknown",
        "PDF is untagged, so it carries no table or page-header semantics for "
        "a parser to trip on; the risk cannot be measured from the file"
        if not tagged else "")

    return rows


def column_stack(lines):
    """Lines that form a real second column, or [] if the page is single-column."""
    if not lines:
        return []
    measure = max(max(l["x1"] for l in lines) - min(l["x0"] for l in lines), 1)
    left = min(l["x0"] for l in lines)
    stack = [l for l in lines
             if (l["x0"] - left) / measure > COLUMN_MIN_INDENT
             and (l["x1"] - l["x0"]) / measure > COLUMN_MIN_WIDTH]
    return stack if len(stack) >= COLUMN_MIN_LINES else []


def check(path, keywords):
    text = run(["pdftotext", path, "-"])
    lower = text.lower()
    issues, score = [], 0.0

    # 15 - a real, selectable text layer.
    if len(text.strip()) >= 300:
        score += 15
    else:
        issues.append(("critical", f"only {len(text.strip())} characters of "
                       "selectable text; the CV may be rasterized and an ATS "
                       "will read nothing"))

    # 20 - standard section headings an ATS can segment on.
    missing = [h for h in REQUIRED_HEADINGS if h not in lower]
    found_bonus = [h for h in BONUS_HEADINGS if h in lower]
    score += (len(REQUIRED_HEADINGS) - len(missing)) / len(REQUIRED_HEADINGS) * 14
    score += min(len(found_bonus), 3) * 2
    if missing:
        issues.append(("critical", "missing standard heading(s): "
                       + ", ".join(h.title() for h in missing)))

    # 15 - a contact email that survives extraction.
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    if emails:
        score += 15
    else:
        issues.append(("critical", "no email address found in the extracted "
                       "text; an ATS cannot route the application"))

    # 20 - single-column body. Two prose lines sharing a baseline mean the
    # extractor will interleave them and scramble the reading order.
    lines = bbox_lines(path)
    multi = column_stack(lines)
    if not multi:
        score += 20
    else:
        sample = " ".join(multi[0]["words"])[:60]
        issues.append(("critical", f"{len(multi)} wide lines start well right "
                       "of the left margin, which looks like a second column "
                       f"and scrambles reading order: {sample}"))

    # 10 - no CV text baked into an image.
    imgs = [l for l in run(["pdfimages", "-list", path]).splitlines()[2:] if l.strip()]
    if not imgs:
        score += 10
    else:
        score += 5
        issues.append(("warning", f"{len(imgs)} embedded image(s); an ATS reads "
                       "no text inside them, so check none carries content"))

    # 10 - every font embedded, so glyphs extract rather than substitute.
    # pdffonts columns: name type encoding emb sub uni object-ID. The name can
    # hold spaces and the object ID is two tokens, so anchor on the emb/sub/uni
    # triple, the only run of yes/no values in a row.
    font_rows = []
    for line in run(["pdffonts", path]).splitlines()[2:]:
        row = line.split()
        flags = [t for t in row if t in ("yes", "no")]
        if row and len(flags) >= 3:
            font_rows.append({"name": row[0], "emb": flags[-3], "uni": flags[-1]})
    not_embedded = [r["name"] for r in font_rows if r["emb"] == "no"]
    if not not_embedded:
        score += 10
    else:
        issues.append(("warning", "font(s) not embedded, glyphs may extract "
                       "garbled: " + ", ".join(not_embedded)))

    # 5 - encoding integrity. The PDF answer to "is the text recoverable as
    # the characters a human sees", replacing the HTML checker's UTF-8 meta tag.
    nbhyphen = text.count("‑")
    ligatures = len(re.findall(r"[ﬀ-ﬆ]", text))
    no_unicode = [r["name"] for r in font_rows if r["uni"] == "no"]
    # A missing ToUnicode CMap only matters if its glyphs actually reach the
    # text layer. Wrapping an icon in a span with empty ActualText fixes the
    # extraction without changing the font, so warning on the font property
    # alone would cry wolf forever after the fix.
    junk = sorted({w for w in text.split()
                   if len(w) == 1 and w not in SAFE_SINGLE_TOKENS})
    if nbhyphen or ligatures:
        issues.append(("critical", f"{nbhyphen} non-breaking hyphen(s) and "
                       f"{ligatures} ligature glyph(s) in the text layer; "
                       "compounds like real-time extract unmatchable "
                       "(is \\XeTeXgenerateactualtext still set?)"))
    elif no_unicode and junk:
        score += 2
        issues.append(("warning", "font(s) with no ToUnicode CMap are leaking "
                       f"junk into the text layer ({' '.join(junk)}): "
                       + ", ".join(n.split("+")[-1] for n in no_unicode)
                       + " (wrap the glyph in a span with empty ActualText)"))
    else:
        score += 5

    # 5 - no hidden text or keyword stuffing.
    raw = open(path, "rb").read()
    body = b""
    for s in STREAM_RE.findall(raw):
        try:
            body += zlib.decompress(s)
        except Exception:
            pass
    if re.search(rb"\b1 1 1 rg\b|\b1 g\b", body):
        issues.append(("warning", "white fill colour used in a content stream; "
                       "check for hidden white-on-white keywords"))
    else:
        score += 5

    score = round(min(score, 100))
    grade = ("A" if score >= 90 else "B" if score >= 80 else
             "C" if score >= 70 else "D" if score >= 60 else "F")

    result = {"file": path, "score": score, "grade": grade,
              "issues": [{"severity": s, "message": m} for s, m in issues],
              "greenhouse": greenhouse_checklist(path, text, lines, imgs, raw),
              "greenhouse_source": GH_DOC}

    if keywords:
        found = [k for k in keywords if k.lower() in lower]
        result["keywords"] = {
            "total": len(keywords), "found": len(found),
            "percent": round(len(found) / len(keywords) * 100),
            "missing": [k for k in keywords if k not in found],
        }
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdfs", nargs="+")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--min-score", type=int, default=70)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--checklist", action="store_true",
                    help="show every Greenhouse row, not just failures "
                         "and unknowns")
    args = ap.parse_args()

    for tool in ("pdftotext", "pdffonts", "pdfimages"):
        if not shutil.which(tool):
            print(f"warn  check-ats: {tool} not found, skipping "
                  "(brew install poppler)", file=sys.stderr)
            return 0

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    results, failed = [], 0

    for path in args.pdfs:
        r = check(path, keywords)
        results.append(r)
        critical = any(i["severity"] == "critical" for i in r["issues"])
        ok = r["score"] >= args.min_score and not critical
        if not ok:
            failed += 1
        if args.json:
            continue
        gh = r["greenhouse"]
        gh_fail = [g for g in gh if g["state"] == "fail"]
        gh_unknown = [g for g in gh if g["state"] == "unknown"]
        gh_line = (f"greenhouse {len(gh) - len(gh_fail) - len(gh_unknown)}"
                   f"/{len(gh)}"
                   + (f" ({len(gh_fail)} fail)" if gh_fail else "")
                   + (f" ({len(gh_unknown)} unmeasurable)" if gh_unknown else ""))
        if ok and not r["issues"] and not gh_fail and not args.checklist:
            if not args.quiet:
                print(f"ok   {path}  ATS {r['score']}/100 ({r['grade']})  {gh_line}")
            continue
        tag = "ok  " if ok else "WARN"
        print(f"{tag} {path}  ATS {r['score']}/100 ({r['grade']})  {gh_line}")
        for i in r["issues"]:
            print(f"       [{i['severity']}] {i['message']}")
        for g in r.get("greenhouse", []):
            # Default output carries only what needs action. A pass is silent
            # and an unknown is a documented limit, not a task.
            if not args.checklist and g["state"] != "fail":
                continue
            mark = {"pass": "ok ", "fail": "FAIL", "unknown": "?  "}[g["state"]]
            detail = f"  ({g['detail']})" if g["detail"] else ""
            print(f"       {mark} greenhouse: {g['check']}{detail}")
        if r.get("keywords"):
            k = r["keywords"]
            print(f"       keywords {k['found']}/{k['total']} ({k['percent']}%)")
            if k["missing"]:
                print(f"       missing: {', '.join(k['missing'])}")

    if args.json:
        print(json.dumps(results, indent=2))
    return 1 if (failed and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
