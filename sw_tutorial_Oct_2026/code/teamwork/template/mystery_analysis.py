#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""The mystery resonance: an analysis written by a team of courageous folks.

The file mystery.root holds one RNTuple, "events", with a single field,
"mass": the invariant mass, in GeV, of the decay products of an unknown
particle. Its line shape is a Breit-Wigner. Your team's job is to find out
its mass and width, and which particle it is.

The analysis is split into ten tasks. Each task is one function below, owned
by one person, and starts out empty. Every function says what it receives
(Input), what it must give back (Output), and which ROOT calls are useful
(Relevant). Write your code between the "your code" markers of YOUR function
only; do not change the function's name or arguments, because your teammates'
functions call it.

    pixi cvmfs analysis                        # run the whole chain
    pixi cvmfs check-task 4                    # test task 4 on its own
    pixi cvmfs check                           # test every task

The chain runs from task 1 and stops, politely, at the first task that is not
written yet. Every merged pull request lets it run further.
"""

import argparse
import os
import sys

import ROOT

ROOT.gROOT.SetBatch(True)  # no windows: everything goes to files

# ---------------------------------------------------------------------------
# Shared settings. Owned by the organisers; change them only in a pull
# request of their own, never inside a task.
# ---------------------------------------------------------------------------
INPUT_FILE = "mystery.root"
NTUPLE_NAME = "events"
FIELD_NAME = "mass"
OUTPUT_PDF = "mystery_fit.pdf"

# Known resonances: name -> (mass, width), both in GeV. Approximate values
# from the Review of Particle Physics (https://pdg.lbl.gov). Used by task 9.
CANDIDATES = {
    # Sharp and well known, also surprisingly deadly
    "J/psi(1S)": (3.0969, 0.0000926),
    # The little brother of a flavour physicist's best friend
    "Upsilon(1S)": (9.4603, 0.0000540),
    # a Nambu-Goldstone boson, given mass
    "W boson": (80.37, 2.09),
    # It is beauty, it is grace, if you call it a heavy photon, it will kick you in the face
    "Z boson": (91.19, 2.50),
    # Only if SM model-like! Rendez vous in FCC to figure out if this is true
    "Higgs boson": (125.2, 0.0037),
}

# Note: google is your best friend

# ===========================================================================
# TASK 1 -- Open the file                                   owner: __________
# ---------------------------------------------------------------------------
# Input:    path         (str)  name of the ROOT file, e.g. "mystery.root"
#           ntuple_name  (str)  name of the RNTuple inside it, "events"
# Output:   reader       (ROOT.RNTupleReader) opened on that RNTuple
# Relevant: ROOT.RNTupleReader.Open(ntuple_name, path)
#           reader.GetNEntries()   number of entries (one entry = one decay)
#           reader.PrintInfo()     prints the fields and their C++ types
# Hints:    Print the number of entries: your teammates will want it.
#           ROOT's error for a missing file is cryptic: check
#           os.path.exists(path) first and raise FileNotFoundError with a
#           message that names the file.
# Check:    pixi cvmfs check-task 1
# ===========================================================================
def open_file(path, ntuple_name=NTUPLE_NAME):
    # ---- TASK 1: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 1: open_file")
    # ---- TASK 1: your code above -------------------------------------------


# ===========================================================================
# TASK 2 -- Read the masses                                 owner: __________
# ---------------------------------------------------------------------------
# Input:    reader       (ROOT.RNTupleReader) from task 1
#           field_name   (str)  name of the field to read, "mass"
# Output:   masses       (list of float) one value per entry, in GeV
# Relevant: view = reader.GetView["float"](field_name)  a typed "view"
#           view(i)      the value of entry i (a Python float)
#           range(reader.GetNEntries())
# Hints:    A list comprehension does it in one line. Convert each value
#           with float(...) so that later tasks get plain Python numbers.
# Check:    pixi cvmfs check-task 2
# ===========================================================================
def read_masses(reader, field_name=FIELD_NAME):
    # ---- TASK 2: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 2: read_masses")
    # ---- TASK 2: your code above -------------------------------------------


# ===========================================================================
# TASK 3 -- Summarise the sample                            owner: __________
# ---------------------------------------------------------------------------
# Input:    masses       (list of float) from task 2
# Output:   stats        (dict) with exactly these keys, all numbers:
#             "n"       number of values
#             "min"     smallest value        "max"    largest value
#             "mean"    arithmetic mean       "median" the 50% quantile
#             "lo68"    the 16% quantile      "hi68"   the 84% quantile
#           i.e. [lo68, hi68] holds the central 68% of the values.
# Relevant: s = sorted(masses); len(s); sum(s); min(s); max(s)
#           a q-quantile of a sorted list s is about s[int(q * (len(s) - 1))]
# Hints:    Print the dictionary. Compare the mean with the median: why are
#           they different? A Breit-Wigner has very long tails, so its mean
#           and RMS are pulled around by a few far-away values, while
#           quantiles are not. Task 4 relies on the quantiles.
# Check:    pixi cvmfs check-task 3
# ===========================================================================
def summarise(masses):
    # ---- TASK 3: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 3: summarise")
    # ---- TASK 3: your code above -------------------------------------------


# ===========================================================================
# TASK 4 -- Book the histogram                              owner: __________
# ---------------------------------------------------------------------------
# Input:    stats        (dict) from task 3
# Output:   h_mystery    (ROOT.TH1F) EMPTY histogram, named "h_mystery",
#                        with a title and both axis titles set
# Relevant: ROOT.TH1F(name, "title;x-axis title;y-axis title", nbins, lo, hi)
# Hints:    Choose lo and hi from the statistics, not by looking at the
#           data by eye: centre the range on the median and make it several
#           times wider than the central 68% interval, so that the tails are
#           visible. Choose the number of bins so that several bins fall
#           inside the central 68% interval (the bin width should be a
#           fraction of the width of the peak). The y-axis title should give
#           the bin width, e.g. "Events / 0.5 GeV" (use an f-string).
# Check:    pixi cvmfs check-task 4
# ===========================================================================
def book_histogram(stats):
    # ---- TASK 4: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 4: book_histogram")
    # ---- TASK 4: your code above -------------------------------------------


# ===========================================================================
# TASK 5 -- Fill the histogram                              owner: __________
# ---------------------------------------------------------------------------
# Input:    h_mystery    (ROOT.TH1F) empty histogram from task 4
#           masses       (list of float) from task 2
# Output:   h_mystery    the same histogram, now filled (return it)
# Relevant: h.Fill(x)                  adds one entry
#           h.GetEntries()             number of Fill calls so far
#           h.GetBinContent(0)         underflow (below the range)
#           h.GetBinContent(h.GetNbinsX() + 1)   overflow (above the range)
# Hints:    Print how many values fell below and above the histogram range.
#           If it is more than a few percent, tell the owner of task 4.
# Check:    pixi cvmfs check-task 5
# ===========================================================================
def fill_histogram(h_mystery, masses):
    # ---- TASK 5: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 5: fill_histogram")
    # ---- TASK 5: your code above -------------------------------------------


# ===========================================================================
# TASK 6 -- Build the fit model                             owner: __________
# ---------------------------------------------------------------------------
# Input:    h_mystery    (ROOT.TH1F) filled histogram from task 5
# Output:   f_func       (ROOT.TF1) named "f_func", NOT yet fitted, with
#                        parameter 0 = normalisation, 1 = mass, 2 = width,
#                        defined over the histogram's x range, and with
#                        sensible starting values for all three parameters
# Relevant: ROOT.TF1("f_func", "[0]*TMath::BreitWigner(x, [1], [2])", lo, hi)
#           f.SetParameters(p0, p1, p2);  f.SetParNames("N", "M", "#Gamma")
#           h.GetXaxis().GetXmin(), h.GetXaxis().GetXmax()
#           h.GetMaximumBin(), h.GetBinCenter(i), h.GetBinWidth(1)
#           h.Integral()          sum of the bin contents inside the range
#           h.FindFirstBinAbove(y), h.FindLastBinAbove(y)
# Hints:    TMath::BreitWigner(x, M, Gamma) is normalised to unit area, so the
#           expected content of a bin is (number of entries) x (bin width) x
#           BW(x). The peak position is a good start for M; the full width at
#           half maximum (FWHM) of the peak is exactly Gamma for a
#           Breit-Wigner. A fit started far from the answer may not find it.
# Check:    pixi cvmfs check-task 6
# ===========================================================================
def make_model(h_mystery):
    # ---- TASK 6: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 6: make_model")
    # ---- TASK 6: your code above -------------------------------------------


# ===========================================================================
# TASK 7 -- Fit                                             owner: __________
# ---------------------------------------------------------------------------
# Input:    h_mystery    (ROOT.TH1F) filled histogram from task 5
#           f_func       (ROOT.TF1) model with starting values from task 6
# Output:   fit_result   (the object returned by h.Fit(..., "S")); after the
#                        call, f_func holds the fitted parameters
# Relevant: h.Fit("gaus")              fits a built-in Gaussian
#           h.Fit(f_func, options)     fits your own TF1; useful options:
#             "S" return the fit result   "L" Poisson likelihood (counts!)
#             "R" use the TF1's range     "Q" quiet   "0" do not draw
#           fit_result.Status()        0 means the fit converged
#           fit_result.Print("V")      parameters, errors, correlations
# Hints:    Which option is right for a histogram of counts, chi-square or
#           likelihood? Try both and compare. If Status() is not 0, raise a
#           RuntimeError: a failed fit must not produce a number.
# Check:    pixi cvmfs check-task 7
# ===========================================================================
def fit_model(h_mystery, f_func):
    # ---- TASK 7: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 7: fit_model")
    # ---- TASK 7: your code above -------------------------------------------


# ===========================================================================
# TASK 8 -- Extract the results                             owner: __________
# ---------------------------------------------------------------------------
# Input:    f_func       (ROOT.TF1) fitted model from task 7
#           fit_result   from task 7
# Output:   results      (dict) with exactly these keys, all numbers:
#             "mass", "mass_err"     fitted mass and its error   [GeV]
#             "width", "width_err"   fitted width and its error  [GeV]
#             "chi2", "ndf", "prob"  goodness of fit
# Relevant: f.GetParameter(i), f.GetParError(i)
#           f.GetChisquare(), f.GetNDF(), f.GetProb()
#           fit_result.Chi2(), fit_result.Ndf(), fit_result.Prob()
# Hints:    The width parameter can come out negative: the Breit-Wigner only
#           depends on Gamma squared. Report its absolute value. Print the
#           results with a sensible number of digits (look at the errors).
# Check:    pixi cvmfs check-task 8
# ===========================================================================
def extract_results(f_func, fit_result):
    # ---- TASK 8: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 8: extract_results")
    # ---- TASK 8: your code above -------------------------------------------


# ===========================================================================
# TASK 9 -- Identify the particle                           owner: __________
# ---------------------------------------------------------------------------
# Input:    results      (dict) from task 8
#           candidates   (dict) name -> (mass, width) in GeV, see CANDIDATES
# Output:   (name, pull) (tuple: str, float) the best-matching candidate and
#                        its mass pull = (fitted mass - candidate mass)
#                                        / (error of the fitted mass)
# Relevant: candidates.items(), abs(), min(..., key=...)
# Hints:    Print a small table: every candidate with its mass pull and the
#           difference between its width and the fitted one. Is the best
#           match also compatible in width? A pull of a few units is fine
#           here (the reference values are rounded); hundreds are not.
# Check:    pixi cvmfs check-task 9
# ===========================================================================
def identify_particle(results, candidates=CANDIDATES):
    # ---- TASK 9: your code below (delete the "raise" line) ----------------
    raise NotImplementedError("task 9: identify_particle")
    # ---- TASK 9: your code above -------------------------------------------


# ===========================================================================
# TASK 10 -- Draw and save the plot                         owner: __________
# ---------------------------------------------------------------------------
# Input:    h_mystery    (ROOT.TH1F) filled histogram from task 5
#           f_func       (ROOT.TF1) fitted model from task 7
#           results      (dict) from task 8
#           path         (str)  output file name, e.g. "mystery_fit.pdf"
# Output:   path         (str)  the file written; it must exist afterwards
# Relevant: c = ROOT.TCanvas("c", "c", 800, 600)
#           h.Draw("E")                  data points with error bars
#           f.Draw("SAME")               the fitted curve on top
#           leg = ROOT.TLegend(x1, y1, x2, y2); leg.AddEntry(obj, "text", "lep")
#           ROOT.TLatex().DrawLatexNDC(x, y, "M = ... GeV")
#           c.SaveAs(path)
# Hints:    Keep the canvas, legend and text in local variables until after
#           SaveAs, otherwise Python may delete them too early. A
#           logarithmic y axis (c.SetLogy()) shows the tails. Write mass and
#           width with their errors on the plot.
# Check:    pixi cvmfs check-task 10
# ===========================================================================
def save_plot(h_mystery, f_func, results, path=OUTPUT_PDF):
    # ---- TASK 10: your code below (delete the "raise" line) ---------------
    raise NotImplementedError("task 10: save_plot")
    # ---- TASK 10: your code above ------------------------------------------


# ===========================================================================
# Putting it together. Owned by the organisers: do not edit in a task PR.
# ===========================================================================
def run_pipeline(impl, input_file=INPUT_FILE, output_pdf=OUTPUT_PDF):
    """Run the ten tasks in order; stop at the first one not written yet.

    `impl` is the module that provides the task functions (normally this
    file). Returns (number of tasks completed, dict of their outputs).
    """
    data = {}
    steps = [
        ("open_file", lambda: impl.open_file(input_file)),
        ("read_masses", lambda: impl.read_masses(data["open_file"])),
        ("summarise", lambda: impl.summarise(data["read_masses"])),
        ("book_histogram", lambda: impl.book_histogram(data["summarise"])),
        ("fill_histogram", lambda: impl.fill_histogram(data["book_histogram"],
                                                       data["read_masses"])),
        ("make_model", lambda: impl.make_model(data["fill_histogram"])),
        ("fit_model", lambda: impl.fit_model(data["fill_histogram"], data["make_model"])),
        ("extract_results", lambda: impl.extract_results(data["make_model"],
                                                         data["fit_model"])),
        ("identify_particle", lambda: impl.identify_particle(data["extract_results"])),
        ("save_plot", lambda: impl.save_plot(data["fill_histogram"], data["make_model"],
                                             data["extract_results"], output_pdf)),
    ]
    for number, (name, step) in enumerate(steps, start=1):
        print(f"--- task {number:2d}/10: {name}")
        try:
            data[name] = step()
        except NotImplementedError:
            print(f"--- task {number:2d}/10: {name} is not written yet; "
                  f"the chain stops here ({number - 1} of 10 tasks done)")
            return number - 1, data
        if data[name] is None:
            raise RuntimeError(f"task {number} ({name}) returned None; "
                               f"see its 'Output' line")
    print(f"--- all 10 tasks done: the plot is in {output_pdf}")
    return 10, data


def finish(status=0):
    """Exit without Python tearing down ROOT objects (avoids rare crashes)."""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=INPUT_FILE, help="the data file")
    parser.add_argument("--output", default=OUTPUT_PDF, help="the plot to write")
    args = parser.parse_args()
    run_pipeline(sys.modules[__name__], args.input, args.output)


if __name__ == "__main__":
    main()
    finish()
