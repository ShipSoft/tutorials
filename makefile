SLIDES := $(patsubst %.md,%.slides.pdf,$(wildcard *.md))
HANDOUT := $(patsubst %.md,%.handout.pdf,$(wildcard *.md))

all : $(SLIDES) # $(HANDOUT)

%.slides.pdf : %.md event.pdf
	pandoc $< -t beamer --slide-level 2 -o $@ --pdf-engine=tectonic --template default.latex

%.handout.pdf : %.md
	pandoc $< -t latex -o $@ --pdf-engine=tectonic # --template default.latex

%.pdf: %.dot
	dot -T pdf $< -o $@

clobber :
	rm -f $(SLIDES) $(HANDOUT)
