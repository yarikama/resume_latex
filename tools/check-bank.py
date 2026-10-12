#!/usr/bin/env python3
"""Check the project bank and every resume module that draws on it.

content/bank/projects/<id>.tex is the complete record of one project: every
facet that could go on a page, each with the evidence behind it, plus the
constraints any wording has to respect. It is the source of truth for project
facts. A resume never \\inputs it. A module under content/resume/ or
content/customized/ picks facets from it and says so on its first line:

    % bank: agentic-hybrid-rag

The bank is only worth having if nothing escapes it, so this checks both
directions:

  Bank files   The card at the top of each file (id, title, dates, link, team,
               status, tech, signals, summary, verified) is complete and well
               formed, every FACET names its evidence, and nothing below the
               UNVERIFIED line is a live \\resumeItem.

  Modules      Every file with a live \\resumeProjectEntry carries a marker that
               resolves to a bank file, and its dates and link agree with the
               card. A module that disagrees with its card is how one wrong
               date range reached fifteen resumes.

  Public repo  A bank file never names a company or an application, never holds
               a path into applications/ or content/customized/, and never
               holds a secret. The company list is read at runtime from the
               directory names, so it is never written down in this repo.

  Retracted    Phrases listed in content/bank/private/retracted.txt (gitignored)
               must not reappear anywhere under content/, comments included: a
               commented-out bullet is one edit away from a page.

--list prints every card instead. It is the catalog to read before choosing
which projects go on a resume.

This is a WARNING, never a gate, like check-orphans.py: it prints what it found
and exits 0. Pass --strict to make it exit 1 instead, for a hook or CI.

Usage:
    tools/check-bank.py [--list] [--quiet] [--strict]

Options:
    --list     print every project card (the catalog) and exit 0
    --quiet    print only problems, not the per-file ok lines
    --strict   exit 1 when anything is flagged (default: always exit 0)
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANK = ROOT / "content" / "bank" / "projects"
PRIVATE = ROOT / "content" / "bank" / "private"
RETRACTED = PRIVATE / "retracted.txt"
GENERIC_WORDS = PRIVATE / "not-companies.txt"
MODULE_ROOTS = (ROOT / "content" / "resume", ROOT / "content" / "customized")
DRIVER_GLOBS = ("general_resume/*/*.tex", "applications/*/*.tex")

CARD_KEYS = ("id", "title", "dates", "link", "team", "status", "tech",
             "signals", "summary", "verified")
STATUSES = {"claimable", "interview-only", "retired"}
STALE_DAYS = 180

MONTH = r"(?:Jan\.|Feb\.|Mar\.|Apr\.|May|Jun\.|Jul\.|Aug\.|Sep\.|Oct\.|Nov\.|Dec\.)"
DATES_RE = re.compile(rf"^{MONTH} \d{{4}}(?: -- (?:{MONTH} \d{{4}}|Present))?$")
LINK_RE = re.compile(r"^(https://\S+) \((public|private)\)$")
TEAM_RE = re.compile(r"^(?:solo|\d+-person)\b")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^%\s*([a-z]+):\s*(.*)$")
CONT_RE = re.compile(r"^%\s{3,}(\S.*)$")
RULE_RE = re.compile(r"^%\s*-{3,}")
CONSTRAINTS_RE = re.compile(r"^%\s*CONSTRAINTS\b")
FACET_RE = re.compile(r"^%\s*FACET:\s*(.*)$")
EVIDENCE_RE = re.compile(r"^%\s*Evidence:\s*\S")
UNVERIFIED_RE = re.compile(r"^%\s*UNVERIFIED\b")
NOTES_RE = re.compile(r"^%\s*INTERVIEW NOTES\b")
MARKER_RE = re.compile(r"^% bank: ([a-z0-9-]+)\s*$")
ITEM_RE = re.compile(r"\\resumeItem\b")
ENTRY_RE = re.compile(r"\\resumeProjectEntry\b")
LIST_MACRO_RE = re.compile(
    r"\\(?:resumeItemListStart|resumeItemListEnd|resumeProjectEntry|resumeEntry"
    r"|begin\{itemize\})")
BANK_INPUT_RE = re.compile(r"\\input\{[^}]*bank/")

SECRET_RES = (
    ("a Google API key", re.compile(r"AIza[0-9A-Za-z_\-]{20,}")),
    ("an OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}")),
    ("a GitHub token", re.compile(r"\bghp_[A-Za-z0-9]{20,}")),
    ("a private key", re.compile(r"PRIVATE KEY")),
)
FORBIDDEN_PATHS = ("customized/", "applications/", "/Users/")

# Directory names that are technology names too, so a bank file may use them.
# Everything else under applications/ and content/customized/ is treated as a
# company name. A word too generic to mean a company on its own, such as the
# first word of a hyphenated name, goes in content/bank/private/not-companies.txt
# (gitignored, one per line, # for comments) instead: listed here, it would
# publish a hint of where Henry applied.
NOT_COMPANIES = {"google", "microsoft", "openai", "langchain", "nvidia"}


def rel(path):
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_lines(path):
    return path.read_text(encoding="utf-8-sig").splitlines()


def split_comment(line):
    """Return (code, comment) for one line; comment is None if there is none.

    A % starts a comment only when an even number of backslashes precede it,
    so 35\\% stays text.
    """
    i = 0
    while True:
        i = line.find("%", i)
        if i < 0:
            return line, None
        j, n = i - 1, 0
        while j >= 0 and line[j] == "\\":
            n += 1
            j -= 1
        if n % 2 == 0:
            return line[:i], line[i + 1:]
        i += 1


def code_of(lines):
    return "\n".join(split_comment(line)[0] for line in lines)


def braced(s, i):
    """Read the {...} group at or after index i; return (body, end) or (None, i)."""
    while i < len(s) and s[i].isspace():
        i += 1
    if i >= len(s) or s[i] != "{":
        return None, i
    depth, j = 0, i
    while j < len(s):
        c = s[j]
        if c == "\\":
            j += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    return None, i


def norm_dates(s):
    return re.sub(r"\s+", " ", s.replace("\u2013", "--")).strip()


def card_links(value):
    """Return (urls, private_urls, problem) for a card's link value."""
    if re.match(r"^none -- \S", value):
        return [], [], None
    urls, private = [], []
    for part in (p.strip() for p in value.split(";")):
        m = LINK_RE.match(part)
        if not m:
            return urls, private, (f"link '{part}' is neither 'https://... (public)' "
                                   "nor 'none -- <why>'")
        urls.append(m.group(1))
        if m.group(2) == "private":
            private.append(m.group(1))
    return urls, private, None


