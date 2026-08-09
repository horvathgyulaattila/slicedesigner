"""Az Összetett példaprojekt (examples/complex_example/) reprodukálható generálása.

Lásd: examples/complex_example/README.md és ROADMAP Phase 6, 6.6 tétel.

Legenerálja a forrás STL-t (egy egyszerű téglatest), lefuttatja a teljes
pipeline-t mindhárom opcionális összeépítési mechanizmussal (Dowel, Gap,
Backplate) egyszerre, exportálja a DXF-eket, és elmenti a projektfájlt —
mindezt egyetlen, kézi beavatkozás nélküli lépésként, a ROADMAP Phase 6.9
reprodukálhatósági követelménye szerint.

Futtatás a repó gyökeréből: `uv run python examples/complex_example/generate_example.py`
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
STL_PATH = EXAMPLE_DIR / "box.stl"
PROJECT_PATH = EXAMPLE_DIR / "complex_example.json"


def main() -> None:
    # 1. Forrás geometria: téglatest, 100x60x80 mm (X x Y x Z).
    box = trimesh.creation.box(extents=(100.0, 60.0, 80.0))
    box.export(str(STL_PATH), file_type="stl")
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
            gap_mm=4.0,
        ),
        dowel=DowelParams(dowel_diameter_mm=6.0, spacer_diameter_mm=20.0),
        gap=GapParams(spacer_diameter_mm=20.0),
        backplate=BackplateParams(
            backplate_normal_axis=BackplateNormalAxis.PLUS_X,
            backplate_thickness_mm=6.0,
            tab_length_mm=15.0,
        ),
        numbering=NumberingParams(
            numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=15.0,
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
                    material_id="plywood_4mm",
                    thickness_mm=4.0,
                    sheet_width_mm=600.0,
                    sheet_height_mm=400.0,
                    kerf_mm=0.2,
                ),
            ),
            slice_material_id="plywood_10mm",
            backplate_material_id="plywood_6mm",
            spacer_material_id="plywood_4mm",
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
