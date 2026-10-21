// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// ft_production.jsonnet -- stage 1: fixed-target production (booklet ch. 6).
//
// 400 GeV protons on the SHiP target, generated with Pythia 8 and tracked by
// Geant4 through the target and the hadron absorber. Everything that reaches
// a scoring plane just behind the absorber is recorded there and stopped.
// This is aegir's workflows/fixed_target_production.jsonnet with every
// building block written out, so that the whole job can be read in one place.
//
//   phlex -j 4 -c <(jsonnet --tla-code events=1000 --tla-code seed=42 \
//                           $CODE/workflows/ft_production.jsonnet)
//
// Top-level arguments (--tla-code name=value, --tla-str for strings):
//   events  number of protons on target, i.e. proton-nucleus interactions
//   seed    seeds Pythia 8 and Geant4; the same seed gives the same events
//   ecut    kinetic-energy cut in GeV: lighter tracks are killed (default 0.5)
//   output  output name: writes <output>.root and <output>_validation.root
local stage = 'simulation';

function(events, seed=42, ecut=0.5, output='ft_production') {
  stage: stage,

  // One job with `events` events: one proton on target each.
  driver: {
    cpp: 'generate_layers',
    layers: { event: { total: events } },
  },

  sources: {
    // Pythia 8 p-p and p-n collisions in the proportions of tungsten
    // (Z = 74, A = 184), with the interaction point sampled along the target
    // from its interaction length. Particles with c*tau0 below
    // tau0_threshold are decayed by Pythia; the rest are left to Geant4.
    pythia8: {
      cpp: 'fixed_target_source',
      stage: stage,
      beam_energy: 400.0,  // GeV
      target_z: 74,  // proton number, not a coordinate
      target_a: 184,
      target_z_start: 0.0,  // mm
      target_z_end: 1164.0,  // mm
      interaction_length: 191.9,  // mm
      tau0_threshold: 1.0,  // mm/c
      record: 'final_state',
      seed: seed,
    },

    // The SHiP geometry. No detector is sensitive in this stage: only the
    // scoring plane below records anything.
    geometry: {
      cpp: 'geometry_geomodel_provider',
      db_file: 'ship_geometry.db',
      sensitive_volumes: [],
    },

    // No magnetic field: as in FairShip's default, the absorber is not
    // magnetised.
    field: { cpp: 'field_null_provider' },
  },

  modules: {
    geant4: {
      cpp: 'geant4_module',
      physics_list: 'FTFP_BERT',
      seed: seed,
      // Crossing mode: a sensitive volume records the first step of each
      // track that enters it. Tracks below the energy cut are killed.
      sd_mode: 'crossing',
      ke_threshold: ecut,  // GeV
      energy_cut: true,
      // Record every track, so that every ancestor of what reaches the plane
      // is there to keep ...
      particle_ke_cut: 0.0,  // GeV
      // ... and then keep only those: the particles that left a hit and
      // their ancestors.
      keep_particles: 'hit_ancestry',
      // Production cuts [mm] in the dense target and absorber.
      regions: { '/SHiP/target': 50, '/SHiP/muon_shield/magn_absorb': 50 },
      // FairShip's exitHadronAbsorber plane: 1 cm behind the hadron absorber,
      // 7.12 m x 3.40 m, 2 mm thick, in its own parallel world. It records
      // every track that reaches it, whatever the particle, stops it, and
      // writes the ones going downstream as plane_particles for stage 2.
      scoring_planes: [{
        name: 'exit_hadron_absorber',
        id: 1,
        half_x: 3559.0,  // mm
        half_y: 1699.0,  // mm
        half_z: 1.0,  // mm
        after_volume: '/SHiP/muon_shield/magn_absorb',
        gap: 10.0,  // mm
        kill: true,
        record_particles: true,
        ke_threshold: ecut,  // GeV
      }],
      progress_interval: 100,  // log every N events
    },

    // 'full' writes event_number, event_header, mc_particles, sim_hits,
    // sim_particles and plane_particles. filter_empty drops the events in
    // which nothing reached the plane.
    output: {
      cpp: 'sim_output_module',
      mode: 'full',
      rntuple_file: output + '.root',
      histo_file: output + '_validation.root',
      filter_empty: true,
    },
  },
}
