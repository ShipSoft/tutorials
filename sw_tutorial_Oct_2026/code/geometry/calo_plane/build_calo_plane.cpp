// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// build_calo_plane.cpp -- GeoModel from scratch: one calorimeter plane.
//
// A 2.16 m x 2.16 m x 1 cm air container filled with 36 scintillator bars of
// 2.16 m x 6 cm x 1 cm, built the way the SHiP calorimeter builds its
// scintillator layers (Geometry/subsystems/Calorimeter), but with nothing
// from the SHiP geometry library: only GeoModel. Written to a .db file that
// the Geant4 viewer (../viewer) opens like the full SHiP geometry.
//
//   build_calo_plane [output.db]        (default: calo_plane.db)

#include <GeoModelDBManager/GMDBManager.h>
#include <GeoModelKernel/GeoBox.h>
#include <GeoModelKernel/GeoElement.h>
#include <GeoModelKernel/GeoLogVol.h>
#include <GeoModelKernel/GeoMaterial.h>
#include <GeoModelKernel/GeoNameTag.h>
#include <GeoModelKernel/GeoPhysVol.h>
#include <GeoModelKernel/GeoTransform.h>
#include <GeoModelKernel/Units.h>
#include <GeoModelWrite/WriteGeoModel.h>

#include <filesystem>
#include <iostream>
#include <string>

namespace GU = GeoModelKernelUnits;

namespace {

// ---- STEP 0: the dimensions (full lengths, in mm) ---------------------------
constexpr double kPlaneXY = 2160.0;  // container: 2.16 m x 2.16 m ...
constexpr double kPlaneZ = 10.0;     // ... x 1 cm
constexpr double kBarWidth = 60.0;   // bar: 2.16 m x 6 cm x 1 cm
constexpr int kNBars = static_cast<int>(kPlaneXY / kBarWidth);  // 36 bars
constexpr double kWorldXY = 3000.0;  // a world box around the plane
constexpr double kWorldZ = 1000.0;

struct Materials {
    GeoMaterial* air;
    GeoMaterial* pvt;
};

// ---- STEP 1: elements and materials -----------------------------------------
// An element has a name, a symbol, Z and the molar mass; a material has a
// density and its elements' mass fractions, and must be locked when complete.
Materials makeMaterials() {
    auto* hydrogen = new GeoElement("Hydrogen", "H", 1, 1.008 * GU::g / GU::mole);
    auto* carbon = new GeoElement("Carbon", "C", 6, 12.011 * GU::g / GU::mole);
    auto* nitrogen = new GeoElement("Nitrogen", "N", 7, 14.007 * GU::g / GU::mole);
    auto* oxygen = new GeoElement("Oxygen", "O", 8, 15.999 * GU::g / GU::mole);
    auto* argon = new GeoElement("Argon", "Ar", 18, 39.948 * GU::g / GU::mole);

    auto* air = new GeoMaterial("Air", 1.29e-3 * GU::g / GU::cm3);
    air->add(nitrogen, 0.755);
    air->add(oxygen, 0.231);
    air->add(argon, 0.014);
    air->lock();

    // Polyvinyltoluene, (C9H10)n, the plastic scintillator of the wide bars
    const double molarMass = 9 * 12.011 + 10 * 1.008;
    auto* pvt = new GeoMaterial("PVT", 1.032 * GU::g / GU::cm3);
    pvt->add(carbon, 9 * 12.011 / molarMass);
    pvt->add(hydrogen, 10 * 1.008 / molarMass);
    pvt->lock();

    return {air, pvt};
}

GeoPhysVol* buildPlane(const Materials& materials) {
    // ---- STEP 2: the container ----------------------------------------------
    // Shape (GeoBox takes HALF-lengths) + name + material = logical volume;
    // a physical volume is one placed instance of it.
    auto* containerShape = new GeoBox(
        0.5 * kPlaneXY * GU::mm, 0.5 * kPlaneXY * GU::mm, 0.5 * kPlaneZ * GU::mm);
    // As in the SHiP calorimeter, an air envelope's name ends in "_env".
    auto* containerLog =
        new GeoLogVol("/tutorial/calo_plane_env", containerShape, materials.air);
    auto* container = new GeoPhysVol(containerLog);

    // ---- STEP 3: one bar ----------------------------------------------------
    // Long in x, 6 cm in y, as thick as the container: an "h" bar, like
    // /SHiP/calorimeter/wide_pvt_h. All 36 bars share this one logical
    // volume; only their positions differ.
    auto* barShape = new GeoBox(0.5 * kPlaneXY * GU::mm, 0.5 * kBarWidth * GU::mm,
                                0.5 * kPlaneZ * GU::mm);
    auto* barLog =
        new GeoLogVol("/tutorial/calo_plane/wide_pvt_h", barShape, materials.pvt);

    // ---- STEP 4: place the bars ---------------------------------------------
    // For each bar: a name tag, a transform, then the physical volume. They
    // apply to the next volume added to the same mother.
    const double firstBarY = -0.5 * (kNBars - 1) * kBarWidth;  // centred on 0
    for (int i = 0; i < kNBars; ++i) {
        const double y = firstBarY + i * kBarWidth;
        container->add(
            new GeoNameTag("/tutorial/calo_plane/bar_" + std::to_string(i)));
        container->add(new GeoTransform(GeoTrf::Translate3D(0, y * GU::mm, 0)));
        container->add(new GeoPhysVol(barLog));
    }
    return container;
}

// ---- STEP 5: a world around the plane ---------------------------------------
GeoPhysVol* buildWorld(const Materials& materials, GeoPhysVol* plane) {
    auto* worldShape = new GeoBox(0.5 * kWorldXY * GU::mm, 0.5 * kWorldXY * GU::mm,
                                  0.5 * kWorldZ * GU::mm);
    auto* world = new GeoPhysVol(new GeoLogVol("World", worldShape, materials.air));
    world->add(new GeoNameTag("/tutorial/calo_plane"));
    world->add(new GeoTransform(GeoTrf::Translate3D(0, 0, 0)));
    world->add(plane);
    return world;
}

}  // namespace

int main(int argc, char* argv[]) {
    const std::string output = argc > 1 ? argv[1] : "calo_plane.db";

    const Materials materials = makeMaterials();
    GeoPhysVol* plane = buildPlane(materials);
    GeoPhysVol* world = buildWorld(materials, plane);
    std::cout << "plane: " << plane->getNChildVols() << " bars of " << kPlaneXY
              << " x " << kBarWidth << " x " << kPlaneZ << " mm\n";

    // ---- STEP 6: write the tree to a GeoModel database ----------------------
    if (std::filesystem::exists(output))
        std::filesystem::remove(
            output);  // start from an empty file, as build_geometry does
    GMDBManager db(output);
    GeoModelIO::WriteGeoModel writer(db);
    world->exec(&writer);
    writer.saveToDB();
    std::cout << "wrote " << output << "\n";
    return 0;
}