def not_companies():
    words = set(NOT_COMPANIES)
    if GENERIC_WORDS.is_file():
        for line in GENERIC_WORDS.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip().lower()
            if line and not line.startswith("#"):
                words.add(line)
    return words


def company_names():
    names = set()
    for parent in (ROOT / "applications", ROOT / "content" / "customized"):
        if not parent.is_dir():
            continue
        for d in parent.iterdir():
            if d.is_dir():
                name = d.name.lower()
                names.add(name)
                first = name.split("-")[0]
                if len(first) >= 4:
                    names.add(first)
    allowed = not_companies()
    return sorted(n for n in names if n not in allowed)


def parse_bank(path, companies, today):
    """Return (card, issues) for one bank file."""
    lines = read_lines(path)
    card, issues = {}, []

    # The card: everything above the first "% ---" rule. Keys are read only up to
    # the CONSTRAINTS heading, so a constraint that happens to start with
    # "word:" is never mistaken for a card key.
    i, last_key, in_constraints = 0, None, False
    while i < len(lines) and not RULE_RE.match(lines[i].strip()):
        line = lines[i].strip()
        if CONSTRAINTS_RE.match(line):
            in_constraints = True
        if in_constraints:
            i += 1
            continue
        m = KEY_RE.match(line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if key not in CARD_KEYS:
                issues.append(f"line {i + 1}: unknown card key '{key}'")
            elif key in card:
                issues.append(f"line {i + 1}: card key '{key}' given twice")
            card[key] = val
            last_key = key
        else:
            c = CONT_RE.match(line)
            if c and last_key:
                card[last_key] += " " + c.group(1).strip()
            else:
                last_key = None
        i += 1
    if i == len(lines):
        issues.append("no '% ---' rule: the card never ends, so no facets follow it")

    for key in CARD_KEYS:
        if not card.get(key):
            issues.append(f"card is missing '{key}'")
    if not ID_RE.match(path.stem):
        issues.append(f"filename '{path.name}' is not kebab-case")
    if card.get("id") and card["id"] != path.stem:
        issues.append(f"id '{card['id']}' does not match the filename '{path.stem}'")
    if card.get("dates") and not DATES_RE.match(norm_dates(card["dates"])):
        issues.append(f"dates '{card['dates']}' is not 'Mon. YYYY[ -- Mon. YYYY|Present]'"
                      " (May takes no period)")
    if card.get("link"):
        _, private, problem = card_links(card["link"])
        if problem:
            issues.append(problem)
        for url in private:
            issues.append(f"links to a private repo, so a reader gets a 404: {url}")
    if card.get("team") and not TEAM_RE.match(card["team"]):
        issues.append(f"team '{card['team'][:40]}' does not start with 'solo' or 'N-person'")
    if card.get("status") and card["status"] not in STATUSES:
        issues.append(f"status '{card['status']}' is not one of {', '.join(sorted(STATUSES))}")
    if card.get("verified"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})\b", card["verified"])
        if not m:
            issues.append("verified does not start with an ISO date (YYYY-MM-DD)")
        else:
            age = (today - dt.date.fromisoformat(m.group(1))).days
            if age > STALE_DAYS:
                issues.append(f"verified {age} days ago: re-check the facts against the repo")

    # Facets, then the UNVERIFIED and INTERVIEW NOTES zones.
    zone, facet, facet_line, has_evidence, n_facets = "facets", None, 0, False, 0

    def close_facet():
        if facet is not None and not has_evidence:
            issues.append(f"line {facet_line}: FACET '{facet}' has no Evidence line")

    for k in range(i, len(lines)):
        raw = lines[k].strip()
        code, _ = split_comment(lines[k])
        m = FACET_RE.match(raw)
        if m:
            close_facet()
            facet, facet_line, has_evidence = m.group(1).strip(), k + 1, False
            n_facets += 1
            if zone != "facets":
                issues.append(f"line {k + 1}: FACET below the {zone.upper()} line")
            continue
        if UNVERIFIED_RE.match(raw) or NOTES_RE.match(raw):
            close_facet()
            facet = None
            zone = "unverified" if UNVERIFIED_RE.match(raw) else "interview notes"
            continue
        if EVIDENCE_RE.match(raw):
            has_evidence = True
            continue
        if not code.strip():
            continue
        if LIST_MACRO_RE.search(code):
            issues.append(f"line {k + 1}: list macro in a bank file; facets are bare "
                          "\\resumeItem lines, so an accidental \\input fails loudly")
        if ITEM_RE.search(code):
            if zone != "facets":
                issues.append(f"line {k + 1}: live \\resumeItem below the {zone.upper()} line")
            elif facet is None:
                issues.append(f"line {k + 1}: \\resumeItem outside any FACET")
    close_facet()
    if n_facets == 0:
        issues.append("no FACET: the bank file records nothing claimable")

    body = code_of(lines[i:])
    for m in ITEM_RE.finditer(body):
        content, _ = braced(body, m.end())
        if content is None:
            snippet = body[m.end():m.end() + 50].replace("\n", " ")
            issues.append(f"\\resumeItem with unbalanced braces near '{snippet}'")

    # Public-repo safety: the whole file, comments included.
    text = "\n".join(lines)
    for frag in FORBIDDEN_PATHS:
        if frag in text:
            issues.append(f"contains '{frag}': a bank file must not point into "
                          "per-application material")
    for label, rx in SECRET_RES:
        if rx.search(text):
            issues.append(f"contains what looks like {label}")
    for name in companies:
        if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", text, re.I):
            issues.append(f"names '{name}', which is an application directory here; "
                          "the bank is public and names no company")
    return card, issues


