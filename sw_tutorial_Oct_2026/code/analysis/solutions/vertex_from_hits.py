#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Solution to the vertexing exercise of booklet chapter 10.

A poor man's vertex: for each daughter, take the mean position of its
simulated straw hits in stations 1 and 2 (upstream of the magnet, so the
track is straight there), extend the line through these two points back into
the decay volume, and take the midpoint of the shortest segment between the
two lines. Compare it with the true decay vertex.

    python solutions/vertex_from_hits.py hnl_sim.root

Run it from code/analysis/ or with that directory on PYTHONPATH (it imports
shipfiles).
"""

import argparse
import collections
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import ROOT  # noqa: E402

import shipfiles as sf  # noqa: E402
from hnl_analysis import truth_decay  # noqa: E402


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def closest_approach(p1, d1, p2, d2):
    """Midpoint and distance of closest approach of lines p1 + t d1, p2 + s d2."""
    w0 = sub(p1, p2)
    a, b, c = dot(d1, d1), dot(d1, d2), dot(d2, d2)
    d, e = dot(d1, w0), dot(d2, w0)
    den = a * c - b * b
    if a == 0 or c == 0 or den <= 1e-12 * a * c:  # parallel
        return None
    t = (b * e - c * d) / den
    s = (a * e - b * d) / den
    q1 = add(p1, scale(d1, t))
    q2 = add(p2, scale(d2, s))
    return scale(add(q1, q2), 0.5), math.sqrt(dot(sub(q1, q2), sub(q1, q2)))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file")
    p.add_argument("--out", default="vertex_from_hits.pdf")
    args = p.parse_args()

    f = sf.EventFile(args.file)
    f.view("mc_particles", "std::vector<SHiP::MCParticle>")
    f.view("sim_particles", "std::vector<SHiP::SimParticle>")
    f.view("sim_hits", "std::vector<SHiP::SimHit>")

    headers = f.view("event_header", "SHiP::EventHeader")
    ROOT.TH1.SetDefaultSumw2(True)
    hz = ROOT.TH1D("dz", "Vertex z: from hits - true;#Deltaz [mm];weighted events", 100, -2000.0, 2000.0)
    hx = ROOT.TH1D("dx", "Vertex x: from hits - true;#Deltax [mm];weighted events", 100, -50.0, 50.0)
    hd = ROOT.TH1D("doca", "Distance of closest approach;DOCA [mm];weighted events", 100, 0.0, 20.0)

    for i in f.entries():
        decay = truth_decay(f["mc_particles"](i))
        if decay is None:
            continue
        true_vertex, _ = decay
        weight = sf.valid_weight(headers(i).weight)

        primaries = {q.trackId for q in f["sim_particles"](i) if q.parentId == 0}
        pts = {t: collections.defaultdict(list) for t in primaries}
        for h in f["sim_hits"](i):
            if h.detectorId == sf.STRAWS and h.trackId in pts:
                s = sf.station_of(h.position[2])
                if s in (0, 1):
                    pts[h.trackId][s].append(tuple(h.position))
        lines = []
        for t, by_station in pts.items():
            if len(by_station[0]) and len(by_station[1]):
                a = scale(tuple(map(sum, zip(*by_station[0]))), 1.0 / len(by_station[0]))
                b = scale(tuple(map(sum, zip(*by_station[1]))), 1.0 / len(by_station[1]))
                lines.append((a, sub(b, a)))
        if len(lines) != 2:
            continue
        result = closest_approach(lines[0][0], lines[0][1], lines[1][0], lines[1][1])
        if result is None:
            continue
        vertex, doca = result
        hz.Fill(vertex[2] - true_vertex[2], weight)
        hx.Fill(vertex[0] - true_vertex[0], weight)
        hd.Fill(doca, weight)

    for hist in (hx, hz):
        if hist.GetEntries() > 10:
            print(f"{hist.GetName()}: RMS {hist.GetRMS():.2f} mm over {int(hist.GetEntries())} events")
    canvas = ROOT.TCanvas("c", "c", 1500, 500)
    canvas.Divide(3, 1)
    for pad, hist in enumerate((hx, hz, hd), start=1):
        canvas.cd(pad)
        sf.style_hist(hist)
        hist.Draw()
    canvas.SaveAs(args.out)


if __name__ == "__main__":
    main()
    sf.finish()
