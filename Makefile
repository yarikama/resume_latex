RESUMES := Henry_Hsu_SWE_resume Henry_Hsu_GAIE_resume
PDFS    := $(addsuffix .pdf,$(RESUMES))

# XeLaTeX is required -- the preamble uses fontspec. A pdfLaTeX build silently
# produces a different, wrong PDF.
LATEXMK := latexmk -xelatex -interaction=nonstopmode

.PHONY: all check clean

# Build every resume, then verify each still fits on one page.
all: check

# resumestyle.sty is a prerequisite: one style edit reflows every variant.
%.pdf: %.tex resumestyle.sty
	$(LATEXMK) $<

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

clean:
	find . -name "*.synctex.gz" -delete
	$(LATEXMK) -c $(addsuffix .tex,$(RESUMES)) >/dev/null
