// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// muon_gun.jsonnet -- an artificial muon sample through the downstream
// detectors (booklet ch. 7).
//
// Muons start on the beam axis at the back of the muon shield, z = 27 m,
// at a small angle to the beam, and are tracked through the decay volume and
// the detectors behind it, with the detectors sensitive. One muon per event.
// The 1000 protons of ch. 6 give too few muons to study the detectors; this
// sample stands in for them. It is not a flux: momenta are flat between
// p_min and p_max and all muons have the same charge.
//
//   phlex -j 4 -c <(jsonnet $CODE/workflows/muon_gun.jsonnet)
//
// Top-level arguments (all optional; --tla-code, output with --tla-str):
//   events     number of muons (default 100)
//   pdg        13 for mu-, -13 for mu+ (default 13)
//   p_min      lowest momentum in GeV (default 10)
//   p_max      highest momentum in GeV (default 100)
//   max_theta  largest angle to the beam in rad (default 0.02)
//   vertex_z   start, in mm (default 27000, the back of the muon shield)
//   seed       seeds the gun and Geant4 (default 42)
//   ecut       kinetic-energy cut in GeV (default 0.5)
//   field      true: the muon-shield and spectrometer field maps; false: no field
//   output     output name: writes <output>.root and <output>_validation.root
local stage = 'simulation';

function(events=100, pdg=13, p_min=10.0, p_max=100.0, max_theta=0.02,
         vertex_z=27000.0, seed=42, ecut=0.5, field=true,
         output='muon_gun') {
  stage: stage,

  driver: {
    cpp: 'generate_layers',
    layers: { event: { total: events } },
  },

  sources: {
    // One muon per event, from (0, 0, vertex_z), with |p| flat in
    // [p_min, p_max], the polar angle flat in [0, max_theta] and the azimuth
    // flat in [0, 2 pi).
    gun: {
      cpp: 'particle_gun_source',
      stage: stage,  // sources need their own copy of the stage name
      pdg: pdg,
      p_min: p_min,  // GeV/c
      p_max: p_max,  // GeV/c
      max_theta: max_theta,  // rad
      vertex_z: vertex_z,  // mm
      seed: seed,
    },

    // The SHiP geometry, read through the geometry service. A logical volume
    // is sensitive if its name *contains* one of the patterns; `detector`
    // gives the SimHit::detector_id that Shannon uses to choose the
    // digitiser.
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
    // Scoring mode: every step that deposits energy in a sensitive volume
    // becomes a SimHit, which is what Shannon digitises. Tracks below the
    // energy cut are killed; secondaries below particle_ke_cut are tracked
    // but not written as SimParticles.
    geant4: {
      cpp: 'geant4_module',
      physics_list: 'FTFP_BERT',
      seed: seed,
      sd_mode: 'scoring',
      energy_cut: true,
      energy_cut_threshold: ecut,  // GeV
      particle_ke_cut: 1.0,  // GeV
      progress_interval: 10,
    },

    output: {
      cpp: 'sim_output_module',
      mode: 'full',
      rntuple_file: output + '.root',
      histo_file: output + '_validation.root',
    },
  },
}
