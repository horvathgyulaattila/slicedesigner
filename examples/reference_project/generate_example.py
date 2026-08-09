"""A Teljes referencia projekt (examples/reference_project/) reprodukálható generálása.

Lásd: examples/reference_project/README.md és ROADMAP Phase 6, 6.8 tétel.

Legenerálja a forrás STL-t (egy "kapu"-formájú, három összefűzött
téglatestből álló modell — két láb és egy felső gerenda), lefuttatja a
teljes pipeline-t mindhárom opcionális összeépítési mechanizmussal (Dowel,
Gap, Backplate) egyszerre, exportálja a DXF-eket, és elmenti a
projektfájlt — mindezt egyetlen, kézi beavatkozás nélküli lépésként, a
ROADMAP Phase 6.9 reprodukálhatósági követelménye szerint.

Futtatás a repó gyökeréből: `uv run python examples/reference_project/generate_example.py`
"""

from __future__ import annotations

from pathlib import Path

import trimesh

from slicedesigner.engines.backplate_engine import BackplateNormalAxis
from slicedesigner.engines.nesting_engine import MaterialDefinition
from slicedesigner.engines.numbering_engine import NumberingDirectionSign
from slicedesigner.engines.slice_engine import SliceAxis
from slicedesigner.project.persistence import load_project_config, save_project_config
from slicedesigner.project.pipeline import (
    BackplateParams,
    DowelParams,
    DxfExportParams,
    GapParams,
    MeshImportParams,
    NestingParams,
    NumberingParams,
    PipelineConfig,
    SliceParams,
    export_pipeline_result_to_dxf,
    run_pipeline,
)

EXAMPLE_DIR = Path(__file__).parent
STL_PATH = EXAMPLE_DIR / "gate.stl"
PROJECT_PATH = EXAMPLE_DIR / "reference_project.json"


def main() -> None:
    # 1. Forrás geometria: "kapu"-forma, három téglatestből — két láb
    #    (egyenként 30x40x72 mm) és egy felső gerenda (120x40x22 mm), amely
    #    a lábakon nyugszik. A lábak belső éle (a "kapunyílás" felőli
    #    oldalon) a gerenda alsó lapjának *belsejében* végződik (T-illesztés)
    #    — egy egyszerű trimesh.util.concatenate() ezt csak érintkező, nem
    #    ténylegesen összeforrasztott lapokként kezelné, ami a mesh-import
    #    lépés csúcspont-összevonása (vertex merge) után non-manifold
    #    geometriát eredményezne, amin a Backplate Engine belső Boole-
    #    metszete (lásd README.md, "Tervezési döntések — eltérés az eredeti
    #    tervtől") elhasal. Ezért a három téglatestet valódi, egyetlen
    #    watertight szilárd testté Boole-unióval (trimesh.boolean.union(),
    #    a projekt már meglévő manifold3d függősége) egyesítjük.
    leg_extents = (30.0, 40.0, 72.0)
    leg_left = trimesh.creation.box(extents=leg_extents)
    leg_left.apply_translation((-45.0, 0.0, 36.0))
    leg_right = trimesh.creation.box(extents=leg_extents)
    leg_right.apply_translation((45.0, 0.0, 36.0))
    beam = trimesh.creation.box(extents=(120.0, 40.0, 22.0))
    beam.apply_translation((0.0, 0.0, 83.0))
    gate = trimesh.boolean.union([leg_left, leg_right, beam])
    gate.export(str(STL_PATH), file_type="stl")
    print(f"STL létrehozva: {STL_PATH}")

    # 2. Pipeline-konfiguráció: Dowel + Gap + Backplate egyszerre aktív.
    config = PipelineConfig(
        use_dowels=True,
        use_spacers=True,
        use_backplate=True,
        mesh_import=MeshImportParams(file_path=str(STL_PATH)),
        slicing=SliceParams(
            slice_thickness_mm=10.0,
            slice_axis=SliceAxis.Z,
            gap_mm=2.0,
        ),
        dowel=DowelParams(dowel_diameter_mm=6.0, spacer_diameter_mm=10.0),
        gap=GapParams(spacer_diameter_mm=10.0),
        backplate=BackplateParams(
            backplate_normal_axis=BackplateNormalAxis.PLUS_Y,
            backplate_thickness_mm=6.0,
            tab_length_mm=8.0,
        ),
        numbering=NumberingParams(
            numbering_normal_axis=BackplateNormalAxis.MINUS_Y,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=8.0,
        ),
        nesting=NestingParams(
            material_definitions=(
                MaterialDefinition(
                    material_id="plywood_10mm",
                    thickness_mm=10.0,
                    sheet_width_mm=600.0,
                    sheet_height_mm=400.0,
                    kerf_mm=0.2,
                ),
                MaterialDefinition(
                    material_id="plywood_6mm",
                    thickness_mm=6.0,
                    sheet_width_mm=600.0,
                    sheet_height_mm=400.0,
                    kerf_mm=0.2,
                ),
                MaterialDefinition(
                    material_id="plywood_2mm",
                    thickness_mm=2.0,
                    sheet_width_mm=600.0,
                    sheet_height_mm=400.0,
                    kerf_mm=0.2,
                ),
            ),
            slice_material_id="plywood_10mm",
            backplate_material_id="plywood_6mm",
            spacer_material_id="plywood_2mm",
            seam_marking_height_mm=10.0,
        ),
        dxf_export=DxfExportParams(output_directory=str(EXAMPLE_DIR)),
    )

    # 3. Pipeline futtatása.
    result = run_pipeline(config)
    print(
        f"Pipeline lefutott: {len(result.slice_set.slices)} szelet, "
        f"{len(result.dowel_positions)} Dowel, {len(result.spacers)} Spacer, "
        f"Backplate: {'igen' if result.backplate is not None else 'nem'}, "
        f"{len(result.nests)} Nest."
    )

    # 4. DXF export (a Futtatástól leválasztott, önálló lépés — ADR-0009).
    exports = export_pipeline_result_to_dxf(result.nests, config.dxf_export)
    print(f"DXF export kész: {len(exports)} fájl.")
    for export in exports:
        print(f"  - {export.filename}")

    # 5. Projekt mentése.
    save_project_config(config, str(PROJECT_PATH))
    print(f"Projektfájl elmentve: {PROJECT_PATH}")

    # 6. Reprodukálhatósági ellenőrzés (ROADMAP 6.9): a mentett projektfájl
    #    ténylegesen visszatölthető.
    reloaded = load_project_config(str(PROJECT_PATH))
    assert reloaded == config
    print("Projektfájl visszatöltése ellenőrizve — OK.")


if __name__ == "__main__":
    main()
