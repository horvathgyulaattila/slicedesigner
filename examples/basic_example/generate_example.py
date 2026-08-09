"""Az Alap példaprojekt (examples/basic_example/) reprodukálható generálása.

Lásd: examples/basic_example/README.md és ROADMAP Phase 6, 6.5 tétel.

Legenerálja a forrás STL-t (egy egyszerű henger), lefuttatja a teljes
pipeline-t Dowel-lel (Gap és Backplate nélkül), exportálja a DXF-et, és
elmenti a projektfájlt — mindezt egyetlen, kézi beavatkozás nélküli
lépésként, a ROADMAP Phase 6.9 reprodukálhatósági követelménye szerint.

Futtatás a repó gyökeréből: `uv run python examples/basic_example/generate_example.py`
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
    DowelParams,
    DxfExportParams,
    MeshImportParams,
    NestingParams,
    NumberingParams,
    PipelineConfig,
    SliceParams,
    export_pipeline_result_to_dxf,
    run_pipeline,
)

EXAMPLE_DIR = Path(__file__).parent
STL_PATH = EXAMPLE_DIR / "cylinder.stl"
PROJECT_PATH = EXAMPLE_DIR / "basic_example.json"


def main() -> None:
    # 1. Forrás geometria: egyszerű, álló henger (sugár 50 mm, magasság 60 mm).
    cylinder = trimesh.creation.cylinder(radius=50.0, height=60.0, sections=64)
    cylinder.export(str(STL_PATH), file_type="stl")
    print(f"STL létrehozva: {STL_PATH}")

    # 2. Pipeline-konfiguráció: kizárólag Dowel aktív (legegyszerűbb
    #    működő összeépítési mechanizmus).
    config = PipelineConfig(
        use_dowels=True,
        use_spacers=False,
        use_backplate=False,
        mesh_import=MeshImportParams(file_path=str(STL_PATH)),
        slicing=SliceParams(
            slice_thickness_mm=6.0,
            slice_axis=SliceAxis.Z,
            gap_mm=0.0,
        ),
        dowel=DowelParams(dowel_diameter_mm=6.0),
        numbering=NumberingParams(
            numbering_normal_axis=BackplateNormalAxis.PLUS_Y,
            numbering_direction_axis_sign=NumberingDirectionSign.POSITIVE,
            numbering_height_mm=15.0,
        ),
        nesting=NestingParams(
            material_definitions=(
                MaterialDefinition(
                    material_id="plywood_6mm",
                    thickness_mm=6.0,
                    sheet_width_mm=600.0,
                    sheet_height_mm=400.0,
                    kerf_mm=0.2,
                ),
            ),
            slice_material_id="plywood_6mm",
            seam_marking_height_mm=10.0,
        ),
        dxf_export=DxfExportParams(output_directory=str(EXAMPLE_DIR)),
    )

    # 3. Pipeline futtatása.
    result = run_pipeline(config)
    print(
        f"Pipeline lefutott: {len(result.slice_set.slices)} szelet, "
        f"{len(result.dowel_positions)} Dowel, {len(result.nests)} Nest."
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
