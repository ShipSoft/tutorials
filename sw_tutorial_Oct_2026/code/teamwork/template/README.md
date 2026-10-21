# The mystery resonance

A team analysis for the SHiP software tutorial. `mystery.root` holds 20 000
measured masses of an unknown particle, which decays with a Breit–Wigner line
shape. Together, find its mass and width, and say what it is.

The analysis lives in one file, `mystery_analysis.py`, split into ten tasks.
Each task is one function with one owner. Every function lists its **Input**,
its **Output** and the **Relevant** ROOT calls in the comment above it.

| Task | Function | What it does | Owner | Reviewer |
|-----:|----------|--------------|-------|----------|
| 1 | `open_file` | open the RNTuple in `mystery.root` | | owner of 2 |
| 2 | `read_masses` | read the `mass` field into a list | | owner of 3 |
| 3 | `summarise` | count, mean, median, central 68% interval | | owner of 4 |
| 4 | `book_histogram` | choose range and binning, book `h_mystery` | | owner of 5 |
| 5 | `fill_histogram` | fill `h_mystery`, report under/overflow | | owner of 6 |
| 6 | `make_model` | Breit–Wigner `f_func` with starting values | | owner of 7 |
| 7 | `fit_model` | fit `f_func` to `h_mystery` | | owner of 8 |
| 8 | `extract_results` | mass, width, errors, fit quality | | owner of 9 |
| 9 | `identify_particle` | compare with known particles | | owner of 10 |
| 10 | `save_plot` | draw data and fit, save `mystery_fit.pdf` | | owner of 1 |

Your reviewer is the person who uses what your function returns.

## Getting started

You need an lxplus account with an SSH key known to GitHub, and pixi from
CVMFS, which provides Python and ROOT, the same versions for everybody and
for CI, without filling your AFS quota. Once, add this line to your
`~/.bashrc` (open it in your editor) and open a new shell:

```bash
export PATH=/cvmfs/ship-nightlies.cern.ch/pixi/0.72.0-rattlerfs-layers-d5a7568/bin:$PATH
```

Use `pixi cvmfs <task>`; never `pixi run`, `pixi shell` or `pixi install`
on lxplus, which install the environment into `.pixi/` on AFS.

```bash
# 1. fork this repository on GitHub, then clone YOUR fork
git clone git@github.com:<you>/sw_tutorial_2026.git
cd sw_tutorial_2026
git remote add upstream git@github.com:matclim/sw_tutorial_2026.git
cp <wherever-it-is>/mystery.root . # data: not under version control

# 2. one branch for your task
git switch -c task-04-book-histogram

# 3. write your function, then test it on its own
pixi cvmfs check-task 4
pixi cvmfs lint

# 4. commit, push to your fork, open a pull request
git add mystery_analysis.py README.md
git commit -m "feat(task-04): book the mystery histogram"
git push -u origin task-04-book-histogram
```

| Command | What it does |
|---------|--------------|
| `pixi cvmfs analysis` | run every task that has been merged so far |
| `pixi cvmfs check-task N` | test task N on its own, with a toy sample |
| `pixi cvmfs check` | test every task (what CI runs) |
| `pixi cvmfs lint` | static checks of the Python code (what CI runs) |

Every pull request is checked by CI (`.github/workflows/ci.yml`); it can be
merged when "All checks passed" is green and your reviewer has approved.
See `CONTRIBUTING.md` for the rules of the game.
