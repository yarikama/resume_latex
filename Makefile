RESUMES := Henry_Hsu_SWE_resume Henry_Hsu_GAIE_resume
PDFS    := $(addsuffix .pdf,$(RESUMES))

# XeLaTeX is required -- the preamble uses fontspec. A pdfLaTeX build silently
# produces a different, wrong PDF.
LATEXMK := latexmk -xelatex -interaction=nonstopmode

.PHONY: all check clean cover $(PDFS)

# Build every resume, verify each still fits on one page, then build the
# tracked cover letter template.
all: check cover

# The PDF targets are deliberately phony so latexmk runs every time and makes
# the decision itself: it knows the real dependency graph (resumestyle.sty plus
# every \input'ed content module, recorded in the .fls file) and compares file
# contents, so it catches same-second edits that make's mtime check misses.
# It exits immediately when there is nothing to do.
$(PDFS): %.pdf: %.tex
	@$(LATEXMK) $<

check: $(PDFS)
	@status=0; \
	for pdf in $(PDFS); do \
	  pages=$$(pdfinfo $$pdf | awk '/^Pages:/ {print $$2}'); \
	  if [ "$$pages" = "1" ]; then \
	    echo "ok   $$pdf (1 page)"; \
	  else \
	    echo "FAIL $$pdf is $$pages pages -- must be exactly 1"; \
	    status=1; \
	  fi; \
	done; \
	exit $$status

# Built from inside its own directory: it \input's ../content/shared/header
# and \includegraphics's sign.png, both relative to cover_letters/.
cover:
	@cd cover_letters && $(LATEXMK) cover_letter.tex

clean:
	find . -name "*.synctex.gz" -delete
	cd cover_letters && $(LATEXMK) -c cover_letter.tex >/dev/null
	$(LATEXMK) -c $(addsuffix .tex,$(RESUMES)) >/dev/null
