# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LaTeX resume repository with multiple resume variants (SWE vs GenAI/AI Engineer) and a cover letter system. It is split three ways: layout in `resumestyle.sty`, content in `content/` (one file per entry), and each resume `.tex` is a thin driver that only picks which entries appear and in what order. A layout change is made once in the package; an entry is written once in `content/` and `\input` by whichever resumes want it.

## Build Commands

Build both resumes and verify each still fits on one page:
```
make
```
`make` rebuilds any resume whose `.tex` or `resumestyle.sty` is newer than its PDF, then fails if a PDF is not exactly 1 page. Always use this after editing `resumestyle.sty` — an editor's on-save build only rebuilds the file you have open, leaving the other variant stale.

Compile a single file (cover letters, one-off checks):
```
latexmk -xelatex <filename>.tex
```

Remove build artifacts (`make clean` keeps the PDFs):
```
make clean
```

## Formatting

LaTeX source is formatted with `latexindent` configured via `.latexindent.yaml` (2-space indent, 100-column text wrap, no backups).

## Architecture

- **Shared style**: `resumestyle.sty` carries the whole layout. Loading it is the entire preamble of a resume file.
- **Content modules**: `content/resume/` holds one file per entry — `awards.tex`, `summary/`, `experience/`, `education/`, `projects/`, `extracurricular/`, `skills/`. `content/shared/header.tex` is the single source of contact details and is shared with the cover letters, so it must not reference anything defined in `resumestyle.sty` (the caller owns the spacing after it). There is no `\mylocation` indirection any more: the address lives in that one file. Each file contains exactly one `\resumeEntry` / `\resumeProjectEntry` block (or one section's lines) and **must end with `%`** so `\input` does not inject a blank line, which would add a stray `\par` of vertical space.
- **Resume variants**: `Henry_Hsu_SWE_resume.tex` (Software Engineer) and `Henry_Hsu_GAIE_resume.tex` (GenAI/AI Engineer) are drivers: `\documentclass`, `\usepackage{resumestyle}`, `\mylocation`, then `\section` scaffolding around `\input` lines. Retarget a resume by swapping `\input` lines — never paste an entry body into a driver.
- **Module pool**: `content/` also holds entries no current resume uses (six inactive projects, three extracurricular entries). They are ready to `\input`, not commented out. Add to the pool rather than deleting an entry you are dropping from a resume.
- **Duplicate content is intentional**: style is DRY, content is not. When a project or role needs different framing per target (e.g. `projects/chat-bar-server.tex` vs `projects/chat-bar-mud.tex`, `experience/google-swe.tex` vs `experience/google-gaie.tex`), write a second module. Do not try to parameterise one file into serving both — the point of tailoring is that the sentences differ.
- **Cover letters**: `cover_letters/cover_letter.tex` is the tracked generic template. It `\input`s `../content/shared/header` and is built from inside `cover_letters/`, so those relative paths resolve — build it with `make cover`, not from the repo root. Company-specific letters go in `cover_letters/specific_comps/` (gitignored, so they exist only on the local disk). `sign.png` is intentionally untracked and guarded with `\IfFileExists`; never make the template hard-depend on it.
- **Fonts**: get Source Sans Pro from `\usepackage[default]{sourcesanspro}`, never `\setmainfont{Source Sans Pro}` — that needs the font installed system-wide and breaks the XeLaTeX build.
- **Custom commands** (defined in `resumestyle.sty`, each with a doc comment above its definition):
  - `\resumeEntry{title}{date}{org}{location}` — entry header, two rows
  - `\resumeEducation[note]{school}{date}{degree}{location}` — education entry; all rows sit in one `\item` so the group holds together, and the optional note becomes a third row (minor, thesis, honours)
  - `\resumeProjectEntry{title}{date}` — project header
  - `\resumeItem{text}` — one bullet
  - `\resumeEntryListStart`/`End` — outer list of entries; `\resumeItemListStart`/`End` — inner bullet list
- **Vertical rhythm**: all spacing lives in the `VERTICAL RHYTHM` block near the top of `resumestyle.sty` — `\resumeBulletSep`, `\resumeEntrySep`, `\resumeHeadSep`, `\resumeHeaderGap`, `\resumeSectionBefore`, `\resumeSectionRuleGap`, `\resumeSectionAfter`. The document body contains **no bare `\vspace`**; entries are vertically self-contained so they can be reordered or swapped freely. Never reintroduce a hand-tuned `\vspace` in content — adjust a knob instead. Both resumes fit on exactly one page with **almost no slack** — `\resumeSectionAfter` is at 4pt and 5pt already overflows the SWE resume — so run `make` after any edit and expect to trade space elsewhere when adding content.

  Spacing that groups rows *within* an entry belongs inside the entry's macro, in one `\item`, not in a negative `\vspace` between items. A `\vspace` written after a `tabular*` is still in horizontal mode and collapses rows instead of separating them; this has broken the layout twice.
- **Key packages**: `sourcesanspro` (font), `fontawesome5` (icons), `titlesec`, `enumitem`, `tabularx`, `hyperref`, `xcolor`.

## Cover Letter Workflow

When writing a cover letter for a specific company:

1. **Read** both resume variants to understand the user's full experience
2. **Analyze the job ad** — extract Must-Have vs Nice-to-Have skills, competencies, keywords
3. **Ask STAR questions** one cluster at a time (Situation → Task → Action → Result), pausing for answers. Tag each question with the source requirement from the JD (e.g., `[A3: "Python; data pipelines"]`)
4. **Probe** for: context, impact/metrics, scope, reach, tools/tech, constraints/challenges, leadership/communication
5. **Calibrate verbs** — clarify actual role and autonomy (designed vs contributed; avoid "pioneered" unless warranted)
6. **Draft body paragraphs** — smooth narrative flow (not bullets strung together), concise, evidence-driven. One STAR story per paragraph. Never assume or invent details.
7. **Save** as `cover_letters/specific_comps/cover_letter_<company>.tex` using `cover_letters/cover_letter.tex` as template

Full methodology is stored in the persistent memory file `cover_letter_methodology.md`.

## Important Notes

- Layout changes go in `resumestyle.sty` only — never copy layout back into a resume `.tex`. Recompile **both** resumes afterwards, since one package edit reflows every variant.
- Always compile with XeLaTeX. A pdfLaTeX build silently produces a different (wrong) PDF — check `pdffonts` shows `CID Type 0C` fonts if a PDF looks unexpectedly different.
- The project uses XeLaTeX (not pdfLaTeX) for font support via `fontspec`.
- PDFs are tracked in git. Recompile and include updated PDFs when modifying `.tex` content.
