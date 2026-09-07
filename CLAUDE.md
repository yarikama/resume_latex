# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LaTeX resume repository with multiple resume variants (SWE vs GenAI/AI Engineer) and a cover letter system. All layout — packages, margins, custom commands, spacing — lives in the shared `resumestyle.sty`; each resume `.tex` holds only `\documentclass`, `\usepackage{resumestyle}`, the contact details, and its content. A layout change is made once, in the package, and applies to every variant.

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
- **Resume variants**: `Henry_Hsu_SWE_resume.tex` (Software Engineer) and `Henry_Hsu_GAIE_resume.tex` (GenAI/AI Engineer). Both share the contact header, education, awards, and skills sections but differ in work experience bullets, project selections, and skills emphasis. Unused sections are commented out rather than removed.
- **Cover letters**: `cover_letters/cover_letter.tex` is the tracked generic template. Company-specific letters go in `cover_letters/specific_comps/` (gitignored).
- **Custom commands** (defined in `resumestyle.sty`, each with a doc comment above its definition):
  - `\resumeEntry{title}{date}{org}{location}` — entry header, two rows
  - `\resumeEntryNoOrg{title}{date}` — entry header, single row (no org/location)
  - `\resumeEntryDetail{text}{right}` — detail row, plain left / italic right
  - `\resumeProjectEntry{title}{date}` — project header
  - `\resumeItem{text}` — one bullet
  - `\resumeEntryListStart`/`End` — outer list of entries; `\resumeItemListStart`/`End` — inner bullet list
- **Vertical rhythm**: all spacing lives in the `VERTICAL RHYTHM` block near the top of `resumestyle.sty` — `\resumeBulletSep`, `\resumeEntrySep`, `\resumeHeadSep`, `\resumeHeaderGap`, `\resumeSectionBefore`, `\resumeSectionAfter`. The document body contains **no bare `\vspace`**; entries are vertically self-contained so they can be reordered or swapped freely. Never reintroduce a hand-tuned `\vspace` in content — adjust a knob instead. Both resumes fit on exactly one page with little slack, so recompile and check the page count after any edit.
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
