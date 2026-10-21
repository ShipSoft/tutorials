#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Solution: the spectrometer magnet bends the two charges apart (booklet ch. 10).

For every primary muon with hits in all four straw stations, take the mean x
and z of its hits in each station, and compute the change of slope in the
horizontal plane across the magnet, which sits between stations 2 and 3:

    dtheta_x = (x4 - x3) / (z4 - z3) - (x2 - x1) / (z2 - z1)

separately for mu- and mu+. The field of the magnet is vertical, so it bends
in x, and the two charges to opposite sides; without field dtheta_x is
centred on zero.

    python solutions/spectrometer_charge.py muon_gun.root muon_gun_mup.root
    python solutions/spectrometer_charge.py muon_gun_nofield.root --output nofield
"""

import argparse
import collections
import os
import sys

import ROOT

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import shipfiles as sf  # noqa: E402


def station_means(hits, track_id):
    """{station: (mean x, mean z)} of a track's straw hits, in mm."""
    sums = collections.defaultdict(lambda: [0.0, 0.0, 0])
    for h in hits:
        if h.track_id != track_id or h.detector_id != sf.STRAWS:
            continue
        s = sf.station_of(h.position[2])
        if s is not None:
            sums[s][0] += h.position[0]
            sums[s][1] += h.position[2]
            sums[s][2] += 1
    return {s: (x / n, z / n) for s, (x, z, n) in sums.items()}


def kink(means):
    """Change of the x slope between stations 1-2 and 3-4 (rad), or None."""
    if len(means) < 4:
        return None
    (x1, z1), (x2, z2), (x3, z3), (x4, z4) = (means[s] for s in range(4))
    return (x4 - x3) / (z4 - z3) - (x2 - x1) / (z2 - z1)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="simulation output(s)")
    p.add_argument("--output", default="spectrometer_charge", help="PDF file name prefix")
    args = p.parse_args()

    hist = {
        13: ROOT.TH1D("kink_mum", "#mu^{-};#Delta#theta_{x} [mrad];muons", 60, -30.0, 30.0),
        -13: ROOT.TH1D("kink_mup", "#mu^{+};#Delta#theta_{x} [mrad];muons", 60, -30.0, 30.0),
    }
    sf.style_hist(hist[13])
    sf.style_hist(hist[-13], dashed=True)

    for ev in sf.events(args.files, sim_hits="std::vector<SHiP::SimHit>",
                        sim_particles="std::vector<SHiP::SimParticle>"):
        hits = ev.sim_hits
        for p_ in ev.sim_particles:
            if p_.parent_id != 0 or p_.pdg_code not in hist:
                continue
            k = kink(station_means(hits, p_.track_id))
            if k is not None:
                hist[p_.pdg_code].Fill(k * 1000.0)

    for pdg, name in ((13, "mu-"), (-13, "mu+")):
        h = hist[pdg]
        print(f"{name}: {int(h.GetEntries())} cross all four stations, "
              f"mean kink {h.GetMean():+.2f} mrad, rms {h.GetRMS():.2f} mrad")
    canvas = ROOT.TCanvas("c", "", 800, 600)
    hist[13].Draw("hist")
    hist[-13].Draw("hist same")
    canvas.BuildLegend(0.65, 0.75, 0.88, 0.88)
    canvas.SaveAs(f"{args.output}.pdf")
    return 0


if __name__ == "__main__":
    sf.finish(main() or 0)
