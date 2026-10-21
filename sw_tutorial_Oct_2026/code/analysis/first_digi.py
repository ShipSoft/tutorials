#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""A first look at a Shannon file (booklet ch. 10): hits per collection, and
the times and positions of the straw hits.

    cp $CODE/analysis/first_digi.py .
    python first_digi.py ft_digi.root

Copy it to work/ and extend it in the exercises.
"""

import os
import sys

import ROOT

sys.path.append(os.path.join(os.environ.get("CODE", ""), "analysis"))
import shipfiles as sf  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else "ft_digi.root"

# A Shannon file holds one RNTuple per hit collection, with one entry per
# hit (not per event). Every hit type wraps a SHiP::RecHit, `rec_hit`.
COLLECTIONS = {
    "ubt_hits": "SHiP::UBTHit",
    "sbt_hits": "SHiP::SBTHit",
    "straw_tubes_hits": "SHiP::StrawTubesHit",
    "calorimeter_hits": "SHiP::CaloHit",
    "timing_detector_hits": "SHiP::TimeDetHit",
}
readers = {name: ROOT.RNTupleReader.Open(name, path) for name in COLLECTIONS}
for name, reader in readers.items():
    print(f"{name:22} {reader.GetNEntries():7d} hits")

straws = readers["straw_tubes_hits"]
hit = straws.GetView[COLLECTIONS["straw_tubes_hits"]]("hit")
times, xy = [], []
for i in range(straws.GetNEntries()):
    rec = hit(i).rec_hit  # copy out the numbers: the view reuses its buffer
    times.append(rec.time)
    if sf.station_of(rec.position[2]) == 0:
        xy.append((rec.position[0], rec.position[1]))

h_t = ROOT.TH1D("straw_t", "straw hits;t [ns];hits", 100, min(times), max(times) + 1.0)
h_xy = ROOT.TH2D("straw_xy", "straw station 1;x [mm];y [mm]",
                 60, -3000.0, 3000.0, 70, -3500.0, 3500.0)
for t in times:
    h_t.Fill(t)
for x, y in xy:
    h_xy.Fill(x, y)

canvas = ROOT.TCanvas("c", "", 800, 600)
h_t.Draw("hist")
canvas.SaveAs("straw_t.pdf")
h_xy.Draw("colz")
canvas.SaveAs("straw_xy.pdf")
sf.finish()  # leave without PyROOT's teardown, which can crash
