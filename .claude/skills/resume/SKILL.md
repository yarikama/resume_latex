---
name: resume
description: Tailor, build, or check Henry's LaTeX resumes. Use whenever he asks to adapt his resume to a job ad, add or drop an entry, fix layout or page overflow, check ATS parseability, or build the PDFs. Covers the general_resume/ vs applications/ layout and the rule that content changes start in the general resume, never in a per-application copy.
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
the old version. There are already seven customized `skills.tex` files against two
general ones, which is how far this drifts if it is not enforced.

So:

1. Make the change in `content/resume/` (or in `content/shared/` if it is header or
   contact detail). `cv.md` in career-ops stays the source of truth for the facts; if a
   number changes here, sync it there.
2. Run `make`. All eleven resumes rebuild, so you immediately see who no longer fits
   on one page.
3. Only then, if a specific posting needs different *emphasis*, add or update a module
   under `content/customized/<company>/` and record in its header comment what it
   changed versus the canonical module and why.

A customized module that differs from its general counterpart by anything other than
deliberate reframing is a bug. When you touch one, check whether the general module
needs the same change.

## Building

Everything builds **from the repo root**. TeX resolves `\input` against the current
directory rather than the file's own directory, so `cd applications/openai && latexmk`
breaks. latexmk does not `cd` by default, so `make` is correct.

| Command | What it does |
|---|---|
| `make` | build all eleven resumes, letters and the generic template; fail if any resume is not exactly 1 page |
| `make check` | the same page gate plus the orphan and ATS warnings |
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
- **Never invent a claim.** Every number traces to `cv.md`. Reframe and reorder
  freely; do not manufacture.
