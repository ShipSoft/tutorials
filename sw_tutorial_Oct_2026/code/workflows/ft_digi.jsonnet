// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// ft_digi.jsonnet -- stage 3: digitise the stage-2 hits with Shannon
// (booklet ch. 9).
//
//   phlex -j 4 -c <(jsonnet --tla-str infile=ft_replay.root \
//                           --tla-code entries=<entries of infile> \
//                           --tla-code pot=<protons simulated in stage 1> \
//                           $CODE/workflows/ft_digi.jsonnet)
//
// Top-level arguments:
//   infile   stage-2 output (--tla-str)
//   entries  number of its entries to digitise (aegir writes one per event)
//   pot      protons on target that stage 1 simulated: Shannon spreads the
//            events over the part of a spill that they correspond to
//   seed     seeds the time offsets and the smearing (default 42)
//   output   output name: writes <output>.root and <output>_validation.root
local stage = 'digitisation';
local layer = 'spill';

function(infile, entries, pot, seed=42, output='ft_digi') {
  stage: stage,

  // Shannon processes "spills". Each spill reads one entry of the simulation
  // file, i.e. here one replayed event.
  driver: {
    cpp: 'generate_layers',
    layers: { [layer]: { parent: 'job', total: entries } },
  },

  sources: {
    // Reads sim_hits and sim_particles from the aegir output. The plugin
    // publishes its products under the creator name `rntuple_source`, which
    // the modules below look for.
    rntuple_source: {
      cpp: 'read_sim_file',
      input_file: infile,
      ntuple_name: 'events',
      layer: layer,
    },
  },

  modules: {
    // Turns each SimHit into the hit type of its detector, chosen by
    // SimHit::detector_id (0 UBT, 1 SBT, 2 straws, 3 calorimeter, 4 timing).
    digitise_hits: {
      cpp: 'digitise_hits',
      layer: layer,
      seed: seed,
      // Simulated protons on target: the events are spread over a window of
      // (1.2 s spill) x pot / (4e13 protons per spill).
      pot: pot,
    },

    // Writes one RNTuple per hit collection and validation histograms.
    digitised_output: {
      cpp: 'digitised_output_module',
      mode: 'digi',
      rntuple_file: output + '.root',
      histo_file: output + '_validation.root',
      creator: 'digitise_hits',
      layer: layer,
    },
  },
}
