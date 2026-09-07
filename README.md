## Henry Hsu — LaTeX Resume

LaTeX source for Henry Hsu's resume, in two variants, plus a cover letter template.

| | View | Download |
|---|---|---|
| Software Engineer | [PDF](https://github.com/yarikama/resume_latex/blob/main/Henry_Hsu_SWE_resume.pdf) | [raw](https://raw.githubusercontent.com/yarikama/resume_latex/main/Henry_Hsu_SWE_resume.pdf) |
| GenAI / AI Engineer | [PDF](https://github.com/yarikama/resume_latex/blob/main/Henry_Hsu_GAIE_resume.pdf) | [raw](https://raw.githubusercontent.com/yarikama/resume_latex/main/Henry_Hsu_GAIE_resume.pdf) |

### Layout

```
resumestyle.sty            all layout: packages, margins, spacing knobs, \resume* commands
Henry_Hsu_*_resume.tex     thin drivers -- they only pick which entries appear, in what order
content/
  shared/header.tex        contact details, single source, shared with the cover letters
  resume/                  one file per entry (experience, projects, education, ...)
cover_letters/             generic template; per-company letters are not tracked
docs/                      reference material
```

Each entry lives in exactly one file under `content/resume/`, including entries no
current resume uses. Retarget a resume by swapping `\input` lines, not by editing
entry bodies in place.

### Build

```
make          # build both resumes, fail if either is not exactly 1 page, then the cover letter
make clean    # remove build artifacts (PDFs are kept and tracked)
```

Requires XeLaTeX — the documents use `fontspec`, and a pdfLaTeX build silently
produces a different, wrong PDF.

### Signature

`cover_letters/sign.png` is deliberately **not** tracked: a scanned signature does not
belong in a public repository. The template builds fine without it and picks it up
automatically if you drop your own copy into `cover_letters/`.
