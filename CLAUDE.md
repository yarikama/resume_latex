# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LaTeX resume repository with multiple resume variants (SWE vs GenAI/AI Engineer) and a cover letter system. It is split three ways: layout in `resumestyle.sty`, content in `content/` (one file per entry), and each resume `.tex` is a thin driver that only picks which entries appear and in what order. A layout change is made once in the package; an entry is written once in `content/` and `\input` by whichever resumes want it.

## Build Commands

Build both resumes and verify each still fits on one page:
```
make
```
`make` rebuilds **every resume**, the two general resumes and every `applications/*/` variant, then fails if any PDF is not exactly 1 page. Variants are included on purpose: one that nothing rebuilds goes stale silently, which is how nine of them kept a broken text layer after the fix had already landed in the shared header. A no-op run costs under two seconds, because latexmk compares file contents and exits immediately when there is nothing to do. Always use this after editing `resumestyle.sty` or anything under `content/shared/` — an editor's on-save build only rebuilds the file you have open, leaving every other variant stale.

Check every built PDF for orphan lines, including the cover letters:
```
make orphans
```
`make check` already runs this over every resume. It is a **warning, never a gate**: the page count is binary, but orphan detection is a heuristic, so it prints what it found and lets the build pass. `tools/check-orphans.py` reads the real word geometry out of `pdftotext -bbox-layout` and flags a wrapped bullet or paragraph whose last line holds 2 words or fewer, or fills under 25% of the text width. Tune with `--min-words` / `--min-fill`, silence the clean files with `--quiet`, and pass `--strict` to make it exit 1 for a hook or CI. It needs `pdftotext` (`brew install poppler`) and skips itself with a warning if that is missing.

Score every resume for ATS parseability (0-100 plus a letter grade):
```
make ats
```
`make check` runs this over every resume too. Same eight weighted checks and grade bands as career-ops' `verify-ats.mjs`, but that tool only reads the HTML career-ops' own `pdf` mode emits, and this repo ships XeLaTeX PDFs, so `tools/check-ats.py` measures the PDF an ATS actually receives: text layer, standard headings, an extractable email, single-column reading order, text baked into images, font embedding, ToUnicode coverage and hidden white text. The one check that does not carry over is "UTF-8 declared", a markup concern; its 5 points go to ToUnicode coverage instead. Alongside the score it reports **Greenhouse's own published parse-failure causes** as a separate pass/fail list ([their docs](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse)): file size, placeholder data, letter-spacing, graphics, image-only uploads, abbreviated job titles, columned layouts. That list is deliberately **not folded into the score** and never will be: the weights above are one person's judgement with no external basis, while every checklist row traces to the vendor, so averaging them would hide which is which. Two rows report `unknown` on purpose, because an untagged PDF carries no table or page-header semantics to measure. Default output shows only failures; `--checklist` shows every row. `--keywords "a,b,c"` adds advisory coverage that never moves the score, `--json` is machine-readable, and `--strict` restores the 0/1 exit contract. Resumes only: the rubric expects Experience / Education / Skills headings, so a cover letter scores as an F for no useful reason.

List every project, one card each, before choosing what goes on a resume:
```
make bank
```
The cards come from `content/bank/projects/`, the complete record of every project (see **Project bank** under Architecture). `make check` runs the same `tools/check-bank.py` without `--list`: it checks each card and facet, that every project module carries a `% bank: <id>` marker whose dates and link agree with its card, that no bank file names a company, a per-application path or a secret, and, when the gitignored `content/bank/private/retracted.txt` exists, that no retracted phrase has crept back anywhere under `content/`, comments included. A warning, never a gate, with the same `--quiet` / `--strict` contract as the orphan check.

Compile a single file (cover letters, one-off checks):
```
latexmk -xelatex <filename>.tex
```

Intermediates (`.aux`, `.log`, `.fls`, `.fdb_latexmk`, `.out`, `.xdv`) go to `build/` via latexmk's `-auxdir`, not the repo root: six per driver across eleven drivers was 66 of the 97 files sitting next to the sources. The **PDF still lands beside its `.tex`**, because that is the file you attach to an application and git tracks it. `build/` and `cover_letters/build/` are gitignored. A one-off `latexmk -xelatex <file>.tex` without `-auxdir` will scatter intermediates back into the root; pass `-auxdir=build` or just use `make`.

