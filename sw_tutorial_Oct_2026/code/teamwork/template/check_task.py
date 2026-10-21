#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Test one task of mystery_analysis.py on its own.

Every task is tested with inputs made up here, from a toy Breit-Wigner sample
whose answer is known (M = 50 GeV, Gamma = 4 GeV -- not the mystery particle).
So you can test your task before your teammates have written theirs.

    pixi cvmfs check-task 4         # test task 4  (= python check_task.py 4)
    pixi cvmfs check                # test every task, as CI does

Exit status 0 means every requested task passed. Run it before you open your
pull request, and paste its output into the pull-request description.
"""

import argparse
import importlib
import math
import os
import random
import sys
import tempfile
import traceback

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)  # histograms belong to Python, not to a ROOT file

TOY_MASS = 50.0      # GeV
TOY_WIDTH = 4.0      # GeV
TOY_WINDOW = (20.0, 80.0)
TOY_EVENTS = 20000

# Writes a toy RNTuple with one float field; used to test tasks 1 and 2.
_WRITER = r"""
#include <ROOT/RNTupleModel.hxx>
#include <ROOT/RNTupleWriter.hxx>
#include <RVersion.h>
#include <memory>
#include <string>
#include <vector>
namespace check_task_io {
#if ROOT_VERSION_CODE >= ROOT_VERSION(6, 36, 0)
namespace rnt = ROOT;
#else
namespace rnt = ROOT::Experimental;
#endif
inline void write(const std::string& path, const std::string& ntuple,
                  const std::string& field, const std::vector<double>& values) {
  auto model = rnt::RNTupleModel::Create();
  auto value = model->MakeField<float>(field);
  auto writer = rnt::RNTupleWriter::Recreate(std::move(model), ntuple, path);
  for (double v : values) {
    *value = static_cast<float>(v);
    writer->Fill();
  }
}
}  // namespace check_task_io
"""


class CheckFailed(Exception):
    """A requirement of the task's Output line is not met."""


def require(condition, message):
    if not condition:
        raise CheckFailed(message)


def note(message):
    print(f"      note: {message}")


# ---------------------------------------------------------------------------
# Reference inputs, made up here
# ---------------------------------------------------------------------------
def toy_masses(n=TOY_EVENTS, seed=1):
    """Breit-Wigner values inside TOY_WINDOW, by inverting the cumulative."""
    rng = random.Random(seed)
    lo, hi = TOY_WINDOW
    values = []
    while len(values) < n:
        x = TOY_MASS + 0.5 * TOY_WIDTH * math.tan(math.pi * (rng.random() - 0.5))
        if lo <= x < hi:
            values.append(x)
    return values


def quantile(sorted_values, q):
    return sorted_values[int(q * (len(sorted_values) - 1))]


def reference_stats(values):
    s = sorted(values)
    return {"n": len(s), "min": s[0], "max": s[-1], "mean": sum(s) / len(s),
            "median": quantile(s, 0.5), "lo68": quantile(s, 0.16),
            "hi68": quantile(s, 0.84)}


def reference_histogram(values, name="h_mystery"):
    h = ROOT.TH1F(name, "toy;m [GeV];Events / 0.25 GeV", 160, 30.0, 70.0)
    for x in values:
        h.Fill(x)
    return h


def reference_model(h, name="f_func"):
    lo, hi = h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax()
    f = ROOT.TF1(name, "[0]*TMath::BreitWigner(x, [1], [2])", lo, hi)
    f.SetParameters(h.Integral() * h.GetBinWidth(1),
                    h.GetBinCenter(h.GetMaximumBin()), 3.0)
    return f


def reference_fit(h, f):
    result = h.Fit(f, "SLRQ0")
    require(result.Status() == 0, "internal error: the reference fit failed")
    return result


def reference_results(f, result):
    return {"mass": f.GetParameter(1), "mass_err": f.GetParError(1),
            "width": abs(f.GetParameter(2)), "width_err": f.GetParError(2),
            "chi2": result.Chi2(), "ndf": result.Ndf(), "prob": result.Prob()}


def close(a, b, tolerance):
    return abs(a - b) <= tolerance


