# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LaTeX resume repository with multiple resume variants (SWE vs GenAI/AI Engineer) and a cover letter system. Each `.tex` file is fully self-contained — there are no shared `.cls` or `.sty` files. Each resume duplicates the same ~128-line preamble: same custom commands, same list/section spacing. Because it is duplicated rather than shared, any preamble edit must be applied to both files by hand.

## Build Commands

Compile any `.tex` file:
```
latexmk -xelatex <filename>.tex
```

Clean synctex files:
```
make clean
```

The Makefile only has a `clean` target. There is no `build` or `all` target — compilation is done directly with `latexmk` + `xelatex`.

## Formatting

LaTeX source is formatted with `latexindent` configured via `.latexindent.yaml` (2-space indent, 100-column text wrap, no backups).

## Architecture

- **Resume variants**: `Henry_Hsu_SWE_resume.tex` (Software Engineer) and `Henry_Hsu_GAIE_resume.tex` (GenAI/AI Engineer). Both share the same preamble, contact header, education, awards, and skills sections but differ in work experience bullets, project selections, and skills emphasis. Unused sections are commented out rather than removed.
- **Cover letters**: `cover_letters/cover_letter.tex` is the tracked generic template. Company-specific letters go in `cover_letters/specific_comps/` (gitignored).
- **Custom commands** (identical in both resume preambles, each with a doc comment above its definition):
  - `\resumeEntry{title}{date}{org}{location}` — entry header, two rows
  - `\resumeEntryNoOrg{title}{date}` — entry header, single row (no org/location)
  - `\resumeEntryDetail{text}{right}` — detail row, plain left / italic right
  - `\resumeProjectEntry{title}{date}` — project header
  - `\resumeItem{text}` — one bullet
  - `\resumeEntryListStart`/`End` — outer list of entries; `\resumeItemListStart`/`End` — inner bullet list
- **Spacing knobs**: `\setlist[itemize]` (`itemsep=1pt`, `topsep=1pt`) and `\titlespacing*{\section}` (`3pt`/`3pt`). Both resumes fit on exactly one page with little slack — changing these reflows the whole document, so recompile and check the page count after any edit.
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

- When modifying the shared preamble or custom commands, changes must be applied to **both** resume `.tex` files to keep them in sync.
- The project uses XeLaTeX (not pdfLaTeX) for font support via `fontspec`.
- PDFs are tracked in git. Recompile and include updated PDFs when modifying `.tex` content.