Builds are **reproducible**: `SOURCE_DATE_EPOCH` is pinned in the Makefile, so the same sources give byte-identical PDFs and `git status` after a build reflects a real change rather than a new timestamp. Without it XeLaTeX stamps the wall clock into `/CreationDate` and `/ID` and every `make` marked all eleven tracked PDFs modified. It is a fixed constant rather than anything git-derived, because the PDFs are committed alongside the sources they are built from, so a git-derived timestamp would move the moment you commit and dirty the tree again on the next build. A PDF's stated creation date therefore stays put until the constant is bumped; that is metadata nobody reads, traded for a tree that tells the truth.

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
- **Project bank**: `content/bank/projects/<id>.tex` is the complete record of every project, one file each, and the **source of truth for project facts**. career-ops' `cv.md` Projects section is a summary synced from it; experience, education and skills still trace to `cv.md`.
  - **Layout of a bank file.** A card comes first (`id`, `title`, `dates`, `link`, `team`, `status`, `tech`, `signals`, `summary`, `verified`). Then CONSTRAINTS that every wording must respect. Then one `FACET` per claimable facet, each with an `Evidence:` line and a full-length `\resumeItem`. Last come UNVERIFIED and INTERVIEW NOTES blocks, which never reach a page.
  - **Never `\input` a bank file.** Its facets are bare `\resumeItem`s with no list around them, so an accidental `\input` fails loudly with "Lonely \item".
  - **Every project module carries `% bank: <id>` on line 1**, canonical or customized. `make check` warns when a module's dates or link disagree with its card.
  - **It names no one.** The repo is public, so a bank file names no company, application or teammate. Teammates' names and splits, contested authorship, interview caveats and retracted phrases go in `content/bank/private/<id>.md`, which is gitignored.

  It exists because before it, the best wording of each project lived in whichever company folder last rewrote it, variants forked from other variants, and one wrong date range sat on fifteen resumes.
- **Resume variants**: `Henry_Hsu_SWE_resume.tex` (Software Engineer) and `Henry_Hsu_GAIE_resume.tex` (GenAI/AI Engineer) are drivers: `\documentclass`, `\usepackage{resumestyle}`, `\mylocation`, then `\section` scaffolding around `\input` lines. Retarget a resume by swapping `\input` lines — never paste an entry body into a driver.
- **Module pool**: every project has a bank file whether or not a resume currently uses it, so `make bank` is the complete project list. `content/resume/` also holds modules no current resume uses (inactive project framings, three extracurricular entries). They are ready to `\input`, not commented out. Add to the pool rather than deleting an entry you are dropping from a resume.
- **One directory per resume, one filename for every resume PDF.** `general_resume/SWE/` and `general_resume/GAIE/` hold the two resumes that keep evolving; `applications/<company>/` holds one directory per **application** (company plus role, hence `bytedance-agenteval` and `bytedance-agentsec`) carrying that application's resume, cover letter and any supplement. The split mirrors `content/resume/` versus `content/customized/`. Every resume PDF is `Henry_Hsu_Resume.pdf`, because that filename is what a recruiter and their ATS see; the `.tex` keeps a descriptive name so the editor tabs stay tellable apart, and `latexmk -jobname` decouples the two. Cover letters keep the company in the filename **on purpose**: a resume names no company, so attaching the wrong one costs a slightly less tailored document, while a letter names the company in its first line and attaching the wrong one is unrecoverable.
- **Everything builds from the repo root.** **TeX resolves `\input` against the current directory, not the file's own directory**, so `cd applications/openai && latexmk ...` breaks. latexmk does not `cd` by default, so `make` is right. The one exception is the generic cover-letter template, which `make cover` still builds from inside `cover_letters/`.
- **A content change starts in `content/resume/`, or for a project in its bank file, never in a `content/customized/<company>/` copy.** A customized module exists to reframe one entry for one posting. It is not the place to fix a typo, update a metric, add a shipped project or add a skill, because the fix would then exist in exactly one application while every other resume keeps the old version.
  - There are twenty-two customized skills files against two general ones, which is how far this drifts unenforced.
  - For a non-project entry: change the general module, run `make` to see who no longer fits on one page, and only then add a customized override for deliberate re-emphasis, recording in its header comment what it changed and why.
  - For a project: change the bank file first and sync `cv.md`. Then change every module that carries its marker; `grep -rl '^% bank: <id>' content/` lists them.

  A customized module differing from its general counterpart, or from its bank file, by anything other than deliberate reframing is a bug.