def open_reader(path, ntuple):
    reader_class = getattr(ROOT, "RNTupleReader", None) or ROOT.Experimental.RNTupleReader
    return reader_class.Open(ntuple, path)


# ---------------------------------------------------------------------------
# One check per task
# ---------------------------------------------------------------------------
_keep = []  # readers must outlive their views


def check_1(mod, tmp):
    ROOT.gInterpreter.Declare(_WRITER)
    values = toy_masses(1000)
    path = os.path.join(tmp, "toy.root")
    ROOT.check_task_io.write(path, "events", "mass", ROOT.std.vector["double"](values))
    reader = mod.open_file(path, "events")
    _keep.append(reader)
    require(reader is not None, "open_file returned None; return the reader")
    require(hasattr(reader, "GetNEntries"),
            f"open_file must return an RNTupleReader, got {type(reader).__name__}")
    require(int(reader.GetNEntries()) == len(values),
            f"the reader sees {reader.GetNEntries()} entries, the file has {len(values)}")
    try:
        mod.open_file(os.path.join(tmp, "no_such_file.root"), "events")
        note("a missing file did not raise an error")
    except FileNotFoundError:
        pass
    except Exception as error:  # noqa: BLE001 -- report, do not fail
        note(f"a missing file raised {type(error).__name__}; FileNotFoundError is clearer")


def check_2(mod, tmp):
    ROOT.gInterpreter.Declare(_WRITER)
    values = toy_masses(1000, seed=2)
    path = os.path.join(tmp, "toy.root")
    ROOT.check_task_io.write(path, "events", "mass", ROOT.std.vector["double"](values))
    reader = open_reader(path, "events")
    _keep.append(reader)
    masses = mod.read_masses(reader, "mass")
    require(isinstance(masses, list),
            f"read_masses must return a list, got {type(masses).__name__}")
    require(len(masses) == len(values), f"got {len(masses)} values, the file has {len(values)}")
    require(all(isinstance(x, float) for x in masses),
            "every value must be a Python float; convert with float(...)")
    worst = max(abs(a - b) for a, b in zip(masses, values))
    require(worst < 1e-3, f"values differ from the file by up to {worst:.3g} GeV; "
                          "are they read in entry order?")


def check_3(mod, tmp):
    values = toy_masses()
    ref = reference_stats(values)
    stats = mod.summarise(values)
    require(isinstance(stats, dict), f"summarise must return a dict, got {type(stats).__name__}")
    missing = set(ref) - set(stats)
    require(not missing, f"missing keys: {sorted(missing)}")
    extra = set(stats) - set(ref)
    if extra:
        note(f"extra keys are fine but unused: {sorted(extra)}")
    require(stats["n"] == ref["n"], f"n = {stats['n']}, expected {ref['n']}")
    for key in ("min", "max", "mean"):
        require(close(stats[key], ref[key], 1e-6), f"{key} = {stats[key]}, expected {ref[key]:.4f}")
    for key in ("median", "lo68", "hi68"):
        require(close(stats[key], ref[key], 0.05),
                f"{key} = {stats[key]:.4f}, expected about {ref[key]:.4f}")
    require(stats["lo68"] < stats["median"] < stats["hi68"],
            "the quantiles must satisfy lo68 < median < hi68")


def check_4(mod, tmp):
    ref = reference_stats(toy_masses())
    h = mod.book_histogram(ref)
    require(isinstance(h, ROOT.TH1), f"book_histogram must return a TH1F, got {type(h).__name__}")
    if not isinstance(h, ROOT.TH1F):
        note(f"a {h.ClassName()} works too, but the task asks for a TH1F")
    require(h.GetName() == "h_mystery",
            f"the histogram must be named 'h_mystery', got '{h.GetName()}'")
    require(h.GetEntries() == 0, "the histogram must come back empty (task 5 fills it)")
    lo, hi = h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax()
    core = ref["hi68"] - ref["lo68"]
    require(lo < ref["lo68"] and hi > ref["hi68"],
            f"the range [{lo:g}, {hi:g}] must contain the central 68% "
            f"[{ref['lo68']:.2f}, {ref['hi68']:.2f}]")
    require(hi - lo >= 3 * core, f"the range is only {(hi - lo) / core:.1f} times the central "
                                 "68% interval; make it several times wider to show the tails")
    require(h.GetBinWidth(1) <= core / 4,
            f"bins of {h.GetBinWidth(1):g} GeV are too coarse: fewer than 4 fit in the "
            f"central 68% interval ({core:.2f} GeV)")
    require(h.GetNbinsX() <= 2000, f"{h.GetNbinsX()} bins is far too many")
    require(h.GetXaxis().GetTitle() and h.GetYaxis().GetTitle(),
            "set both axis titles: ROOT.TH1F(name, 'title;x title;y title', ...)")


