// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// hnl_sim.jsonnet -- simulate converted EventCalc HNL events with aegir
// (booklet chapter 7).
//
// Self-contained on purpose: every plugin and key is spelled out here instead
// of being imported from aegir's workflows/lib.libsonnet, so you can see the
// whole job in one file.
//
//   phlex -j 4 -c <(jsonnet \
//       --ext-str events=1000 \
//       --ext-str infile=hnl_events.root \
//       --ext-str simout=hnl_sim.root \
//       --ext-str histo=hnl_sim_validation.root \
//       $CODE/workflows/hnl_sim.jsonnet)
//
// Optional: --tla-code seed=N to change the Geant4 seed (default fixed below,
// so that everyone in the tutorial simulates the same events).
local stage = 'simulation';

function(seed=20261015) {
  stage: stage,

  // One job containing `events` events. Must not exceed the number of entries
  // in the input file.
  driver: {
    cpp: 'generate_layers',
    layers: { event: { total: std.parseInt(std.extVar('events')) } },
  },

  sources: {
    // The HNL events: one entry of the input RNTuple per event. The tracked
    // particles are the status-1 entries of `mc_particles`; the event weight
    // comes from the `event_header` field.
    input: {
      cpp: 'file_source',
      stage: stage,  // sources need their own copy of the stage name
      input_file: std.extVar('infile'),
      ntuple: 'events',
      product: 'mc_particles',
      skip: 0,  // first entry to read
    },

    // The SHiP geometry, read through the geometry service. The position of a
    // name fragment in `sensitive_volumes` becomes SimHit::detectorId, and
    // Shannon reads that ID with the data model's detector_id enum, so this
    // list must have exactly these five entries in exactly this order. A
    // logical volume is sensitive if its name *contains* the fragment.
    geometry: {
      cpp: 'geometry_geomodel_provider',
      db_file: 'ship_geometry.db',
      sensitive_volumes: [
        '/SHiP/upstream_tagger/',          // 0 UBT (tiles, plus their air envelopes)
        '/SHiP/decay_volume/sbt/sensors',  // 1 SBT (LAB cells, plus their walls)
        '/SHiP/trackers/straw_gas',        // 2 straw tubes
        '/SHiP/calorimeter/',              // 3 calorimeter (scintillator and absorber)
        '/SHiP/timing_detector/bar',       // 4 timing detector
      ],
    },

    // Field maps in the SHiP field-map format. Each map is stored in its own
    // frame; `translation` (mm) places its origin in the geometry, and the
    // field is attached to the logical volumes whose names contain
    // `volume_pattern`. Bare file names are looked up in the current
    // directory, then in $SHIPFIELD_ROOT/share/field/.
    field: {
      cpp: 'field_map_provider',
      magnets: [
        {
          name: 'MuonShield',
          volume_pattern: '/SHiP/muon_shield',
          file: 'muon_shield.root',
          map: 'muon_shield',
          translation: [0, 0, 2040],  // shield entrance
        },
        {
          name: 'Spectrometer',
          volume_pattern: '/SHiP/magnet',
          file: 'spectrometer_dipole.root',
          map: 'spectrometer_dipole',
          translation: [0, 0, 89570],  // magnet centre
        },
      ],
    },
  },

  modules: {
    // Geant4 transport of the status-1 particles through geometry and field.
    geant4: {
      cpp: 'geant4_module',
      physics_list: 'FTFP_BERT',
      verbosity: 0,
      seed: seed,
      progress_interval: 100,  // log every N events
    },

    // 'full' writes event_number, event_header, mc_particles, sim_hits and
    // sim_particles per event, plus validation histograms to `histo_file`.
    output: {
      cpp: 'sim_output_module',
      mode: 'full',
      rntuple_file: std.extVar('simout'),
      histo_file: std.extVar('histo'),
    },
  },
}
