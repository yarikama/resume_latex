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

LaTeX source is formatted with `latexindent` configured via `.latexindent.yaml` (2-space indent,
trailing whitespace stripped, one `.bak` at most). The 100-column text wrap lives under
`modifyLineBreaks`, so it only applies when latexindent is run with `-m`.

## Architecture

- **Shared style**: `resumestyle.sty` carries the whole layout. Loading it is the entire preamble of a resume file.
- **Content modules**: `content/resume/` holds one file per entry — `awards.tex`, `summary/`, `experience/`, `education/`, `projects/`, `extracurricular/`, `skills/`. `content/shared/header.tex` is the single source of contact details and is shared with the cover letters, so it must not reference anything defined in `resumestyle.sty` (the caller owns the spacing after it). There is no `\mylocation` indirection any more: the address lives in that one file. Each file contains exactly one `\resumeEntry` / `\resumeProjectEntry` block (or one section's lines) and **must end with `%`** so `\input` does not inject a blank line, which would add a stray `\par` of vertical space.
- **Resume variants**: `Henry_Hsu_SWE_resume.tex` (Software Engineer) and `Henry_Hsu_GAIE_resume.tex` (GenAI/AI Engineer) are drivers: `\documentclass`, `\usepackage{resumestyle}`, `\mylocation`, then `\section` scaffolding around `\input` lines. Retarget a resume by swapping `\input` lines — never paste an entry body into a driver.
- **Module pool**: `content/` also holds entries no current resume uses (six inactive projects, three extracurricular entries). They are ready to `\input`, not commented out. Add to the pool rather than deleting an entry you are dropping from a resume.
- **Per-application variants live in `content/customized/<company>/`**: modules written for one specific job posting, not for the general pool. Same file shape as `content/resume/`, one entry per file, each ending in `%`. A tailored resume gets its own driver at the repo root (`Henry_Hsu_SWE_resume_notion.tex`, `Henry_Hsu_GAIE_resume_fervo.tex`) whose `\input` lines mix canonical modules with the customized ones. Keeping them out of `content/resume/` means the general pool stays the set of entries any resume might reuse, while one-off reframings do not accumulate there. `make` does not build these drivers (`RESUMES` lists only the two canonical resumes), so build them with `latexmk -xelatex <driver>.tex` and check the page count yourself. Every customized module's header comment records what it changed versus the canonical module and why.
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
- **ATS text layer**: `resumestyle.sty` sets `\XeTeXgenerateactualtext=1` (guarded with `\ifdefined`, it is XeTeX-only), and the cover letters set the same thing in their own preambles. Without it the `sourcesanspro` ToUnicode CMap maps every hyphen to U+2011 NON-BREAKING HYPHEN, so `pdftotext` returned zero ASCII hyphens: the phone number, `real-time`, `scikit-learn` and every other compound came out unmatchable by an ATS regex, while looking perfectly normal on the page. Do not remove it. Check with `pdftotext file.pdf - | grep -c '‑'` — it should be 0.
- **Key packages**: `sourcesanspro` (font), `fontawesome5` (icons), `titlesec`, `enumitem`, `tabularx`, `hyperref`, `xcolor`.

## Cover Letter Workflow

Use the **`cover-letter` skill** (`.claude/skills/cover-letter/`). It carries the full
process — job-ad analysis, the STAR interview, the drafting standards from the Rice CCD
and CMU GCC guidance, and the template's path/build quirks. Do not reimplement it here;
edit the skill instead.

Company-specific letters are saved as `cover_letters/specific_comps/cover_letter_<company>.tex`.

## Important Notes

- Layout changes go in `resumestyle.sty` only — never copy layout back into a resume `.tex`. Recompile **both** resumes afterwards, since one package edit reflows every variant.
- Always compile with XeLaTeX. A pdfLaTeX build silently produces a different (wrong) PDF — check `pdffonts` shows `CID Type 0C` fonts if a PDF looks unexpectedly different.
- The project uses XeLaTeX (not pdfLaTeX) for font support via `fontspec`.
- PDFs are tracked in git. Recompile and include updated PDFs when modifying `.tex` content.
