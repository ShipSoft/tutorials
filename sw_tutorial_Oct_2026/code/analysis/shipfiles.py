# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Small helpers shared by the booklet's analysis scripts.

Reading SHiP data-model files from PyROOT takes three lines (open a reader,
get a typed view per field, call the view with an entry number). The helpers
below only add the bookkeeping that every script needs: keeping the readers
alive, iterating over entries, and exiting cleanly.

Member names follow data model v0.5 (camelCase, e.g. ``pdgCode``). From v0.6
they are snake_case (``pdg_code``); see appendix B of the booklet.
"""

import os
import math
import sys

import ROOT

ROOT.gROOT.SetBatch(True)

# Detector numbering of SimHit::detectorId (data model detector_id enum).
UBT, SBT, STRAWS, CALORIMETER, TIMING = range(5)

# Geometry, in mm, in the frame of the SHiP geometry (origin at the front face
# of the target). From Geometry/subsystem_envelopes.csv and the Trackers README.
DECAY_VOLUME_Z = (32920.0, 83320.0)
STRAW_STATION_Z = (84070.0, 86070.0, 93070.0, 95070.0)  # station centres
STRAW_STATION_HALF_DEPTH = 500.0

# Keep readers and views alive until exit: tearing down a PyROOT
# RNTupleReader at interpreter shutdown can crash and hide the exit status.
_alive = []


class EventFile:
    """Typed, per-entry access to the fields of an RNTuple.

    >>> f = EventFile("hnl_sim.root")
    >>> f.view("mc_particles", "std::vector<SHiP::MCParticle>")
    >>> for i in f.entries(): particles = f["mc_particles"](i)
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


def station_of(z):
    """Index 0-3 of the straw station containing z (mm), or None."""
    for i, zc in enumerate(STRAW_STATION_Z):
        if abs(z - zc) <= STRAW_STATION_HALF_DEPTH:
            return i
    return None


def mass(p4):
    """Invariant mass of a four-vector (px, py, pz, E); 0 if space-like."""
    px, py, pz, e = p4
    m2 = e * e - px * px - py * py - pz * pz
    return m2 ** 0.5 if m2 > 0 else 0.0


def finish(status=0):
    """Flush and exit without PyROOT teardown (see _alive)."""
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(status)


def valid_weight(value):
    """This tutorial expects finite nonnegative EventCalc weights."""
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid EventCalc weight: {value}")
    return value


def style_hist(hist):
    """High-contrast single-series plots: colour is never the identifier."""
    hist.SetLineColor(ROOT.TColor.GetColor("#005A82"))
    hist.SetLineWidth(2)
    hist.SetMarkerStyle(20)
    hist.SetMarkerColor(ROOT.TColor.GetColor("#005A82"))
    hist.SetFillStyle(0)
