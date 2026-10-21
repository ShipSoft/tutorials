#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""A first look at an aegir file (booklet ch. 10): hits per detector, and
where along the beam the straw hits are.

    cp $CODE/analysis/first_sim.py .
    python first_sim.py muon_gun.root

Copy it to work/ and extend it in the exercises.
"""

import collections
import os
import sys

import ROOT

sys.path.append(os.path.join(os.environ.get("CODE", ""), "analysis"))
import shipfiles as sf  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else "muon_gun.root"

# An aegir file holds one RNTuple, "events", with one entry per event. A view
# reads one field; calling it with an entry number gives that entry's value.
reader = ROOT.RNTupleReader.Open("events", path)
hits = reader.GetView["std::vector<SHiP::SimHit>"]("sim_hits")

per_detector = collections.Counter()
h_z = ROOT.TH1D("straw_z", "straw hits;z [m];hits", 130, 83.0, 96.0)
for i in range(reader.GetNEntries()):
    for h in hits(i):  # the hits of event i
        per_detector[sf.DETECTOR_NAMES.get(h.detector_id, h.detector_id)] += 1
        if h.detector_id == sf.STRAWS:
            h_z.Fill(h.position[2] / 1000.0)

print(f"{path}: {reader.GetNEntries()} events")
for name, n in per_detector.most_common():
    print(f"  {name!s:12} {n:7d} hits")

canvas = ROOT.TCanvas("c", "", 800, 600)
h_z.Draw("hist")
canvas.SaveAs("straw_z.pdf")
sf.finish()  # leave without PyROOT's teardown, which can crash
