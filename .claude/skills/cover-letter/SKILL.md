---
name: cover-letter
description: Write a tailored cover letter for a specific company or job ad, using this repo's LaTeX template. Use whenever Henry asks for a cover letter, wants one revised, pastes a job description to apply to, or asks which of his experiences to feature for a role. Runs a STAR interview before drafting and never invents experience details.
---

# Cover Letter

Writes one-page, company-specific cover letters into `cover_letters/specific_comps/`,
built on `cover_letters/cover_letter.tex`.

The standards below come from the Rice Center for Career Development guidelines and
the CMU Global Communication Center handout Henry was given. They are the whole
substance of those documents — the PDFs are gone; this is the record.

## The one rule that matters most

**A cover letter is not a prose résumé.** The résumé already lists what he did. The
letter's job is to state the *qualifications those experiences produced* and argue
they transfer to this employer's problems.

Test every sentence: *could another Rice M.C.S. new grad have written this exact
sentence?* If yes, it is filler — cut it or make it specific. "I am passionate about
distributed systems and a fast learner" fails. "Scaling MaiAgent's indexing pipeline
from 3M to 20M records taught me to ship schema migrations that stay
backward-compatible under live traffic" passes.

## Workflow

Do not skip ahead. Steps 1–4 happen before a single sentence is drafted.

### 1. Get the actual job ad

Ask for the posting text if it was not provided. Do not work from a company name and
a job title alone — without the ad there is nothing to tailor to, and the letter will
come out generic. Also establish:

- **Who to address.** Hiring manager or recruiter by name if findable. `Dear Hiring
  Team,` is the fallback. **Never "To whom it may concern."**
- Whether this is an internship, new grad, or full-time role.

### 2. Read his material

- `Henry_Hsu_SWE_resume.tex` and `Henry_Hsu_GAIE_resume.tex` (both — the framing
  differs and the right one depends on the role)
- `content/resume/` for the full pool, including entries no current resume uses
- The `star_stories.md` memory file for detail already collected in past sessions.
  **Check it first** — do not re-ask questions he has already answered.

### 3. Analyse the ad

Produce, and show him:

- **Must-have vs nice-to-have** requirements, separated.
- **At least three qualifications** the employer is actually seeking.
- **Three of his achievements** that map onto those, and which resume entry each
  comes from.
- **Gaps** — requirements he has no evidence for. Say so plainly. A letter that
  quietly skips a must-have is a weaker letter than one that reframes an adjacent
  strength.
- **A company-specific hook**: something about their product, mission, or technical
  problem that could not be said about a competitor. "An excellent company" is not a
  hook. If nothing specific can be found, say so rather than inventing enthusiasm.

### 4. STAR interview — one cluster at a time

Tag every question with the requirement that motivated it, e.g.
`[Must-have: "distributed systems at scale"]`, so he can see why he is being asked.

Ask Situation → Task → Action → Result **one cluster at a time and stop for
answers**. Do not dump twenty questions at once; do not proceed on assumptions.

Full question bank and probing areas: `references/star-interview.md`.

**Never invent or embellish a detail.** No inferred metrics, no assumed team sizes,
no guessed technologies. If something is unclear, ask. This is the single most
important constraint in the whole workflow — a fabricated detail in a cover letter is
a fabrication he has to defend in an interview.

### 5. Draft

One paragraph per qualification. Structure per paragraph:

1. Sentence 1–2 names the qualification.
2. The rest is specific supporting evidence — the STAR story, compressed.
3. A clause connecting it to what this employer does.

Body paragraphs must read as **narrative prose**, not résumé bullets joined by
transition words. Bulleted qualifications are an accepted alternative format (Rice's
own sample uses them), but **at most three** and each still needs a bolded lead-in
plus real supporting detail.

Intro paragraph (3–4 sentences):
- Name the position and how he heard about it
- Degree, major, institution, expected graduation (M.C.S., Computer Science, Rice
  University, Dec. 2026)
- Close with a claim previewing the 1–3 qualifications the body will argue

Closing paragraph:
- Why he is a strong match for this role and this organisation
- Mention the enclosed résumé
- Request an interview / state availability
- Thank the reader

Full quality bar, with the before/after rewrites: `references/quality-bar.md`.

### 6. Self-check before showing him

Run the checklist in `references/quality-bar.md`. The ones most often failed:

- **Sentence openings vary** — consecutive sentences starting with "I" is the most
  common tell of a weak letter.
- **One page**, no exceptions.
- **Verbs calibrated to actual autonomy** — "designed" and "led" vs "contributed to"
  and "supported". Confirm which is true before using the stronger verb. Avoid
  "pioneered" unless genuinely warranted.
- No sentence survives that fails the "any M.C.S. grad could write this" test.

### 7. Build it

```
cp cover_letters/cover_letter.tex cover_letters/specific_comps/cover_letter_<company>.tex
cd cover_letters/specific_comps && latexmk -xelatex cover_letter_<company>.tex
```

Then confirm the PDF is exactly one page.

## Template facts

- **Copy `cover_letters/cover_letter.tex`.** Never write a letter from scratch, and
  never use the flatter style of the older letters in `specific_comps/`.
- The contact header is `\input{../content/shared/header}` — shared with the resumes,
  so the letter's header and font match the résumé automatically. A letter in
  `specific_comps/` is one directory deeper: the path becomes
  `\input{../../content/shared/header}`.
- `sign.png` lives in `cover_letters/`, is deliberately untracked, and is guarded by
  `\IfFileExists`. A letter in `specific_comps/` needs the path adjusted or the guard
  silently drops the signature. **Check the built PDF actually shows it.**
- **XeLaTeX only.** Get fonts via `\usepackage[default]{sourcesanspro}`; never
  `\setmainfont{Source Sans Pro}` (not installed system-wide — it breaks the build).
- `specific_comps/` is gitignored. Letters there exist only on the local disk.
