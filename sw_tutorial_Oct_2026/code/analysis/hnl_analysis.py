#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""HNL -> pi mu analysis on aegir output (booklet chapter 10).

Works on the simulation file, which keeps everything belonging to one event
together: the generator record, the event weight, the Geant4 particles and
the hits. For every event it

  1. finds the HNL decay in the generator record and computes the invariant
     mass and opening angle of the daughters;
  2. finds the two daughters among the Geant4 particles (parentId == 0) and
     records which straw stations each of them crossed;
  3. records the activity in the veto systems (UBT, SBT) and the timing
     detector;
  4. measures the bending of each daughter in the spectrometer magnet from
     its hits in the stations before and after it.

It prints a cut flow, weighted with the EventCalc weights, and writes the
histograms to a ROOT file and one PDF per plot.

    python hnl_analysis.py hnl_sim.root
    python hnl_analysis.py hnl_sim.root --n-expected 123.4 --sbt-threshold 0.045
"""

import argparse
import collections
import math

import ROOT

import shipfiles as sf


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("file", help="aegir output with an 'events' RNTuple")
    p.add_argument("--out", default="hnl_analysis.root",
                   help="ROOT file for the histograms (PDFs go next to it)")
    p.add_argument("--n-expected", type=float, default=None,
                   help="EventCalc's expected number of decays, to turn weighted "
                        "efficiencies into yields")
    p.add_argument("--sbt-threshold", type=float, default=0.0,
                   help="SBT veto: total energy deposit in GeV above which an "
                        "event is vetoed (default 0: positive SBT energy vetoes)")
    p.add_argument("--max-events", type=int, default=None)
    return p.parse_args()


def truth_decay(particles):
    """The HNL decay in the generator record.

    Returns (vertex, daughters) where daughters are the status-1 particles
    with a mother, as (pdg, (px, py, pz, E)) tuples, or None if not found.
    """
    # Copy values before any subsequent RNTuple view call can overwrite them.
    daughters = [p for p in particles if p.status == 1]
    if len(daughters) != 2:
        return None
    if sorted(abs(int(p.pdgCode)) for p in daughters) != [13, 211]:
        return None
    # pi+ (211), mu- (13) have SAME PDG-code signs, opposite charges.
    if daughters[0].pdgCode * daughters[1].pdgCode <= 0:
        return None
    mother = int(daughters[0].motherId)
    if not (0 <= mother < len(particles)) or daughters[1].motherId != mother:
        return None
    if particles[mother].status != 2:
        return None
    vertex = tuple(float(v) for v in daughters[0].vertex)
    if any(abs(a - b) > 1e-6 for a, b in zip(vertex, daughters[1].vertex)):
        return None
    four = [(int(d.pdgCode), (float(d.momentum[0]), float(d.momentum[1]),
                             float(d.momentum[2]), float(d.energy)))
            for d in daughters]
    return vertex, four


def opening_angle(p1, p2):
    a = p1[:3]
    b = p2[:3]
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        raise ValueError("Opening angle is undefined for zero momentum")
    return math.acos(max(-1.0, min(1.0, dot / (na * nb))))


def bending(hits_by_station):
    """Change of the x slope (rad) across the magnet, from mean hit positions.

    hits_by_station maps station index -> list of (x, z). Needs all four.
    """
    if any(not hits_by_station.get(s) for s in range(4)):
        return None
    mean = {s: (sum(x for x, _ in h) / len(h), sum(z for _, z in h) / len(h))
            for s, h in hits_by_station.items()}
    (x1, z1), (x2, z2), (x3, z3), (x4, z4) = (mean[s] for s in range(4))
    slope_in = (x2 - x1) / (z2 - z1)
    slope_out = (x4 - x3) / (z4 - z3)
    return math.atan(slope_out) - math.atan(slope_in)


def main():
    args = parse_args()
    f = sf.EventFile(args.file)
    f.view("mc_particles", "std::vector<SHiP::MCParticle>")
    f.view("sim_particles", "std::vector<SHiP::SimParticle>")
    f.view("sim_hits", "std::vector<SHiP::SimHit>")
    headers = f.view("event_header", "SHiP::EventHeader")
    if args.max_events is not None and args.max_events < 1:
        raise ValueError("--max-events must be positive")
    if args.sbt_threshold < 0 or not math.isfinite(args.sbt_threshold):
        raise ValueError("--sbt-threshold must be finite and nonnegative")
    if args.n_expected is not None and (args.n_expected < 0 or not math.isfinite(args.n_expected)):
        raise ValueError("--n-expected must be finite and nonnegative")
    print("TEACHING PROXY: z-only containment; broad sensitive-volume vetoes.")

    # ---- histograms -------------------------------------------------------
    ROOT.TH1.SetDefaultSumw2(True)
    h = {
        "mass": ROOT.TH1D("mass", "m(#pi#mu) from the generator record;m [GeV];weighted events", 100, 0.0, 3.0),
        "decay_z": ROOT.TH1D("decay_z", "HNL decay position;z [m];weighted events", 120, 25.0, 90.0),
        "opening": ROOT.TH1D("opening", "Opening angle of the daughters;#theta [mrad];weighted events", 100, 0.0, 200.0),
        "p_daughter": ROOT.TH1D("p_daughter", "Daughter momentum;p [GeV];weighted daughters", 100, 0.0, 100.0),
        "n_stations": ROOT.TH1D("n_stations", "Straw stations crossed per daughter;stations;weighted daughters", 5, -0.5, 4.5),
        "sbt_edep": ROOT.TH1D("sbt_edep", "SBT energy deposit per event;E [MeV];weighted events", 100, 0.0, 200.0),
        "p_kick": ROOT.TH1D("p_kick", "p #times |#Delta#theta_{x}| across the magnet;p|#Delta#theta| [GeV rad];weighted daughters", 150, 0.0, 3.0),
        "timing_dt": ROOT.TH1D("timing_dt", "Earliest primary hits: muon minus pion;t_{#mu} - t_{#pi} [ps];weighted events", 100, -500.0, 500.0),
    }

    # ---- cut flow -----------------------------------------------------------
    steps = ["all events", "HNL decay found", "decay in nominal z range",
             "both daughters: 4 straw stations", "UBT silent", "SBT below threshold",
             "both daughters hit timing detector"]
    passed = collections.OrderedDict((s, [0, 0.0]) for s in steps)  # count, sum of weights

    def count(step, w):
        passed[step][0] += 1
        passed[step][1] += w

    for i in f.entries(args.max_events):
        w = sf.valid_weight(headers(i).weight)
        count("all events", w)

        decay = truth_decay(f["mc_particles"](i))
        if decay is None:
            continue
        count("HNL decay found", w)
        vertex, daughters = decay
        (_, p4a), (_, p4b) = daughters
        total = tuple(a + b for a, b in zip(p4a, p4b))
        h["mass"].Fill(sf.mass(total), w)
        h["decay_z"].Fill(vertex[2] / 1000.0, w)
        h["opening"].Fill(1000.0 * opening_angle(p4a, p4b), w)

        lo, hi = sf.DECAY_VOLUME_Z
        if not lo <= vertex[2] <= hi:
            continue
        count("decay in nominal z range", w)

        # The daughters as Geant4 tracks: primaries have parentId == 0.
        primaries = {p.trackId: p for p in f["sim_particles"](i) if p.parentId == 0}
        stations = {tid: collections.defaultdict(list) for tid in primaries}
        timing_t = {}
        ubt_hits = 0
        sbt_edep = 0.0
        for hit in f["sim_hits"](i):
            det = hit.detectorId
            if det == sf.UBT:
                ubt_hits += 1
            elif det == sf.SBT:
                sbt_edep += hit.energyDeposit
            elif det == sf.STRAWS and hit.trackId in stations:
                s = sf.station_of(hit.position[2])
                if s is not None:
                    stations[hit.trackId][s].append((hit.position[0], hit.position[2]))
            elif det == sf.TIMING and hit.trackId in primaries:
                timing_t[hit.trackId] = min(timing_t.get(hit.trackId, math.inf), float(hit.time))

        for tid, p in primaries.items():
            pmag = math.sqrt(sum(c * c for c in p.momentum))
            h["p_daughter"].Fill(pmag, w)
            h["n_stations"].Fill(len(stations[tid]), w)
            kick = bending(stations[tid])
            if kick is not None:
                h["p_kick"].Fill(pmag * abs(kick), w)
        h["sbt_edep"].Fill(1000.0 * sbt_edep, w)

        if (sorted(int(p.pdgCode) for p in primaries.values())
                != sorted(pdg for pdg, _ in daughters)
                or any(len(stations[t]) < 4 for t in primaries)):
            continue
        count("both daughters: 4 straw stations", w)
        if ubt_hits:
            continue
        count("UBT silent", w)
        if sbt_edep > args.sbt_threshold:
            continue
        count("SBT below threshold", w)
        if len(timing_t) != 2:
            continue
        count("both daughters hit timing detector", w)
        t_mu = next(timing_t[t] for t, p in primaries.items() if abs(p.pdgCode) == 13)
        t_pi = next(timing_t[t] for t, p in primaries.items() if abs(p.pdgCode) == 211)
        h["timing_dt"].Fill(1000.0 * (t_mu - t_pi), w)

    # ---- report ---------------------------------------------------------------
    total_w = passed["all events"][1]
    if total_w <= 0:
        raise ValueError("No positive total weight; efficiency is undefined")
    print(f"\n{'selection':40s} {'events':>8s} {'sum w':>12s} {'eff (w)':>9s}"
          + ("  {:>10s}".format("yield") if args.n_expected is not None else ""))
    for step, (n, sw) in passed.items():
        eff = sw / total_w if total_w > 0 else 0.0
        line = f"{step:40s} {n:8d} {sw:12.5g} {eff:9.4f}"
        if args.n_expected is not None:
            line += f"  {args.n_expected * eff:10.4g}"
        print(line)

    out = ROOT.TFile(args.out, "RECREATE")
    canvas = ROOT.TCanvas("c", "c", 800, 600)
    stem = args.out.rsplit(".", 1)[0]
    for name, hist in h.items():
        hist.Write()
        sf.style_hist(hist)
        hist.Draw("hist")
        print(f"{name}: underflow={hist.GetBinContent(0):.5g}, "
              f"overflow={hist.GetBinContent(hist.GetNbinsX()+1):.5g}")
        canvas.SaveAs(f"{stem}_{name}.pdf")
    out.Close()
    print(f"\nhistograms written to {args.out} and {stem}_*.pdf")


if __name__ == "__main__":
    main()
    sf.finish()
