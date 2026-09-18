# Every resume lives in its own directory and every resume PDF is called
# Henry_Hsu_Resume.pdf, because that filename is what a recruiter and their ATS
# actually see. The .tex keeps a descriptive name so eleven editor tabs are
# still tellable apart; latexmk's -jobname decouples the two.
#
#   general_resume/SWE/Henry_Hsu_SWE_resume.tex  -> general_resume/SWE/Henry_Hsu_Resume.pdf
#   applications/openai/..._openai.tex           -> applications/openai/Henry_Hsu_Resume.pdf
#
# general_resume/ holds the two resumes that keep evolving; applications/ holds
# one directory per APPLICATION (company plus role, hence bytedance-agenteval
# and bytedance-agentsec) carrying that application's resume, cover letter and
# any supplement. The split mirrors content/resume/ versus content/customized/.
#
# EVERY .tex here is built FROM THE REPO ROOT. TeX resolves \input against the
# current directory, not the file's own directory, so `cd applications/openai
# && latexmk ...` breaks. Use make.
GENERAL_DIRS := $(sort $(dir $(wildcard general_resume/*/Henry_Hsu_*.tex)))
APP_DIRS     := $(sort $(dir $(wildcard applications/*/Henry_Hsu_*.tex)))
RESUME_DIRS  := $(GENERAL_DIRS) $(APP_DIRS)
RESUME_PDFS  := $(addsuffix Henry_Hsu_Resume.pdf,$(RESUME_DIRS))

# Cover letters keep the company in the filename ON PURPOSE. A resume names no
# company, so attaching the wrong one costs you a slightly less tailored
# document; a cover letter names the company in its first line, so attaching
# the wrong one is unrecoverable. The generic name is only safe where the
# content is generic.
LETTER_TEX  := $(wildcard applications/*/cover_letter_*.tex) $(wildcard applications/*/*_supplement.tex)
LETTER_PDFS := $(LETTER_TEX:.tex=.pdf)

# XeLaTeX is required -- the preamble uses fontspec. A pdfLaTeX build silently
# produces a different, wrong PDF.
# -auxdir keeps .aux/.log/.fls/.fdb_latexmk/.out/.xdv out of the working tree.
LATEXMK := latexmk -xelatex -interaction=nonstopmode -auxdir=build
ORPHANS := python3 tools/check-orphans.py
ATS     := python3 tools/check-ats.py

.PHONY: all ats check clean cover letters orphans $(RESUME_PDFS) $(LETTER_PDFS)

# Build every resume, verify each still fits on one page, then the letters and
# the tracked generic template.
all: check letters cover

# One generated rule per resume directory. The targets are deliberately phony
# so latexmk runs every time and makes the decision itself: it knows the real
# dependency graph (resumestyle.sty plus every \input'ed content module,
# recorded in the .fls file) and compares file CONTENTS, so it catches
# same-second edits that make's mtime check misses, and exits immediately when
# there is nothing to do. A no-op pass over all eleven costs under two seconds.
#
# Variants are in the default build on purpose: one that nothing rebuilds goes
# stale silently, which is how nine of them kept a broken text layer after the
# fix had already landed in content/shared/header.tex.
define RESUME_RULE
$(1)Henry_Hsu_Resume.pdf: $(wildcard $(1)Henry_Hsu_*.tex)
	@$$(LATEXMK) -outdir=$(1) -jobname=Henry_Hsu_Resume $$<
endef
$(foreach d,$(RESUME_DIRS),$(eval $(call RESUME_RULE,$(d))))

$(LETTER_PDFS): %.pdf: %.tex
	@$(LATEXMK) -outdir=$(dir $@) $<

letters: $(LETTER_PDFS)

check: $(RESUME_PDFS)
	@status=0; \
	for pdf in $(RESUME_PDFS); do \
	  pages=$$(pdfinfo $$pdf | awk '/^Pages:/ {print $$2}'); \
	  if [ "$$pages" = "1" ]; then \
	    echo "ok   $$pdf (1 page)"; \
	  else \
	    echo "FAIL $$pdf is $$pages pages -- must be exactly 1"; \
	    status=1; \
	  fi; \
	done; \
	$(ORPHANS) $(RESUME_PDFS) || true; \
	$(ATS) $(RESUME_PDFS) || true; \
	exit $$status

# Orphan lines are a WARNING, never a gate. Unlike the page count, which is
# binary, this is a heuristic over the PDF's real text geometry, and a short
# last line is occasionally the right call -- so it reports and lets the build
# pass. `make check` covers the resumes; `make orphans` adds every letter.
# Prefer cutting a word or two; add information only when the line cannot be
# cut further, and never touch a spacing knob.
orphans:
	@$(ORPHANS) $(RESUME_PDFS) $(LETTER_PDFS) $(wildcard cover_letters/*.pdf)

# ATS parseability, 0-100 plus a letter grade, on the same weights as
# career-ops' verify-ats.mjs but measured on the PDF an ATS actually receives,
# plus Greenhouse's own published parse-failure list as a separate pass/fail
# section. Also a warning and not a gate. Resumes only, since the rubric
# expects Experience / Education / Skills headings that a letter never carries.
ats:
	@$(ATS) $(RESUME_PDFS)

# The generic template is the one letter still built from inside its own
# directory: it \input's ../content/shared/header and sign.png relative to
# cover_letters/. The per-application letters were rewritten to root-relative
# paths when they moved, so they build from the root like everything else.
cover:
	@cd cover_letters && $(LATEXMK) cover_letter.tex

clean:
	rm -rf build cover_letters/build
	find . -name "*.synctex.gz" -delete
	cd cover_letters && $(LATEXMK) -c cover_letter.tex >/dev/null
