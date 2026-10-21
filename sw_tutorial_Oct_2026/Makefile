# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: CC-BY-4.0
#
#   make              participant edition  -> booklet.pdf
#   make organiser    organiser edition    -> booklet-organiser.pdf
#   make all          both
#   make check        list the [TBD] items still to fill in
#   make tectonic     build both with tectonic instead of latexmk
#   make participant-archive  framework-booklet-participant.tar.gz without the
#                     organiser edition, solutions, generator and tests
#   make clean        remove auxiliary files

SOURCES := booklet.tex shipbooklet.sty $(wildcard chapters/*.tex) $(wildcard figures/*) \
           $(shell find code -type f)
LATEXMK := latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: participant organiser all check tectonic clean participant-archive

participant: booklet.pdf
organiser: booklet-organiser.pdf
# The organiser edition is built only where its sources exist (not in the
# public, participant copy).
all: participant $(if $(wildcard booklet-organiser.tex),organiser)

booklet.pdf: $(SOURCES)
	$(LATEXMK) booklet.tex

booklet-organiser.pdf: booklet-organiser.tex $(SOURCES)
	$(LATEXMK) booklet-organiser.tex

tectonic:
	tectonic booklet.tex
	tectonic booklet-organiser.tex

check:
	@grep -n '\\tbd{' booklet.tex chapters/*.tex || echo "no TBD items left"

clean:
	latexmk -C booklet.tex booklet-organiser.tex

# What participants get: no organiser edition, no reference solutions, no
# generator, no tests (tests/ and the organiser edition reveal the answers).
participant-archive: booklet.pdf
	cd .. && tar -czf framework-booklet-participant.tar.gz \
	  --exclude='framework-booklet/.git' \
	  --exclude='framework-booklet/code/teamwork/organiser' \
	  --exclude='framework-booklet/code/geometry/organiser' \
	  --exclude='framework-booklet/tests' \
	  --exclude='framework-booklet/tools' \
	  --exclude='framework-booklet/booklet-organiser.*' \
	  --exclude='framework-booklet/REVIEW.md' \
	  --exclude='*.aux' --exclude='*.log' --exclude='*.fls' --exclude='*.fdb_latexmk' \
	  --exclude='*.toc' --exclude='*.out' --exclude='__pycache__' --exclude='.ruff_cache' \
	  framework-booklet
	@echo "wrote ../framework-booklet-participant.tar.gz"
