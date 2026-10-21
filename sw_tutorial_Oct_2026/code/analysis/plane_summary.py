#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""What leaves the hadron absorber: the stage-1 scoring plane (booklet ch. 6).

Reads the output of ft_production.jsonnet. Every particle that reached the
plane behind the hadron absorber left one SimHit there, with detector_id 100.
The script counts them by particle type, normalises the counts to the protons
on target, and plots the muons.

    python plane_summary.py ft_production.root --pot 1000
    python plane_summary.py chunk_*/ft_production.root --pot 100000   # several files

--pot is the number of protons simulated (the `events` of stage 1): the file
holds only the events in which something reached the plane, so it cannot
tell on its own how many protons were simulated.
"""

import argparse
import collections

import ROOT

import shipfiles as sf

SPECIES = ("muon", "neutrino", "photon", "electron", "neutron", "hadron", "other")


def plane_hits(hits):
    """The scoring-plane hits of one event."""
    return [h for h in hits if h.detector_id == sf.SCORING_PLANE]


def count_species(pdg_codes):
    """Counter of sf.species() over PDG codes; muons also split by charge."""
    counts = collections.Counter(sf.species(p) for p in pdg_codes)
    counts["mu-"] = sum(1 for p in pdg_codes if p == 13)
    counts["mu+"] = sum(1 for p in pdg_codes if p == -13)
    return counts


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="stage-1 output(s) (ft_production.root)")
    p.add_argument("--pot", type=float, required=True,
                   help="protons on target simulated in stage 1")
    p.add_argument("--output", default="plane", help="prefix of the PDF files")
    args = p.parse_args()
    if args.pot <= 0:
        p.error("--pot must be positive")

    h_p = ROOT.TH1D("muon_p", "muons at the plane;p [GeV];muons", 80, 0.0, 400.0)
    h_pt = ROOT.TH1D("muon_pt", "muons at the plane;p_{T} [GeV];muons", 60, 0.0, 6.0)
    h_xy = ROOT.TH2D("muon_xy", "muons at the plane;x [mm];y [mm]",
                     72, -3600.0, 3600.0, 34, -1700.0, 1700.0)
    for h in (h_p, h_pt):
        sf.style_hist(h)

    counts = collections.Counter()
    n_events = 0
    for ev in sf.events(args.files, sim_hits="std::vector<SHiP::SimHit>"):
        n_events += 1
        hits = plane_hits(ev.sim_hits)
        counts.update(count_species([h.pdg_code for h in hits]))
        for h in hits:
            if abs(h.pdg_code) != 13:
                continue
            p3 = (h.momentum[0], h.momentum[1], h.momentum[2])
            h_p.Fill(sf.momentum(p3))
            h_pt.Fill(sf.transverse(p3))
            h_xy.Fill(h.position[0], h.position[1])

    name = args.files[0] if len(args.files) == 1 else f"{len(args.files)} files"
    print(f"{name}: {n_events} events with something at the plane, "
          f"from {args.pot:g} protons on target")
    print(f"{'particle':10s} {'at plane':>9s} {'per POT':>11s} {'per spill':>11s}")
    for name in (*SPECIES, "mu+", "mu-"):
        rate, spill = sf.per_pot(counts[name], args.pot)
        print(f"{name:10s} {counts[name]:9d} {rate:11.3e} {spill:11.3e}")

    canvas = ROOT.TCanvas("c", "", 800, 600)
    for h, log in ((h_p, True), (h_pt, True)):
        canvas.SetLogy(log)
        h.Draw("hist")
        canvas.SaveAs(f"{args.output}_{h.GetName()}.pdf")
    canvas.SetLogy(False)
    h_xy.Draw("colz")
    canvas.SaveAs(f"{args.output}_{h_xy.GetName()}.pdf")
    return 0


if __name__ == "__main__":
    sf.finish(main() or 0)
