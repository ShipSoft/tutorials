#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Position residuals of Shannon's digitised hits (booklet chapter 9).

Shannon writes one RNTuple per hit collection, one entry per hit, plus a copy
of the input simulated hits (`sim_hits`). The digitisers copy z, the energy
deposit, the track ID and the PDG code unchanged, so a digitised hit with a
unique composite key can be paired with the simulated hit it came from through
that key. The script
histograms x_digi - x_sim and y_digi - y_sim and fits a Gaussian.

    python digi_residuals.py ft_digi.root --collection straw_tubes_hits
"""

import argparse
import collections

import ROOT

import shipfiles as sf

# collection -> (C++ hit type, SimHit::detector_id)
COLLECTIONS = {
    "ubt_hits": ("SHiP::UBTHit", sf.UBT),
    "sbt_hits": ("SHiP::SBTHit", sf.SBT),
    "straw_tubes_hits": ("SHiP::StrawTubesHit", sf.STRAWS),
    "calorimeter_hits": ("SHiP::CaloHit", sf.CALORIMETER),
    "timing_detector_hits": ("SHiP::TimeDetHit", sf.TIMING),
}


def key(h):
    return (h.track_id, h.pdg_code, h.position[2], h.energy_deposit)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", help="Shannon output file")
    p.add_argument("--collection", default="straw_tubes_hits", choices=sorted(COLLECTIONS))
    p.add_argument("--range", type=float, default=0.5, help="histogram range +- [mm]")
    args = p.parse_args()
    if args.range <= 0:
        p.error("--range must be positive")
    hit_type, det = COLLECTIONS[args.collection]

    # Simulated hits of this detector, indexed by the key; keys seen twice are
    # ambiguous and dropped.
    sim = sf.EventFile(args.file, ntuple="sim_hits")
    sim.view("hit", "SHiP::SimHit")
    by_key = {}
    seen = collections.Counter()
    for i in sim.entries():
        h = sim["hit"](i)
        if h.detector_id != det:
            continue
        k = key(h)
        seen[k] += 1
        by_key[k] = (h.position[0], h.position[1])
    ambiguous = {k for k, n in seen.items() if n > 1}

    digi = sf.EventFile(args.file, ntuple=args.collection)
    digi.view("hit", hit_type)
    digi_counts = collections.Counter(key(digi["hit"](i).rec_hit) for i in digi.entries())
    ambiguous.update(k for k, n in digi_counts.items() if n > 1)
    r = args.range
    hx = ROOT.TH1D("res_x", f"{args.collection};x_{{digi}} - x_{{sim}} [mm];hits", 100, -r, r)
    hy = ROOT.TH1D("res_y", f"{args.collection};y_{{digi}} - y_{{sim}} [mm];hits", 100, -r, r)
    paired = unpaired = 0
    for i in digi.entries():
        rec = digi["hit"](i).rec_hit
        k = key(rec)
        if k not in by_key or k in ambiguous:
            unpaired += 1
            continue
        xs, ys = by_key[k]
        hx.Fill(rec.position[0] - xs)
        hy.Fill(rec.position[1] - ys)
        paired += 1

    print(f"{args.collection}: {len(digi)} digitised hits, {paired} paired, "
          f"{unpaired} unpaired ({len(ambiguous)} ambiguous keys)")
    canvas = ROOT.TCanvas("c", "c", 1200, 500)
    canvas.Divide(2, 1)
    for pad, hist in ((1, hx), (2, hy)):
        canvas.cd(pad)
        sf.style_hist(hist)
        if hist.GetEntries() > 10:
            status = int(hist.Fit("gaus", "Q"))
            fit = hist.GetFunction("gaus")
            if status != 0 or not fit:
                print(f"  {hist.GetName()}: Gaussian fit failed (status {status})")
                hist.Draw()
                continue
            fit.SetLineColor(ROOT.kBlack)
            fit.SetLineStyle(2)
            print(f"  {hist.GetName()}: sigma = {fit.GetParameter(2):.4f} "
                  f"+- {fit.GetParError(2):.4f} mm")
        hist.Draw()
    out = f"residuals_{args.collection}.pdf"
    canvas.SaveAs(out)
    print(f"  plot: {out}")


if __name__ == "__main__":
    main()
    sf.finish()
