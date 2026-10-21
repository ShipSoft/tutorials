#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Summarise aegir output per event, or compare two outputs (booklet ch. 7).

Entries of an aegir file are in the order events finished, not in event
order, so events are matched by their `event_number` field.

    python sim_summary.py ft_replay.root                    # totals
    python sim_summary.py ft_replay.root ft_replay_run2.root  # compare
"""

import argparse

import shipfiles as sf


def summarise(path):
    """event_number -> (n_hits, n_particles, sum of energy deposits, sum of hit z)."""
    f = sf.EventFile(path)
    f.view("event_number", "std::uint64_t")
    f.view("sim_hits", "std::vector<SHiP::SimHit>")
    f.view("sim_particles", "std::vector<SHiP::SimParticle>")
    out = {}
    for i in f.entries():
        hits = f["sim_hits"](i)
        edep = sum(h.energy_deposit for h in hits)
        zsum = sum(h.position[2] for h in hits)
        event_id = int(f["event_number"](i))
        if event_id in out:
            raise ValueError(f"Duplicate event_number {event_id} in {path}")
        out[event_id] = (len(hits), len(f["sim_particles"](i)), edep, zsum)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="one or two aegir output files")
    args = p.parse_args()
    if len(args.files) not in (1, 2):
        p.error("supply one or two files")

    a = summarise(args.files[0])
    n_hits = sum(v[0] for v in a.values())
    n_part = sum(v[1] for v in a.values())
    print(f"{args.files[0]}: {len(a)} events, {n_hits} hits, {n_part} particles, "
          f"{sum(v[2] for v in a.values()):.6f} GeV deposited")
    if len(args.files) == 1:
        return

    b = summarise(args.files[1])
    common = sorted(set(a) & set(b))
    identical = sum(1 for k in common if a[k] == b[k])
    print(f"{args.files[1]}: {len(b)} events")
    print(f"events in both: {len(common)}, matching summaries: {identical}, "
          f"different: {len(common) - identical}")
    print(f"only in first: {len(set(a)-set(b))}; only in second: {len(set(b)-set(a))}")
    print("This compares selected summaries, not every stored field.")
    for k in [k for k in common if a[k] != b[k]][:5]:
        print(f"  event {k}: hits {a[k][0]} vs {b[k][0]}, "
              f"edep {a[k][2]:.6f} vs {b[k][2]:.6f} GeV")

    return 0 if a == b else 1


if __name__ == "__main__":
    sf.finish(main() or 0)
