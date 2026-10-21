// SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
// SPDX-License-Identifier: LGPL-3.0-or-later
//
// ship_g4view.cpp -- look at any GeoModel .db file with the Geant4 viewer.
//
// The file is converted to Geant4 by the SHiP geometry service, exactly as
// aegir does before a simulation, so what you see is what Geant4 simulates.
// Everything is driven by Geant4 macro commands; this program adds one:
//
//   /ship/geometry/open <file.db>      choose the geometry (before /run/initialize)
//
// Usage:
//   ship_g4view [--batch] <file.db | macro.mac> ...
//
// Each argument is handled in order: a .db file becomes
// "/ship/geometry/open <file>", anything else "/control/execute <file>".
// Without a macro argument, vis.mac (in the current directory) is executed.
// Without --batch, a Qt window opens and stays open for more commands.

#include <G4ApplicationState.hh>
#include <G4Event.hh>
#include <G4Exception.hh>
#include <G4Geantino.hh>
#include <G4LogicalVolume.hh>
#include <G4PVPlacement.hh>
#include <G4ParticleGun.hh>
#include <G4PhysListFactory.hh>
#include <G4RunManager.hh>
#include <G4RunManagerFactory.hh>
#include <G4SystemOfUnits.hh>
#include <G4ThreeVector.hh>
#include <G4UIExecutive.hh>
#include <G4UIcmdWithAString.hh>
#include <G4UIdirectory.hh>
#include <G4UImanager.hh>
#include <G4UImessenger.hh>
#include <G4VUserActionInitialization.hh>
#include <G4VUserDetectorConstruction.hh>
#include <G4VUserPrimaryGeneratorAction.hh>
#include <G4VisExecutive.hh>

#include <SHiP/GeometryService/GeometryService.h>
#include <filesystem>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

namespace {

// ---- The detector: whatever the .db file contains ---------------------------
class DbDetectorConstruction final : public G4VUserDetectorConstruction {
   public:
    void setFile(const std::string& path) { m_path = path; }

    G4VPhysicalVolume* Construct() override {
        if (m_path.empty()) {
            G4Exception(
                "DbDetectorConstruction", "ShipView001", FatalException,
                "no geometry: give a .db file, or /ship/geometry/open <file.db> "
                "before /run/initialize");
        }
        if (!std::filesystem::exists(m_path)) {
            G4Exception("DbDetectorConstruction", "ShipView002", FatalException,
                        ("no such file: " + m_path).c_str());
        }
        // GeoModel -> Geant4, as in aegir's geometry_geomodel_provider.cpp.
        // geant4WorldLogical() throws if the conversion fails.
        auto service = SHiP::GeometryService::fromFile(m_path);
        G4LogicalVolume& worldLV = service->geant4WorldLogical();
        // The service returns the world's logical volume; Geant4 wants it placed.
        // The converted Geant4 volumes belong to the Geant4 stores, so the
        // GeoModel tree (the service) may go when this function returns.
        return new G4PVPlacement(nullptr, G4ThreeVector(), &worldLV,
                                 worldLV.GetName(), nullptr, false, 0);
    }

   private:
    std::string m_path;
};

// ---- The one SHiP command: /ship/geometry/open ------------------------------
class GeometryMessenger final : public G4UImessenger {
   public:
    explicit GeometryMessenger(DbDetectorConstruction& detector)
        : m_detector(detector) {
        m_shipDir = std::make_unique<G4UIdirectory>("/ship/");
        m_shipDir->SetGuidance("SHiP tutorial commands.");
        m_geometryDir = std::make_unique<G4UIdirectory>("/ship/geometry/");
        m_geometryDir->SetGuidance("Choose the GeoModel geometry to look at.");
        m_open = std::make_unique<G4UIcmdWithAString>("/ship/geometry/open", this);
        m_open->SetGuidance("Read the geometry from a GeoModel .db file.");
        m_open->SetGuidance("Must come before /run/initialize.");
        m_open->SetParameterName("file", false);
        m_open->AvailableForStates(G4State_PreInit);
    }

    void SetNewValue(G4UIcommand* command, G4String value) override {
        if (command == m_open.get()) {
            m_detector.setFile(value);
            std::cout << "ship_g4view: geometry " << value << "\n";
        }
    }

   private:
    DbDetectorConstruction& m_detector;
    std::unique_ptr<G4UIdirectory> m_shipDir;
    std::unique_ptr<G4UIdirectory> m_geometryDir;
    std::unique_ptr<G4UIcmdWithAString> m_open;
};

// ---- Something to shoot, for /run/beamOn: a particle gun --------------------
// Geantinos by default (they interact with nothing, so their tracks show the
// geometry); change it with /gun/particle, /gun/energy, /gun/position ...
class Gun final : public G4VUserPrimaryGeneratorAction {
   public:
    Gun() : m_gun(1) {
        m_gun.SetParticleDefinition(G4Geantino::Definition());
        m_gun.SetParticleEnergy(1 * GeV);
        m_gun.SetParticlePosition(G4ThreeVector(0, 0, -400 * mm));
        m_gun.SetParticleMomentumDirection(G4ThreeVector(0, 0, 1));
    }
    void GeneratePrimaries(G4Event* event) override {
        m_gun.GeneratePrimaryVertex(event);
    }

   private:
    G4ParticleGun m_gun;
};

class Actions final : public G4VUserActionInitialization {
   public:
    void Build() const override { SetUserAction(new Gun()); }
};

bool isDbFile(const std::string& arg) {
    return std::filesystem::path(arg).extension() == ".db";
}

}  // namespace

int main(int argc, char* argv[]) {
    bool batch = false;
    std::vector<std::string> commands;
    bool haveMacro = false;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--batch") {
            batch = true;
        } else if (arg == "-h" || arg == "--help") {
            std::cout << "usage: ship_g4view [--batch] <file.db | macro.mac> ...\n";
            return 0;
        } else if (isDbFile(arg)) {
            commands.push_back("/ship/geometry/open " + arg);
        } else {
            commands.push_back("/control/execute " + arg);
            haveMacro = true;
        }
    }
    if (!haveMacro) {
        if (batch) {
            std::cerr << "ship_g4view: --batch needs a macro to run\n";
            return 1;
        }
        commands.emplace_back("/control/execute vis.mac");
    }

    // The window must exist before any /vis command runs.
    std::unique_ptr<G4UIExecutive> window;
    if (!batch)
        window = std::make_unique<G4UIExecutive>(argc, argv, "qt");

    // One thread is plenty to look at a geometry. Like aegir, the run manager is
    // never deleted: Geant4 and GeoModel tear down their stores at exit.
    auto* runManager =
        G4RunManagerFactory::CreateRunManager(G4RunManagerType::Serial);
    auto* detector = new DbDetectorConstruction();
    GeometryMessenger messenger(*detector);
    runManager->SetUserInitialization(detector);
    runManager->SetUserInitialization(
        G4PhysListFactory().GetReferencePhysList("FTFP_BERT"));
    runManager->SetUserInitialization(new Actions());

    G4VisExecutive visManager("warnings");
    visManager.Initialize();

    auto* ui = G4UImanager::GetUIpointer();
    for (const auto& command : commands) {
        std::cout << "ship_g4view: " << command << "\n";
        if (ui->ApplyCommand(command) != 0) {
            std::cerr << "ship_g4view: command failed: " << command << "\n";
            return 1;
        }
    }

    if (window)
        window->SessionStart();
    return 0;
}
