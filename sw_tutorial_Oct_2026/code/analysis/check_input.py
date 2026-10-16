#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Sanity checks on a converted HNL input file (booklet chapter 6).

Checks what aegir relies on: the particle statuses, the mother links of the
tracked particles, the event weights, and where the decay vertices lie
relative to the decay volume of the SHiP geometry.

    python check_input.py hnl_events.root
"""

import argparse
import collections
import math
import os
import sys

import ROOT

# Decay volume along z in the frame of the SHiP geometry (origin at the front
# face of the target), from Geometry/subsystem_envelopes.csv. In mm.
DECAY_VOLUME_Z = (32920.0, 83320.0)

# Keep readers and views alive until os._exit: tearing down a PyROOT
# RNTupleReader at interpreter exit can crash and hide the exit status.
_alive = []


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="ROOT file with an 'events' RNTuple")
    parser.add_argument("--ntuple", default="events")
    args = parser.parse_args()

    reader = ROOT.RNTupleReader.Open(args.ntuple, args.file)
    particles = reader.GetView["std::vector<SHiP::MCParticle>"]("mc_particles")
    _alive.extend((reader, particles))
    try:
        headers = reader.GetView["SHiP::EventHeader"]("event_header")
        _alive.append(headers)
    except Exception:  # field absent: aegir would fall back to weight 1.0
        headers = None

    n_events = reader.GetNEntries()
    if n_events == 0:
        raise ValueError("Input contains no events")
    statuses = collections.Counter()
    tracked_pdg = collections.Counter()
    orphans = 0          # tracked particles without a mother
    decay_z = []
    weights = []
    invalid_mothers = inconsistent_links = 0

    for i in range(n_events):
        vertex_z = None
        event = particles(i)
        for p in event:
            statuses[p.status] += 1
            if p.status != 1:
                continue
            tracked_pdg[p.pdgCode] += 1
            mid = int(p.motherId)
            if mid < 0:
                orphans += 1
            elif mid >= len(event):
                invalid_mothers += 1
            else:
                vertex_z = float(p.vertex[2])
            mothers = list(p.mothers)
            if (mid < 0 and mothers) or (mid >= 0 and (not mothers or mothers[0] != mid)):
                inconsistent_links += 1
        if vertex_z is not None:
            decay_z.append(vertex_z)
        w = float(headers(i).weight) if headers else 1.0
        if not math.isfinite(w) or not 0 <= w <= 1:
            raise ValueError(f"Entry {i}: expected P_decay in [0, 1], got {w}")
        weights.append(w)

    print(f"file:            {args.file}")
    print(f"events:          {n_events}")
    print(f"status counts:   {dict(sorted(statuses.items()))}")
    print(f"tracked PDG:     {dict(sorted(tracked_pdg.items()))}")
    print(f"tracked without mother: {orphans}")

    print(f"invalid mother indices: {invalid_mothers}; inconsistent mother lists: {inconsistent_links}")
    if headers is None:
        print("event_header:    MISSING -- aegir will use weight 1.0 for every event")
    else:
        print(f"weights:         min {min(weights):.4g}  max {max(weights):.4g}  "
              f"sum {sum(weights):.6g}")

    if decay_z:
        lo, hi = DECAY_VOLUME_Z
        outside = sum(1 for z in decay_z if not lo <= z <= hi)
        print(f"decay z [mm]:    min {min(decay_z):.1f}  max {max(decay_z):.1f}")
        print(f"outside nominal z range [{lo:.0f}, {hi:.0f}] mm: "
              f"{outside} of {len(decay_z)} ({100.0 * outside / len(decay_z):.2f}%)")

    print("This tests z only: transverse containment requires the geometry.")
    if headers is None or orphans or invalid_mothers or inconsistent_links or sum(weights) <= 0:
        raise ValueError("Input failed the tutorial contract; fix it before simulation")


if __name__ == "__main__":
    main()
    sys.stdout.flush()  # os._exit skips the buffer flush
    os._exit(0)
