# Geometry tutorial

Two small programs for the chapter "The detector description" of the SHiP
software tutorial booklet:

- `calo_plane/build_calo_plane.cpp` builds one calorimeter plane with GeoModel
  alone (a 2.16 m x 2.16 m x 1 cm air envelope holding 36 PVT bars of
  2.16 m x 6 cm x 1 cm) and writes it to `calo_plane.db`.
- `viewer/ship_g4view.cpp` opens any GeoModel `.db` file in the Geant4 viewer,
  converting it with the SHiP geometry service as aegir does.

```sh
pixi cvmfs plane        # build calo_plane.db
pixi cvmfs view         # Geant4 window (runs calo_plane.mac)
pixi cvmfs check        # no window: volume tree, mass, overlap test
pixi cvmfs picture      # no window: geometry.png
cp "$SHIP_TUTORIAL/work/ship_geometry.db" .   # the SHiP geometry, from the Geometry chapter
pixi cvmfs view ship.mac  # look at it, one subsystem at a time
```

`ship_g4view [--batch] <file.db | macro.mac> ...` handles its arguments in
order: a `.db` file becomes `/ship/geometry/open <file>`, anything else
`/control/execute <file>`. Without a macro it runs `vis.mac`; without
`--batch` it opens a Qt window and waits for more commands.

On lxplus, use pixi from CVMFS (`pixi cvmfs <task>`), never `pixi run`, which
would install the environment into `.pixi/` on AFS. Organisers create
`pixi.lock` once with `pixi lock` and commit it.
