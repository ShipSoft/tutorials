// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// ft_replay.jsonnet -- stage 2: the particles of stage 1 through SHiP
// (booklet ch. 7).
//
// Reads the plane_particles that stage 1 recorded behind the hadron absorber
// and tracks them, from where they crossed the plane, through the muon
// shield and the rest of the detector, with the detectors sensitive. Each
// entry of the input becomes one event. This follows aegir's
// workflows/plane_replay.jsonnet, with the detectors, the field maps and
// energy-deposit hits (scoring mode) added.
//
//   phlex -j 4 -c <(jsonnet --tla-str infile=ft_production.root \
//                           --tla-code events=<entries of infile> \
//                           $CODE/workflows/ft_replay.jsonnet)
//
// Top-level arguments:
//   infile  stage-1 output (--tla-str)
//   events  number of entries to replay, at most the entries in infile
//   skip    first entry to replay (default 0)
//   seed    seeds Geant4 (default 42)
//   ecut    kinetic-energy cut in GeV, as in stage 1 (default 0.5)
//   field   true: the muon-shield and spectrometer field maps; false: no field
//   output  output name: writes <output>.root and <output>_validation.root
local stage = 'simulation';

function(infile, events, skip=0, seed=42, ecut=0.5, field=true,
         output='ft_replay') {
  stage: stage,

  driver: {
    cpp: 'generate_layers',
    layers: { event: { total: events } },
  },

  sources: {
    // The particles stage 1 recorded at the plane: status 1 for the tracks as
    // they entered it, other statuses for their ancestry, which Geant4 does
    // not track. The event header is passed on, with original_event_id set
    // to the stage-1 event number.
    input: {
      cpp: 'file_source',
      stage: stage,  // sources need their own copy of the stage name
      input_file: infile,
      ntuple: 'events',
      product: 'plane_particles',
      skip: skip,
    },

    // The SHiP geometry, read through the geometry service, without the
    // stage-1 plane (it would stop every track at once). A logical volume is
    // sensitive if its name *contains* one of the patterns; `detector` gives
    // the SimHit::detector_id that Shannon uses to choose the digitiser.
    geometry: {
      cpp: 'geometry_geomodel_provider',
      db_file: 'ship_geometry.db',
      sensitive_volumes: [
        { pattern: '/SHiP/upstream_tagger/fine_tile', detector: 'UpstreamTagger' },
        { pattern: '/SHiP/upstream_tagger/coarse_tile', detector: 'UpstreamTagger' },
        // LAB cells, and also the aluminium walls of their containers
        { pattern: '/SHiP/decay_volume/sbt/sensors', detector: 'SurroundTagger' },
        { pattern: '/SHiP/trackers/straw_gas', detector: 'StrawTubes' },
        { pattern: '/SHiP/calorimeter/wide_pvt', detector: 'Calorimeter' },
        { pattern: '/SHiP/calorimeter/thin_ps', detector: 'Calorimeter' },
        { pattern: 'HPL_FiberCoreLog', detector: 'Calorimeter' },
        { pattern: '/SHiP/timing_detector/bar', detector: 'TimingDetector' },
      ],
    },

    // Field maps in the SHiP field-map format, each in its magnet's own frame:
    // `translation` (mm) places its origin in the geometry, and the field acts
    // in the logical volumes whose names contain `volume_pattern`. Bare file
    // names are looked up in the current directory, then in
    // $SHIPFIELD_ROOT/share/field/.
    field: if field then {
      cpp: 'field_map_provider',
      magnets: [
        {
          name: 'MuonShield',
          volume_pattern: '/SHiP/muon_shield',
          file: 'muon_shield_TRY_2026.root',
          map: 'muon_shield_TRY_2026',
          translation: [0, 0, 2040],  // shield entrance
        },
        {
          name: 'Spectrometer',
          volume_pattern: '/SHiP/magnet',
          file: 'spectrometer_V21_2455.root',
          map: 'spectrometer_V21_2455',
          translation: [0, 0, 89570],  // magnet centre
        },
        // The same map again for the trackers container, which overlaps the
        // magnet along the beam (Geometry issue #118): a muon in the magnet
        // aperture is found in the trackers volume, and without this entry
        // it would see no field there.
        {
          name: 'SpectrometerInTrackers',
          volume_pattern: '/SHiP/trackers',
          file: 'spectrometer_V21_2455.root',
          map: 'spectrometer_V21_2455',
          translation: [0, 0, 89570],
        },
      ],
    } else { cpp: 'field_null_provider' },
  },

  modules: {
    // Unlike stage 1, the default scoring mode: every step that deposits
    // energy in a sensitive volume becomes a SimHit, which is what Shannon
    // digitises. As in stage 1, tracks below the energy cut are killed.
    // Secondaries below particle_ke_cut are tracked but not written as
    // SimParticles.
    geant4: {
      cpp: 'geant4_module',
      physics_list: 'FTFP_BERT',
      seed: seed,
      sd_mode: 'scoring',
      energy_cut: true,
      energy_cut_threshold: ecut,  // GeV
      particle_ke_cut: 1.0,  // GeV
      regions: { '/SHiP/target': 50, '/SHiP/muon_shield/magn_absorb': 50 },
      progress_interval: 100,
    },

    output: {
      cpp: 'sim_output_module',
      mode: 'full',
      rntuple_file: output + '.root',
      histo_file: output + '_validation.root',
    },
  },
}