def check_5(mod, tmp):
    values = toy_masses()
    h = ROOT.TH1F("h_mystery", "toy;m [GeV];Events", 120, 20.0, 80.0)
    out = mod.fill_histogram(h, values)
    require(out is not None, "fill_histogram must return the histogram")
    require(out.GetEntries() == len(values),
            f"the histogram has {out.GetEntries():.0f} entries, there are {len(values)} values")
    ref = ROOT.TH1F("h_ref", "", 120, 20.0, 80.0)
    for x in values:
        ref.Fill(x)
    differing = [i for i in range(0, ref.GetNbinsX() + 2)
                 if out.GetBinContent(i) != ref.GetBinContent(i)]
    require(not differing, f"{len(differing)} bins differ from filling each value once "
                           f"(first: bin {differing[0] if differing else ''})")


def check_6(mod, tmp):
    h = reference_histogram(toy_masses())
    f = mod.make_model(h)
    require(isinstance(f, ROOT.TF1), f"make_model must return a TF1, got {type(f).__name__}")
    require(f.GetName() == "f_func", f"the function must be named 'f_func', got '{f.GetName()}'")
    require(f.GetNpar() >= 3, f"the model needs 3 parameters, it has {f.GetNpar()}")
    if f.GetNpar() > 3:
        note("parameters beyond the third are allowed (e.g. a background)")
    width = h.GetBinWidth(1)
    require(f.GetXmin() <= h.GetXaxis().GetXmin() + width
            and f.GetXmax() >= h.GetXaxis().GetXmax() - width,
            f"the TF1 range [{f.GetXmin():g}, {f.GetXmax():g}] should be the histogram's")
    norm, mass, gamma = (f.GetParameter(i) for i in range(3))
    require(norm > 0, f"start value of the normalisation is {norm:g}; it must be positive")
    require(abs(mass - TOY_MASS) < TOY_WIDTH,
            f"start value of M is {mass:g}; the toy peak is at {TOY_MASS:g}")
    require(0.25 * TOY_WIDTH < abs(gamma) < 4 * TOY_WIDTH,
            f"start value of Gamma is {gamma:g}; the toy width is {TOY_WIDTH:g}")
    ratio = f.Eval(TOY_MASS) / h.GetMaximum()
    require(1 / 3 < ratio < 3, f"at the peak the model is {ratio:.2g} times the data: "
                               "check the normalisation (entries x bin width)")


def check_7(mod, tmp):
    h = reference_histogram(toy_masses())
    f = reference_model(h)
    result = mod.fit_model(h, f)
    require(result is not None, "fit_model must return the fit result: h.Fit(f, 'S...')")
    require(hasattr(result, "Status"),
            "return the object h.Fit(..., 'S') gives back (did you forget the 'S' option?)")
    require(result.Status() == 0, f"the fit did not converge (status {result.Status()})")
    require(close(f.GetParameter(1), TOY_MASS, 0.2),
            f"fitted M = {f.GetParameter(1):.3f}, the toy has {TOY_MASS}; was f_func fitted?")
    require(close(abs(f.GetParameter(2)), TOY_WIDTH, 0.15 * TOY_WIDTH),
            f"fitted Gamma = {f.GetParameter(2):.3f}, the toy has {TOY_WIDTH}")


