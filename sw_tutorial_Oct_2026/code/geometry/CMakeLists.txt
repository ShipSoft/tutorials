# SPDX-FileCopyrightText: 2026 CERN for the benefit of the SHiP Collaboration
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# Geometry tutorial: a GeoModel calorimeter plane from scratch, and a Geant4
# viewer for any GeoModel .db file. Built by `pixi run build`.
cmake_minimum_required(VERSION 3.24)
project(ship_geometry_tutorial LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)  # the geometry service requires C++23
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# --- Part 1: build_calo_plane needs GeoModel only ----------------------------
# The same targets as Geometry/apps/build_geometry.
find_package(GeoModelCore CONFIG REQUIRED)
find_package(GeoModelIO CONFIG REQUIRED)

add_executable(build_calo_plane calo_plane/build_calo_plane.cpp)
target_link_libraries(
    build_calo_plane
    PRIVATE
        GeoModelCore::GeoModelKernel
        GeoModelIO::GeoModelDBManager
        GeoModelIO::GeoModelWrite
)

# --- Part 2: ship_g4view needs Geant4 (with its UI and vis drivers) ---------
# and the SHiP geometry service, which does the GeoModel -> Geant4 conversion.
find_package(Geant4 REQUIRED ui_all vis_all)
find_package(SHiPGeometryService 0.6 CONFIG REQUIRED)

add_executable(ship_g4view viewer/ship_g4view.cpp)
target_link_libraries(
    ship_g4view
    PRIVATE SHiP::GeometryService ${Geant4_LIBRARIES}
)
