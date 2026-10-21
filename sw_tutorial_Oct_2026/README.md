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
`Shannon`, followed through one guiding example produced from scratch: the
muons from 400 GeV protons on the SHiP target: a fixed-target production of
1000 protons to a scoring plane behind the hadron absorber, then an
artificial sample of 100 muons fired from the back of the muon shield
(z = 27 m) through the detectors, digitised, displayed and analysed. Reconstruction (`Trout`) is covered as an outlook for the closing
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
| `code/workflows/` | Phlex workflows: `ft_production.jsonnet` (aegir stage 1), `muon_gun.jsonnet` (artificial muons through the detectors), `ft_replay.jsonnet` (optional replay of stage 1), `ft_digi.jsonnet` (Shannon) |
| `code/analysis/` | Python analysis scripts read by participants (data model 0.6): `first_sim.py` and `first_digi.py` (starting points for their own analysis of aegir and Shannon files), `plane_summary.py`, `muon_background.py`, `sim_summary.py`, `digi_residuals.py`, helpers in `shipfiles.py`; `solutions/` for the optional exercises |
| `chapters/p1-*.tex` | Part I, in order: git basics, branches, remotes and pull requests, pixi, CI, team analysis |
| `code/ci/playground-ci.yml` | the first CI workflow participants set up for their own pixi playground |
| `code/teamwork/template/` | initial content of the team repository: 10-task skeleton `mystery_analysis.py`, per-task checker `check_task.py`, `pixi.toml`, `ruff.toml`, `.github/workflows/ci.yml`, `README.md`, `CONTRIBUTING.md`, `.gitignore`, `.gitattributes` (organisers add `pixi.lock` with one `pixi lock`) |
| `code/teamwork/organiser/` | **do not distribute**: `make_mystery_sample.py` (hidden-parameter generator) and `solutions.py` (reference implementation) |
| `code/geometry/` | geometry chapter workspace: `calo_plane/build_calo_plane.cpp` (one calorimeter plane in plain GeoModel), `viewer/ship_g4view.cpp` (Geant4 viewer for any `.db` file, through the SHiP geometry service, with the macro command `/ship/geometry/open`), the macros `vis.mac`, `calo_plane.mac`, `check_plane.mac`, `picture.mac`, `ship.mac`, and `pixi.toml` (organisers add `pixi.lock` with one `pixi lock`) |
| `code/geometry/organiser/` | **do not distribute**: `build_calo_module.cpp`, solution of the vertical-bar and lead-plate exercises |

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

`bash tools/dry_run.sh [--pot N] [--maps DIR] [--keep-going]` (organisers, on
lxplus) runs Part II end to end with `pixi cvmfs`: clones and builds the
packages, runs the geometry workspace, both simulation stages, a
reproducibility check, digitisation, the display's batch tools and the
analysis, and writes timings, disk use and the analysis tables to
`report/summary.txt`. It is not in the participant archive.

`python tests/test_analysis_helpers.py` runs the analysis scripts on
synthetic events with the data-model 0.6 member names and a stand-in for ROOT,
and fails on any camelCase (0.5) member name.

`python tests/test_workflows.py` evaluates the four Phlex workflows with
`jsonnet` (on the PATH or in `JSONNET`). With `AEGIR` pointing at an aegir
checkout it checks that stage 1 is the same job as aegir's
`fixed_target_production.jsonnet` and stage 2 differs from `plane_replay.jsonnet`
only by the detectors, the field and energy-deposit hits, and that the muon
gun uses the same detectors and field as the replay; with `GEOMETRY`
pointing at a Geometry checkout it checks every volume pattern against its
sources.

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

`python tests/test_booklet_rules.py` enforces three rules over the whole
booklet: no command shown writes a file with `echo`, `printf`, `cat` or a
here-document; everything runs on lxplus with pixi from CVMFS (no
`pixi run`, `pixi shell`, `pixi install`, or `pixi add` without
`--no-install` in the listings and participant READMEs, since they install
into `.pixi/` on AFS); and the geometry viewer is the SHiP one, not the
GeoModel explorer.

`python tests/test_geometry.py` checks the geometry chapter without GeoModel
or Geant4: that every printed excerpt of `code/geometry` still starts and ends
where the text expects, that the code fits the printed width, that the pixi
tasks and macros refer to files and volume names that exist, and that the
numbers in the solutions follow from the dimensions. The C++ itself has been
syntax-checked against the Geant4 11.4.2 headers but not compiled against
GeoModel; build and run the workspace once before the session.