def check_8(mod, tmp):
    h = reference_histogram(toy_masses())
    f = reference_model(h)
    fit = reference_fit(h, f)
    results = mod.extract_results(f, fit)
    ref = reference_results(f, fit)
    require(isinstance(results, dict),
            f"extract_results must return a dict, got {type(results).__name__}")
    missing = set(ref) - set(results)
    require(not missing, f"missing keys: {sorted(missing)}")
    for key in ("mass", "mass_err", "width", "width_err"):
        require(close(results[key], ref[key], 1e-6 * max(1.0, abs(ref[key]))),
                f"{key} = {results[key]}, expected {ref[key]:.6g}")
    require(close(results["chi2"], ref["chi2"], 1e-6 * ref["chi2"])
            or close(results["chi2"], f.GetChisquare(), 1e-6 * max(1.0, f.GetChisquare())),
            f"chi2 = {results['chi2']}, expected {ref['chi2']:.4g} (or f.GetChisquare())")
    require(int(results["ndf"]) in (ref["ndf"], f.GetNDF()),
            f"ndf = {results['ndf']}, expected {ref['ndf']}")
    require(0.0 <= results["prob"] <= 1.0, f"prob = {results['prob']} is not a probability")


def check_9(mod, tmp):
    cases = [({"mass": 80.40, "mass_err": 0.03, "width": 2.05, "width_err": 0.07},
              "W boson", (80.40 - 80.37) / 0.03),
             ({"mass": 3.100, "mass_err": 0.010, "width": 0.01, "width_err": 0.01},
              "J/psi(1S)", (3.100 - 3.0969) / 0.010)]
    for results, expected, pull in cases:
        for key in ("chi2", "ndf", "prob"):
            results.setdefault(key, 1.0)
        answer = mod.identify_particle(results, mod.CANDIDATES)
        require(isinstance(answer, tuple) and len(answer) == 2,
                f"identify_particle must return (name, pull), got {answer!r}")
        name, got = answer
        require(name == expected, f"for M = {results['mass']} GeV you chose {name!r}, "
                                  f"expected {expected!r}")
        require(close(got, pull, 1e-6 * max(1.0, abs(pull))),
                f"pull = {got:.4g}, expected {pull:.4g} = (fitted - candidate) / error")


def check_10(mod, tmp):
    h = reference_histogram(toy_masses())
    f = reference_model(h)
    fit = reference_fit(h, f)
    path = os.path.join(tmp, "check_plot.pdf")
    out = mod.save_plot(h, f, reference_results(f, fit), path)
    require(out == path, f"save_plot must return the path it wrote, got {out!r}")
    require(os.path.exists(path) and os.path.getsize(path) > 0, f"no plot was written to {path}")
    print(f"      look at the plot yourself: {path} (kept until the next run)")


CHECKS = {i: globals()[f"check_{i}"] for i in range(1, 11)}


def run(task, mod, tmp):
    print(f"task {task:2d}: ", end="", flush=True)
    try:
        CHECKS[task](mod, tmp)
    except NotImplementedError:
        print("not written yet")
        return "todo"
    except CheckFailed as failure:
        print(f"FAILED\n      {failure}")
        return "failed"
    except Exception:  # noqa: BLE001 -- show the participant their traceback
        print("FAILED with an exception:")
        traceback.print_exc()
        return "failed"
    print("passed")
    return "passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("task", help="task number 1-10, or 'all'")
    parser.add_argument("--module", default="mystery_analysis",
                        help="module that provides the task functions")
    args = parser.parse_args()
    tasks = range(1, 11) if args.task == "all" else [int(args.task)]
    sys.path.insert(0, os.getcwd())
    mod = importlib.import_module(args.module)
    tmp = os.path.join(tempfile.gettempdir(), "mystery_checks")
    os.makedirs(tmp, exist_ok=True)
    outcome = [run(t, mod, tmp) for t in tasks]
    if len(outcome) > 1:
        print(f"\n{outcome.count('passed')} passed, {outcome.count('todo')} not written yet, "
              f"{outcome.count('failed')} failed")
    # A task that is not written yet fails a single check, but not 'all':
    # the integrator wants to know that nothing merged is broken.
    bad = outcome.count("failed") + (outcome.count("todo") if len(outcome) == 1 else 0)
    return 1 if bad else 0


if __name__ == "__main__":
    status = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)  # skip Python's teardown of ROOT objects
