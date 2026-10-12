---
name: resume
description: Tailor, build, or check Henry's LaTeX resumes. Use whenever he asks to adapt his resume to a job ad, add or drop an entry, choose which projects to feature, fix layout or page overflow, check ATS parseability, or build the PDFs. Covers the general_resume/ vs applications/ layout, the project bank (content/bank/projects/, the complete record every project entry is picked from), and the rule that content changes start in the general resume or the bank, never in a per-application copy.
---

# Resume

Layout, macros and vertical rhythm are documented in `CLAUDE.md`; read it before
touching `resumestyle.sty`. This skill covers **where things live and which copy you
are allowed to edit**.

## Layout

```
general_resume/SWE/Henry_Hsu_SWE_resume.tex    -> general_resume/SWE/Henry_Hsu_Resume.pdf
general_resume/GAIE/Henry_Hsu_GAIE_resume.tex  -> general_resume/GAIE/Henry_Hsu_Resume.pdf
applications/<company>/                        one directory per APPLICATION
  Henry_Hsu_SWE_resume_openai.tex              -> applications/openai/Henry_Hsu_Resume.pdf
  cover_letter_openai.tex                      -> cover_letter_openai.pdf
content/resume/                                the general module pool
content/customized/<company>/                  per-application overrides
content/bank/projects/<id>.tex                 every project, complete and verified; never \input
content/bank/private/<id>.md                   gitignored notes unsafe for a public repo
```

Every resume PDF is `Henry_Hsu_Resume.pdf`, because that filename is what a recruiter
and their ATS see. The `.tex` keeps a descriptive name so the files stay tellable
apart; `latexmk -jobname` decouples the two. Cover letters keep the company in the
filename on purpose: a resume names no company, so a mis-attach is cheap, while a
letter names it in the first line.

One directory per **application**, not per company: two roles at one employer are two
applications (`bytedance-agenteval`, `bytedance-agentsec`).

## The rule: change the general resume first

**A content change starts in `content/resume/`, never in a `content/customized/<company>/`
copy.** A customized module exists to reframe one entry for one posting. It is not the
place to fix a typo, update a metric, add a newly-shipped project, or add a skill,
because that fix then exists in exactly one application and every other resume keeps
the old version. There are already twenty-two customized skills files against two
general ones, which is how far this drifts if it is not enforced.

So:

1. Make the change at its source.
   - **A project:** its bank file comes first, because the bank is the source of truth
     for project facts. Then sync the summary in career-ops' `cv.md`. Then fix every
     module carrying its marker (`grep -rl '^% bank: <id>' content/`).
   - **Anything else:** `content/resume/`, or `content/shared/` for header and contact
     detail. Here `cv.md` stays the source of truth: if a number changes, sync it there.
2. Run `make`. Every resume rebuilds, so you immediately see who no longer fits on one
   page.
3. Only then, if a specific posting needs different *emphasis*, add or update a module
   under `content/customized/<company>/` and record in its header comment what it
   changed versus the canonical module and why.

A customized module that differs from its general counterpart by anything other than
deliberate reframing is a bug. When you touch one, check whether the general module
needs the same change.

## Projects come from the bank

`content/bank/projects/` holds one file per project: the complete, verified record of
everything Henry could claim about it. `make bank` prints every card: dates, team,
status, signals, summary, and how many modules use it.

- **It is complete.** A project without a bank file does not exist for resume purposes.
  A new project starts as a bank file plus a `cv.md` summary, never as a module.
- **It is the source of truth for project facts.**
  - Every project number on a page traces to a facet's `Evidence:` line.
  - `Henry-attested` evidence is his word with no artifact behind it: usable, but never
    strengthen it.
- **Every project module carries `% bank: <id>` on line 1**, canonical or customized.
- **Obey the card.**
  - `status: retired` or `interview-only` keeps a project off the page.
  - The CONSTRAINTS block binds every wording.
  - Nothing under UNVERIFIED or INTERVIEW NOTES ever reaches a page.
- **Write new wording from the bank**, never by forking another application's module.
  Reusing an existing module unchanged is fine.
- **Read `content/bank/private/<id>.md` when it exists.** It holds teammates, authorship,
  caveats and retracted claims. Never copy any of it into a tracked file.
- **The bank names no company, application or teammate.** The repo is public.

## Tailoring a resume to a job ad

1. List the posting's signals: the skills, systems and verbs it asks for.
2. Run `make bank` and shortlist the projects whose `signals` match, from `claimable`
   cards only.
3. For each shortlisted project, read the whole bank file and its private note.
4. Find the modules that already use it: `grep -rl '^% bank: <id>' content/`. If one
   fits, reuse it unchanged. Otherwise write `content/customized/<application>/<id>.tex`
   from the bank's facets:
   - line 1 is `% bank: <id>`;
   - a header comment names the facets used and what was reframed for this posting;
   - shorten a facet, but never add a claim it does not make.
5. Point the driver's `\input` at it. Run `make`, then `make check`, which covers one
   page, orphans, ATS, and check-bank's marker, date and link checks.
6. If tailoring surfaced a new fact or a better general wording, it goes into the bank
   first, then `cv.md`, then the modules.

## Building

Everything builds **from the repo root**. TeX resolves `\input` against the current
directory rather than the file's own directory, so `cd applications/openai && latexmk`
breaks. latexmk does not `cd` by default, so `make` is correct.

| Command | What it does |
|---|---|
| `make` | build every resume, letters and the generic template; fail if any resume is not exactly 1 page |
| `make check` | the same page gate plus the orphan, ATS and bank warnings |
| `make bank` | the project catalog: one card per file in `content/bank/projects/` |
| `make orphans` | orphan lines and over-long bullets, resumes and letters |
| `make ats` | ATS parseability score plus Greenhouse's published checklist |
| `make letters` | the per-application cover letters only |

Intermediates go to `build/`, never the working tree. Variants are in the default
build on purpose: one that nothing rebuilds goes stale silently.

## Content rules

- **One bullet, one point.** One line is the target, two is acceptable, three is not.
- **No orphan lines.** Prefer cutting a word or two; add information only when the
  line genuinely cannot be cut further, and then add real substance, never filler.
  Never fix it with a spacing knob.
- **Both resumes fit one page with almost no slack.** Adding a bullet means trading
  one away.
- **Never invent a claim.** Every project number traces to a bank facet's `Evidence:`
  line, and every other number traces to `cv.md`. Reframe and reorder freely; do not
  manufacture.