- **Per-application content modules live in `content/customized/<company>/`**: modules written for one specific job posting, not for the general pool. Same file shape as `content/resume/`, one entry per file, each ending in `%`. A tailored resume gets its own driver in `applications/<company>/` (see the bullets above) whose `\input` lines mix canonical modules with the customized ones. Keeping them out of `content/resume/` means the general pool stays the set of entries any resume might reuse, while one-off reframings do not accumulate there. Every customized module's header comment records what it changed versus the canonical module and why. A customized project module is written from the bank file, never forked from another application's module, and its header names the facets it used.
- **Duplicate content is intentional**: style is DRY, content is not. When a project or role needs different framing per target (e.g. `projects/chat-bar-server.tex` vs `projects/chat-bar-mud.tex`, `experience/google-swe.tex` vs `experience/google-gaie.tex`), write a second module. Do not try to parameterise one file into serving both — the point of tailoring is that the sentences differ. For a project, each such module is a different selection from the same bank file.
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
- **One bullet, one point, and no orphan lines**: a bullet carries a single point. **One line is the target, two lines is acceptable, three lines is not** — a three-line bullet is two points wearing one bullet, so split it or cut it. On top of that, no bullet, sentence or paragraph may wrap so that its final line holds only one or two short words: it reads as a typo at a glance and it burns a whole line of a page that has no slack.

  There are two ways to fix an orphan, and they are not equal. **Default to cutting a word or two.** The page has no slack, so the line you reclaim is nearly always worth more somewhere else, and this is the right move even when the bullet still has room to say more. **Add information only when the line genuinely cannot be cut further** — then fill it with real substance (a metric, a scope, a system name), never with filler words or hedging that pads the measure without adding a fact. What is never acceptable is reaching for a spacing knob in `resumestyle.sty`, which reflows every other entry on the page.

  Judge it on the built PDF, never on the source: the wrap point depends on font metrics and the text width, so a tidy 100-column source line says nothing about where it actually breaks. `make orphans` checks every built PDF for exactly this, including the cover letters; `make check` runs it over every resume. It warns rather than failing, so it is on you to act on it.

- **ATS text layer**: `resumestyle.sty` sets `\XeTeXgenerateactualtext=1` (guarded with `\ifdefined`, it is XeTeX-only), and the cover letters set the same thing in their own preambles. Without it the `sourcesanspro` ToUnicode CMap maps every hyphen to U+2011 NON-BREAKING HYPHEN, so `pdftotext` returned zero ASCII hyphens: the phone number, `real-time`, `scikit-learn` and every other compound came out unmatchable by an ATS regex, while looking perfectly normal on the page. Do not remove it. Check with `pdftotext file.pdf - | grep -c '‑'` — it should be 0.

  The same class of bug hit the **FontAwesome** icons, which ship no ToUnicode CMap at all, so each one landed in the text layer as a junk Latin character: the contact line extracted as `× +1-510-996-6837 ç www.yarikama.com ] yarikama a yarikama ć hsuhengjui@gmail.com`. `content/shared/header.tex` now wraps every icon in `\atsicon`, a marked-content span with an empty `ActualText`, so an extractor emits nothing for the glyph while the page renders identically. The macro is defined there with `\providecommand` rather than in `resumestyle.sty`, because that file is shared with the cover letters and must stay standalone. `check-ats.py` flags a missing ToUnicode CMap only when junk actually reaches the text layer, so it stays quiet once a document is wrapped.
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
- Never `\input` a file under `content/bank/`: it is a record, not a page. Never copy anything from `content/bank/private/` into a tracked file.