def check_modules(cards):
    """Return ({path: issues}, {bank id: module count})."""
    out, counts = {}, {}
    for root in MODULE_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.tex")):
            lines = read_lines(path)
            code = code_of(lines)
            entries = list(ENTRY_RE.finditer(code))
            marker = MARKER_RE.match(lines[0]) if lines else None
            issues = []
            if not entries:
                if marker:
                    issues.append("has a bank marker but no live \\resumeProjectEntry")
                    out[path] = issues
                continue
            if len(entries) > 1:
                issues.append(f"{len(entries)} project entries in one file; one entry per file")
            if not marker:
                issues.append("no '% bank: <id>' marker on line 1")
                out[path] = issues
                continue
            bid = marker.group(1)
            counts[bid] = counts.get(bid, 0) + 1
            card = cards.get(bid)
            if card is None:
                issues.append(f"marker names '{bid}', which has no bank file")
                out[path] = issues
                continue
            if card.get("status") == "retired":
                issues.append(f"draws on '{bid}', which the bank marks retired")
            title, end = braced(code, entries[0].end())
            date, _ = braced(code, end)
            if date is not None and card.get("dates") and \
                    norm_dates(date) != norm_dates(card["dates"]):
                issues.append(f"dates '{norm_dates(date)}' differ from the card's "
                              f"'{card['dates']}'")
            hrefs = re.findall(r"\\href\{([^}]*)\}", title or "")
            urls, private, _ = card_links(card.get("link", ""))
            if card.get("link", "").startswith("none"):
                if hrefs:
                    issues.append(f"links to {hrefs[0]}, but the card says no link")
                if "RoyalBlue" in (title or ""):
                    issues.append("title is RoyalBlue, which implies a link the card says "
                                  "does not exist")
            elif card.get("link"):
                if not hrefs:
                    issues.append("the card has a link but the module has none")
                for h in hrefs:
                    if h not in urls:
                        issues.append(f"links to {h}, the card lists {', '.join(urls)}")
                    elif h in private:
                        issues.append(f"links to a private repo, a 404 for readers: {h}")
            if issues:
                out[path] = issues
    return out, counts


