## Henry Hsu — LaTeX Resume

LaTeX source for Henry Hsu's resume, in two variants, plus a cover letter template.

| | View | Download |
|---|---|---|
| Software Engineer | [PDF](https://github.com/yarikama/resume_latex/blob/main/general_resume/SWE/Henry_Hsu_Resume.pdf) | [raw](https://raw.githubusercontent.com/yarikama/resume_latex/main/general_resume/SWE/Henry_Hsu_Resume.pdf) |
| GenAI / AI Engineer | [PDF](https://github.com/yarikama/resume_latex/blob/main/general_resume/GAIE/Henry_Hsu_Resume.pdf) | [raw](https://raw.githubusercontent.com/yarikama/resume_latex/main/general_resume/GAIE/Henry_Hsu_Resume.pdf) |

### Layout

```
resumestyle.sty                all layout: packages, margins, spacing knobs, \resume* commands
general_resume/{SWE,GAIE}/     the two general resumes: thin drivers that pick entries and order
applications/<application>/    one directory per application, each with its own driver
content/
  shared/header.tex            contact details, single source, shared with the cover letters
  resume/                      one file per entry (experience, projects, education, ...)
  customized/<application>/    entries reframed for one posting
  bank/projects/               the complete, verified record of every project; never \input
cover_letters/                 generic template; per-company letters are not tracked
tools/                         the orphan, ATS and project-bank checks behind `make check`
.claude/skills/                the resume and cover-letter processes, as Claude Code skills
```

Each entry lives in one file under `content/resume/`, including entries no current
resume uses. Every project also has a bank file holding everything that could be said
about it, with its evidence; a resume's project entry is a selection from it. Retarget
a resume by swapping `\input` lines, not by editing entry bodies in place.

### Build

```
make          # build every resume, fail if any is not exactly 1 page, then the letters
make check    # the page gate plus orphan, ATS and project-bank warnings
make bank     # list every project in the bank, one card each
make clean    # remove build artifacts (PDFs are kept and tracked)
```

Requires XeLaTeX — the documents use `fontspec`, and a pdfLaTeX build silently
produces a different, wrong PDF.

### Signature

`cover_letters/sign.png` is deliberately **not** tracked: a scanned signature does not
belong in a public repository. The template builds fine without it and picks it up
automatically if you drop your own copy into `cover_letters/`.
