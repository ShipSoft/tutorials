// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// hnl_digi.jsonnet -- digitise the aegir output with Shannon
// (booklet chapter 9).
//
//   phlex -j 4 -c <(jsonnet \
//       --ext-str entries=1000 \
//       --ext-str infile=hnl_sim.root \
//       --ext-str digiout=hnl_digi.root \
//       --ext-str histo=hnl_digi_validation.root \
//       $CODE/workflows/hnl_digi.jsonnet)
//
// `entries` is the number of entries of the input file to process: the number
// of events you simulated (aegir writes one entry per event), or the output of
// `python aegir/scripts/count_entries.py hnl_sim.root`.
local stage = 'digitisation';
local layer = 'spill';

{
  stage: stage,

  // Shannon processes "spills". Each spill reads one entry of the simulation
  // file, i.e. here one simulated HNL event.
  driver: {
    cpp: 'generate_layers',
    layers: { [layer]: { parent: 'job', total: std.parseInt(std.extVar('entries')) } },
  },

  sources: {
    // Reads sim_hits and sim_particles from the aegir output. The plugin
    // publishes its products under the creator name `rntuple_source`, which
    // the modules below look for.
    rntuple_source: {
      cpp: 'read_sim_file',
      input_file: std.extVar('infile'),
      ntuple_name: 'events',
      layer: layer,
    },
  },

  modules: {
    // Turns each SimHit into the hit type of its detector, chosen by
    // SimHit::detectorId (0 UBT, 1 SBT, 2 straws, 3 calorimeter, 4 timing).
    digitise_hits: {
      cpp: 'digitise_hits',
      layer: layer,
      seed: 42,
      // Simulated protons on target per spill: sets the time window over
      // which hits are spread (spill length x pot / 4e13). Irrelevant for a
      // signal-only sample; the default is 10000.
      pot: 10000,
    },

    // Writes one RNTuple per hit collection and validation histograms.
    digitised_output: {
      cpp: 'digitised_output_module',
      mode: 'digi',
      rntuple_file: std.extVar('digiout'),
      histo_file: std.extVar('histo'),
      creator: 'digitise_hits',
      layer: layer,
    },
  },
}
