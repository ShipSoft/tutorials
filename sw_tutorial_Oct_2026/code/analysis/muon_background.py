#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Where the muons from the target end up in SHiP (booklet ch. 10).

Reads a simulation with the detectors sensitive: the artificial muons of
muon_gun.jsonnet, or a replay of stage-1 plane particles (ft_replay.jsonnet).
For every primary muon it finds the detectors in which the muon itself left
hits, and for every event the detectors with any hit at all (the muon's
secondaries included).

    python muon_background.py muon_gun.root                 # fractions of the muons
    python muon_background.py ft_replay.root --pot 1000     # rates per proton

Without --pot the counts are given as fractions of the primary muons. With
--pot, the number of protons simulated in stage 1, they are normalised to the
protons on target and to a spill.
"""

import argparse
import collections

import ROOT

import shipfiles as sf

DETECTORS = (sf.UBT, sf.SBT, sf.STRAWS, sf.TIMING, sf.CALORIMETER)


def primary_muons(particles):
    """track_id -> SimParticle of the primary muons (parent_id 0)."""
    return {p.track_id: p for p in particles if p.parent_id == 0 and abs(p.pdg_code) == 13}


def hits_by_track(hits):
    """track_id -> list of (detector_id, z) of its hits."""
    out = collections.defaultdict(list)
    for h in hits:
        out[h.track_id].append((h.detector_id, h.position[2]))
    return out


def stations(track_hits):
    """Set of straw stations (0-3) in which a track left hits."""
    found = set()
    for det, z in track_hits:
        if det == sf.STRAWS:
            s = sf.station_of(z)
            if s is not None:
                found.add(s)
    return found


def muon_record(track_hits):
    """What one muon reached: the set of detectors and the straw stations."""
    return {det for det, _ in track_hits}, stations(track_hits)


def tally(records):
    """Counts of muons per category, from (detectors, stations) records."""
    c = collections.Counter()
    for dets, st in records:
        c["all"] += 1
        for det in DETECTORS:
            if det in dets:
                c[sf.DETECTOR_NAMES[det]] += 1
        if len(st) == 4:
            c["all 4 stations"] += 1
    return c


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="simulation output(s) (muon_gun.root)")
    p.add_argument("--pot", type=float, default=None,
                   help="protons on target simulated in stage 1 (replays only)")
    p.add_argument("--output", default="muon_background", help="prefix of the PDF files")
    args = p.parse_args()
    if args.pot is not None and args.pot <= 0:
        p.error("--pot must be positive")

    h_p_all = ROOT.TH1D("p_all", "primary muons;p at the start [GeV];muons", 40, 0.0, 400.0)
    h_p_straw = ROOT.TH1D("p_straw", "reaching the straws;p at the start [GeV];muons",
                          40, 0.0, 400.0)
    h_xy = ROOT.TH2D("station1_xy", "hits in straw station 1;x [mm];y [mm]",
                     60, -3000.0, 3000.0, 70, -3500.0, 3500.0)
    h_sbt_z = ROOT.TH1D("sbt_z", "SBT hits;z [m];hits", 52, 32.0, 84.0)
    sf.style_hist(h_p_all)
    sf.style_hist(h_p_straw, dashed=True)
    sf.style_hist(h_sbt_z)

    records = []
    events_with = collections.Counter()
    n_events = 0
    for ev in sf.events(args.files, sim_hits="std::vector<SHiP::SimHit>",
                        sim_particles="std::vector<SHiP::SimParticle>"):
        n_events += 1
        hits = ev.sim_hits
        muons = primary_muons(ev.sim_particles)
        by_track = hits_by_track(hits)
        for tid, mu in muons.items():
            dets, st = muon_record(by_track.get(tid, []))
            records.append((dets, st))
            p_start = sf.momentum((mu.momentum[0], mu.momentum[1], mu.momentum[2]))
            h_p_all.Fill(p_start)
            if sf.STRAWS in dets:
                h_p_straw.Fill(p_start)
        for det in {h.detector_id for h in hits}:
            if det in sf.DETECTOR_NAMES:
                events_with[sf.DETECTOR_NAMES[det]] += 1
        for h in hits:
            if h.detector_id == sf.STRAWS and sf.station_of(h.position[2]) == 0:
                h_xy.Fill(h.position[0], h.position[1])
            elif h.detector_id == sf.SBT:
                h_sbt_z.Fill(h.position[2] / 1000.0)

    muon_counts = tally(records)
    name = args.files[0] if len(args.files) == 1 else f"{len(args.files)} files"
    source = f"from {args.pot:g} protons on target" if args.pot else "no normalisation to protons"
    print(f"{name}: {n_events} events, {muon_counts['all']} primary muons, {source}")

    def row(label, count):
        if args.pot:
            rate, spill = sf.per_pot(count, args.pot)
            return f"{label:16s} {count:7d} {rate:11.3e} {spill:11.3e}"
        fraction = count / muon_counts["all"] if muon_counts["all"] else 0.0
        return f"{label:16s} {count:7d} {fraction:11.3f}"

    columns = f"{'per POT':>11s} {'per spill':>11s}" if args.pot else f"{'fraction':>11s}"
    print(f"\n{'muons reaching':16s} {'muons':>7s} {columns}")
    for name in ("all", "UBT", "SBT", "straws", "all 4 stations", "timing", "calorimeter"):
        print(row(name, muon_counts[name]))
    print(f"\n{'events with hits':16s} {'events':>7s} {columns}")
    for det in DETECTORS:
        name = sf.DETECTOR_NAMES[det]
        print(row(name, events_with[name]))

    canvas = ROOT.TCanvas("c", "", 800, 600)
    canvas.SetLogy(True)
    h_p_all.Draw("hist")
    h_p_straw.Draw("hist same")
    legend = ROOT.TLegend(0.55, 0.75, 0.88, 0.88)
    legend.AddEntry(h_p_all, "all primary muons", "l")
    legend.AddEntry(h_p_straw, "reaching the straws (dashed)", "l")
    legend.Draw()
    canvas.SaveAs(f"{args.output}_p.pdf")
    h_sbt_z.Draw("hist")
    canvas.SaveAs(f"{args.output}_sbt_z.pdf")
    canvas.SetLogy(False)
    h_xy.Draw("colz")
    canvas.SaveAs(f"{args.output}_station1_xy.pdf")
    return 0


if __name__ == "__main__":
    sf.finish(main() or 0)
