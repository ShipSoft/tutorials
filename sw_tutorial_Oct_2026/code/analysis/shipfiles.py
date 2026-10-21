# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Small helpers shared by the booklet's analysis scripts.

Reading SHiP data-model files from PyROOT takes three lines (open a reader,
get a typed view per field, call the view with an entry number). The helpers
below only add the bookkeeping that every script needs: keeping the readers
alive, iterating over entries, and exiting cleanly.

Member names follow data model v0.6 (snake_case, e.g. ``pdg_code``); see
appendix B of the booklet.
"""

import os
import sys
import types

import ROOT

ROOT.gROOT.SetBatch(True)

# SimHit::detector_id: the data model's detector_id enum, and the id aegir
# gives the hits of a scoring plane.
UBT, SBT, STRAWS, CALORIMETER, TIMING = range(5)
SCORING_PLANE = 100
DETECTOR_NAMES = {
    UBT: "UBT",
    SBT: "SBT",
    STRAWS: "straws",
    CALORIMETER: "calorimeter",
    TIMING: "timing",
}

# Geometry, in mm, in the frame of the SHiP geometry (origin at the front face
# of the target). From Geometry/subsystem_envelopes.csv and the Trackers README.
DECAY_VOLUME_Z = (32920.0, 83320.0)
STRAW_STATION_Z = (84070.0, 86070.0, 93070.0, 95070.0)  # station centres
STRAW_STATION_HALF_DEPTH = 500.0

# A SPS spill delivers 4e13 protons on target.
POT_PER_SPILL = 4e13

# Keep readers and views alive until exit: tearing down a PyROOT
# RNTupleReader at interpreter shutdown can crash and hide the exit status.
_alive = []


class EventFile:
    """Typed, per-entry access to the fields of an RNTuple.

    >>> f = EventFile("ft_replay.root")
    >>> f.view("sim_hits", "std::vector<SHiP::SimHit>")
    >>> for i in f.entries(): hits = f["sim_hits"](i)
    """

    def __init__(self, path, ntuple="events"):
        self.path = path
        self.reader = ROOT.RNTupleReader.Open(ntuple, path)
        self.views = {}
        _alive.append(self.reader)

    def view(self, field, cpp_type, optional=False):
        """Create a view on `field`; with optional=True return None if absent."""
        try:
            v = self.reader.GetView[cpp_type](field)
        except Exception:
            if optional:
                return None
            raise
        _alive.append(v)
        self.views[field] = v
        return v

    def __getitem__(self, field):
        return self.views[field]

    def __len__(self):
        return int(self.reader.GetNEntries())

    def entries(self, limit=None):
        n = len(self)
        return range(n if limit is None else min(n, limit))


def events(paths, **fields):
    """Every entry of every file in `paths`, as a namespace of the named fields.

    >>> for ev in events(["a.root", "b.root"], sim_hits="std::vector<SHiP::SimHit>"):
    ...     hits = ev.sim_hits

    Several files are read one after the other, as one sample: the chunks of a
    batch production, for example.
    """
    for path in paths:
        f = EventFile(path)
        for name, cpp_type in fields.items():
            f.view(name, cpp_type)
        for i in f.entries():
            yield types.SimpleNamespace(**{name: f[name](i) for name in fields})


def species(pdg):
    """Coarse particle class of a PDG code, for the tables of the scripts."""
    a = abs(int(pdg))
    if a == 13:
        return "muon"
    if a in (12, 14, 16):
        return "neutrino"
    if a == 22:
        return "photon"
    if a == 11:
        return "electron"
    if a == 2112:
        return "neutron"
    if a in (211, 321, 2212, 130, 310):
        return "hadron"
    return "other"


def momentum(p):
    """|p| of a three-vector given as a sequence (px, py, pz)."""
    return (p[0] * p[0] + p[1] * p[1] + p[2] * p[2]) ** 0.5


def transverse(p):
    """Transverse component sqrt(px^2 + py^2)."""
    return (p[0] * p[0] + p[1] * p[1]) ** 0.5


def station_of(z):
    """Index 0-3 of the straw station containing z (mm), or None."""
    for i, zc in enumerate(STRAW_STATION_Z):
        if abs(z - zc) <= STRAW_STATION_HALF_DEPTH:
            return i
    return None


def per_pot(count, pot):
    """A count normalised to the number of protons on target, and per spill."""
    if pot <= 0:
        raise ValueError(f"the number of protons on target must be positive: {pot}")
    rate = count / pot
    return rate, rate * POT_PER_SPILL


def finish(status=0):
    """Flush and exit without PyROOT teardown (see _alive)."""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)


def style_hist(hist, dashed=False):
    """High-contrast plots: colour is never the only identifier."""
    hist.SetLineColor(ROOT.TColor.GetColor("#162A3A" if dashed else "#005A82"))
    hist.SetLineWidth(2)
    hist.SetLineStyle(2 if dashed else 1)
    hist.SetMarkerStyle(20)
    hist.SetMarkerColor(ROOT.TColor.GetColor("#005A82"))
    hist.SetFillStyle(0)
