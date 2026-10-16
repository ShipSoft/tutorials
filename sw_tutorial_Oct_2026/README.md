# SHiP software framework tutorial booklet

LaTeX booklet for the hands-on tutorial on the new SHiP software, built as a
sequence of small steps (roadmap in the preface; every chapter opens with what
it needs and teaches, and closes with a self-check). Part I needs no SHiP
software: git on your own, branches (merge versus rebase), remotes and ShipSoft
pull requests, pixi environments, continuous integration with GitHub Actions,
and a team analysis where up to ten participants each write one function of a
Breit–Wigner fit to a mystery resonance, each through a CI-checked, reviewed
pull request. Part II covers Geometry,
the geometry and field services, the data model, `aegir`, `sea-cucumber` and
`Shannon`, followed through one guiding example, an HNL decaying to πμ from
EventCalc. Reconstruction (`Trout`) is covered as an outlook for the closing
discussion.

## Build

```bash
make              # participant edition  -> booklet.pdf
make organiser    # organiser edition    -> booklet-organiser.pdf (adds solutions and tutor notes)
make all          # both
make check        # list the [TBD] items still to fill in
make tectonic     # build both with tectonic instead of latexmk
make participant-archive  # the archive to hand out: no solutions, generator, tests or organiser edition
```

Any TeX Live with KOMA-Script, tcolorbox, listings and TikZ works
(pdflatex, lualatex, xelatex or tectonic).

## Layout

| Path | Content |
|------|---------|
| `booklet.tex` | master file: metadata (title, date, authors) and chapter order |
| `booklet-organiser.tex` | the same booklet with solutions and organiser notes |
| `shipbooklet.sty` | layout, accessible blue/neutral colours, boxes, code listings |
| `chapters/` | one file per chapter and appendix |
| `code/workflows/` | Phlex workflows: `hnl_sim.jsonnet` (aegir), `hnl_digi.jsonnet` (Shannon) |
| `code/analysis/` | Python analysis scripts read by participants; `solutions/` for the optional exercises |
| `code/eventcalc/` | the EventCalc launch card for the sample |
| `chapters/p1-*.tex` | Part I, in order: git basics, branches, remotes and pull requests, pixi, CI, team analysis |
| `code/ci/playground-ci.yml` | the first CI workflow participants set up for their own pixi playground |
| `code/teamwork/template/` | initial content of the team repository: 10-task skeleton `mystery_analysis.py`, per-task checker `check_task.py`, `pixi.toml`, `ruff.toml`, `.github/workflows/ci.yml`, `README.md`, `CONTRIBUTING.md`, `.gitignore`, `.gitattributes` (organisers add `pixi.lock` with one `pixi install`) |
| `code/teamwork/organiser/` | **do not distribute**: `make_mystery_sample.py` (hidden-parameter generator) and `solutions.py` (reference implementation) |

Workflow files and selected code excerpts are included directly with `\codefile`.
The full executable scripts are in the archive. Set `$CODE` to its `code/`
directory as shown in the preface; no unpublished tutorials repository is required.

## Writing conventions

- Boxes: `exercise`, `checkpoint`, `note`, `pitfall`; organiser-only
  `solution` and `organisernote` (dropped from the participant edition).
- `\tbd{...}` marks anything still to decide; it prints as a labelled, dark-brown item in both
  editions and `make check` lists it.
- Data-model member names follow `shipdatamodel` 0.5 (camelCase), which
  `aegir` and `Shannon` are built against; appendix B maps them to the
  snake_case names of 0.6.

## Reviewed edition (15 October 2026)

Author: M.Climescu (matclim@cern.ch). The LaTeX date is `\today`.
The supplied SHiP logo is in `figures/SHiP-Acronym_Black.png`.

Read `REVIEW.md`, appendix D and `reviewed_sources.json` for the source audit,
remaining prerequisites and verification limits. A data-model 0.5 environment
is required for these scripts. Current development heads are not jointly
compatible: do not treat the reviewed commit list as an environment lock.

No simulation input ROOT file, converter, maps or integrated environment is
bundled. The analysis demonstrates interfaces, with longitudinal-only
containment and broad sensitive-volume selection; it is not a physics
performance result. Run `make check` to list outstanding organiser inputs.

`python tests/test_analysis_helpers.py` checks pure numerical and selection
logic without pretending to exercise ROOT I/O or Geant4.

`bash tests/test_git_workflow.sh` runs every git command sequence of Part I
against local bare repositories (forks, rebase onto an updated main, a
conflict, a rebase-only merge queue).

`python tests/test_teamwork.py` runs the team exercise end to end (generator,
empty skeleton, per-task checker, partial merges, reference solutions) against
a numpy/scipy stand-in for PyROOT in `tests/fakeroot/`. It checks control flow,
contracts and fit numerics, not the real ROOT calls: do the organiser dry run in
the team-analysis chapter with real ROOT before the session. If `pixi`,
`ruff` and `actionlint` are on the PATH (or in the environment variables `PIXI`,
`RUFF`, `ACTIONLINT`), it also checks the team repository's manifest and tasks,
lints the template and the fully solved skeleton as CI would, and validates
both GitHub Actions workflows.