def check_bank_inputs():
    """No driver or module may \\input a bank file."""
    paths = []
    for pattern in DRIVER_GLOBS:
        paths.extend(ROOT.glob(pattern))
    paths.extend((ROOT / "content").rglob("*.tex"))
    out = {}
    for path in sorted(set(paths)):
        if BANK_INPUT_RE.search(code_of(read_lines(path))):
            out[path] = ["\\inputs a bank file; the bank is a record, never a page"]
    return out


def plain(s):
    s = re.sub(r"(?m)^\s*%", " ", s)
    s = (s.replace("\\%", "%").replace("$\\times$", "x")
          .replace("\\textasciitilde", "~").replace("\\&", "&"))
    s = re.sub(r"\\[a-zA-Z]+\*?", " ", s)
    s = s.replace("{", "").replace("}", "").replace("$", "")
    return re.sub(r"\s+", " ", s).lower()


def check_retracted():
    """Return ({path: issues}, phrase count), or (None, 0) without the list."""
    if not RETRACTED.is_file():
        return None, 0
    phrases = []
    for line in RETRACTED.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            phrases.append(plain(line).strip())
    out = {}
    for path in sorted((ROOT / "content").rglob("*.tex")):
        if PRIVATE in path.parents:
            continue
        text = plain(path.read_text(encoding="utf-8-sig"))
        hits = [p for p in phrases if p and p in text]
        if hits:
            out[path] = [f"retracted phrase '{p}'" for p in hits]
    return out, len(phrases)


def print_catalog(cards, counts):
    for bid in sorted(cards):
        c = cards[bid]
        print(f"{bid}  {c.get('dates', '?')}  {c.get('status', '?')}")
        for key in ("title", "team", "link", "signals", "summary"):
            print(f"    {key + ':':<9}{c.get(key, '')}")
        print(f"    modules: {counts.get(bid, 0)}")
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not BANK.is_dir():
        print(f"warn  check-bank: {rel(BANK)} not found, skipping", file=sys.stderr)
        return 0

    today = dt.date.today()
    companies = company_names()
    cards, bank_issues = {}, {}
    for path in sorted(BANK.glob("*.tex")):
        card, issues = parse_bank(path, companies, today)
        cards[path.stem] = card
        bank_issues[path] = issues
    module_issues, counts = check_modules(cards)

    if args.list:
        print_catalog(cards, counts)
        return 0

    total = 0

    def report(path, issues):
        nonlocal total
        if not issues:
            if not args.quiet:
                print(f"ok   {rel(path)}")
            return
        total += len(issues)
        n = len(issues)
        print(f"WARN {rel(path)}: {n} issue{'s' if n != 1 else ''}")
        for msg in issues:
            print(f"       > {msg}")

    for path, issues in bank_issues.items():
        report(path, issues)

    for path, issues in sorted(module_issues.items()):
        report(path, issues)
    if not module_issues and not args.quiet:
        n = sum(counts.values())
        print(f"ok   {n} project module{'s' if n != 1 else ''}, every one linked to the bank")

    for path, issues in check_bank_inputs().items():
        report(path, issues)

    retracted, n_phrases = check_retracted()
    if retracted is None:
        if not args.quiet:
            print(f"note retracted-phrase scan skipped: {rel(RETRACTED)} is not present")
    else:
        for path, issues in sorted(retracted.items()):
            report(path, issues)
        if not retracted and not args.quiet:
            print(f"ok   none of {n_phrases} retracted phrases appears under content/")

    if total and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
