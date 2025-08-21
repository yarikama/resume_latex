TEX=Henry_Hsu_Resume.tex
PDF=$(TEX:.tex=.pdf)

.PHONY: all pdf watch clean fmt

all: pdf

pdf:
	latexmk -xelatex $(TEX)

watch:
	latexmk -xelatex -pvc $(TEX)

clean:
	latexmk -C

fmt:
	latexindent -w $(TEX)
