"""Koordinációs réteg: a rögzített engine-pipeline feltételes végrehajtása.

A három, egymástól független Project-szintű kapcsoló (``use_spacers``,
``use_dowels``, ``use_backplate``) és a hozzájuk tartozó feltételes
pipeline-végrehajtás — lásd ADR-0004, ARCHITECTURE.md 3-4. szakasz.

Ez a modul kizárólag orchestrál: rögzített sorrendben, feltételesen hívja a
`slicedesigner.engines` alatti, változatlan publikus engine-függvényeket, és
továbbítja közöttük az adatot. Geometriai vagy üzleti számítást nem
tartalmaz (ARCHITECTURE.md 4. szakasz).
"""

import logging
from dataclasses import dataclass
from typing import Literal, TypeVar

from slicedesigner.engines.backplate_engine import (
    Backplate,
    BackplateNormalAxis,
    NonBackplateIsland,
    SliceTabOverride,
    Tab,
    apply_backplate,
    place_backplate_tabs,
)
from slicedesigner.engines.dowel_engine import (
    DowelPosition,
    ManualDowelPosition,
    apply_dowels,
)
from slicedesigner.engines.dxf_export_engine import Export, export_nests_to_dxf
from slicedesigner.engines.gap_engine import Spacer, apply_gap
from slicedesigner.engines.mesh_import import Mesh, import_mesh
from slicedesigner.engines.nesting_engine import (
    MaterialDefinition,
    Nest,
    NestingRotationMode,
    create_nests,
    prepare_nesting_parts,
)
from slicedesigner.engines.numbering_engine import (
    NumberingDirectionSign,
    SliceNumberingOverride,
    apply_numbering,
    apply_numbering_to_backplate,
)
from slicedesigner.engines.slice_engine import SliceAxis, SliceSet, create_slice_set
from slicedesigner.project.exceptions import PipelineConfigurationError

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


@dataclass(frozen=True)
class MeshImportParams:
    """A Mesh Import engine (`import_mesh()`) kívülről állítandó paraméterei."""

    file_path: str
    origin_alignment: Literal["none"] = "none"
    min_plausible_size_mm: float = 1.0
    max_plausible_size_mm: float = 3000.0


@dataclass(frozen=True)
class SliceParams:
    """A Slice Engine (`create_slice_set()`) kívülről állítandó paraméterei.

    A `mesh` bemenetet (a Mesh Import kimenete) a pipeline maga adja át,
    nem e paraméter-objektum része.
    """

    slice_thickness_mm: float
    slice_axis: SliceAxis = SliceAxis.Z
    gap_mm: float = 0.0
    max_scale_tolerance: float = 0.02


@dataclass(frozen=True)
class DowelParams:
    """A Dowel Engine (`apply_dowels()`) kívülről állítandó paraméterei.

    A `slice_set` bemenetet a pipeline maga adja át.
    """

    dowel_diameter_mm: float
    spacer_diameter_mm: float = 0.0
    min_edge_clearance_mm: float | None = None
    dowel_count_per_region: int = 3
    min_dowels_per_region: int = 1
    blind_hole_cap_mm: float | None = None
    manual_dowel_positions: tuple[ManualDowelPosition, ...] = ()


@dataclass(frozen=True)
class GapParams:
    """A Gap Engine (`apply_gap()`) kívülről állítandó paraméterei.

    A `slice_set` bemenetet a pipeline maga adja át; a `dowel_positions`-t a
    pipeline a Dowel Engine (ha lefutott) kimenetéből tölti ki.
    """

    spacer_diameter_mm: float
    spacer_count_per_gap: int = 3
    min_spacers_per_region: int = 1


@dataclass(frozen=True)
class BackplateParams:
    """A Backplate Engine (`apply_backplate()`) kívülről állítandó paraméterei.

    A `slice_set` bemenetet a pipeline maga adja át.
    """

    backplate_normal_axis: BackplateNormalAxis
    backplate_thickness_mm: float
    tab_length_mm: float
    backplate_plane_tolerance_mm: float = 0.1
    backplate_margin_mm: float = 0.0
    tab_spacing_mm: float = 700.0
    tab_edge_margin_mm: float | None = None
    slice_tab_overrides: tuple[SliceTabOverride, ...] = ()
    non_backplate_islands: tuple[NonBackplateIsland, ...] = ()
    material_reference: str | None = None


@dataclass(frozen=True)
class NumberingParams:
    """A Numbering Engine (`apply_numbering()`) kívülről állítandó paraméterei.

    A `slice_set` bemenetet a pipeline maga adja át. Ha a Backplate Engine
    lefutott, a pipeline ugyanezen `numbering_height_mm`/
    `numbering_min_height_mm`/`numbering_margin_mm` értékekkel hívja meg a
    Backplate-oldali jelölést (`apply_numbering_to_backplate()`) is.
    """

    numbering_normal_axis: BackplateNormalAxis
    numbering_direction_axis_sign: NumberingDirectionSign
    numbering_height_mm: float
    numbering_min_height_mm: float | None = None
    numbering_margin_mm: float | None = None
    slice_numbering_overrides: tuple[SliceNumberingOverride, ...] = ()


@dataclass(frozen=True)
class NestingParams:
    """A Nesting Engine (`prepare_nesting_parts()` + `create_nests()`) paraméterei.

    A `slice_set`, `backplate` és `spacers` bemeneteket a pipeline maga adja
    át — kikapcsolt `use_backplate`/`use_spacers` esetén a
    `backplate_material_id`/`spacer_material_id` sem kerül átadásra a
    Nesting Engine-nek, függetlenül attól, hogy e mezők milyen értéket
    kaptak.
    """

    material_definitions: tuple[MaterialDefinition, ...]
    slice_material_id: str
    seam_marking_height_mm: float
    backplate_material_id: str | None = None
    spacer_material_id: str | None = None
    nesting_rotation_mode: NestingRotationMode = NestingRotationMode.ORTHOGONAL
    seam_marking_min_height_mm: float | None = None
    seam_marking_margin_mm: float | None = None


@dataclass(frozen=True)
class DxfExportParams:
    """A DXF Export Engine (`export_nests_to_dxf()`) kívülről állítandó paraméterei.

    A `nests` bemenetet (a Nesting Engine kimenete) a pipeline maga adja át.
    """

    output_directory: str
    dxf_version: str = "R12"
    cut_layer_name: str = "CUT"
    cut_layer_color: int = 1
    engrave_layer_name: str = "ENGRAVE"
    engrave_layer_color: int = 5
    output_filename_pattern: str = "{material_id}_sheet{sheet_number}"


@dataclass(frozen=True)
class PipelineConfig:
    """A teljes pipeline-futtatás bemenete: a három kapcsoló és az engine-paraméterek.

    A `dowel`/`gap`/`backplate` kizárólag akkor kötelező (nem lehet
    `None`), ha a megfelelő kapcsoló (`use_dowels`/`use_spacers`/
    `use_backplate`) igaz — ellenkező esetben `run_pipeline()`
    `PipelineConfigurationError`-t dob.
    """

    use_dowels: bool
    use_spacers: bool
    use_backplate: bool
    mesh_import: MeshImportParams
    slicing: SliceParams
    numbering: NumberingParams
    nesting: NestingParams
    dxf_export: DxfExportParams
    dowel: DowelParams | None = None
    gap: GapParams | None = None
    backplate: BackplateParams | None = None


@dataclass(frozen=True)
class PipelineResult:
    """A teljes pipeline-futtatás kimenete: minden lépés releváns eredménye.

    A `backplate` `None`, ha `use_backplate` hamis volt; a
    `dowel_positions`/`spacers` üres, ha a megfelelő kapcsoló hamis volt.
    """

    mesh: Mesh
    slice_set: SliceSet
    dowel_positions: tuple[DowelPosition, ...]
    spacers: tuple[Spacer, ...]
    backplate: Backplate | None
    nests: tuple[Nest, ...]
    exports: tuple[Export, ...]


def _require_params(params: _T | None, *, switch_name: str, params_name: str) -> _T:
    """Bekapcsolt kapcsolóhoz tartozó kötelező paraméter-objektum ellenőrzése."""
    if params is None:
        raise PipelineConfigurationError(
            f"A(z) '{switch_name}' kapcsoló be van kapcsolva, de a hozzá tartozó "
            f"'{params_name}' paraméter (PipelineConfig.{params_name}) nincs megadva."
        )
    return params


def _validate_config(config: PipelineConfig) -> None:
    """Konfiguráció-teljességi előfeltétel a pipeline indítása előtt (ADR-0004).

    Emellett, ha `use_dowels` és `use_spacers` is igaz, és mindkét
    paraméter-objektum meg van adva, a Dowel Engine és a Gap Engine saját
    `spacer_diameter_mm` értékének egyeznie kell (DOWEL_SYSTEM_SPEC.md és
    GAP_SYSTEM_SPEC.md 5. szakasz: "az egyeztetés a Project felelőssége").
    """
    if not (config.use_dowels or config.use_spacers or config.use_backplate):
        raise PipelineConfigurationError(
            "Legalább egy összeépítési kapcsolónak (use_dowels, use_spacers, "
            "use_backplate) be kell kapcsolva lennie."
        )

    # Lebegőpontos zajszűrési küszöb (nem üzleti tűréshatár) a "meg kell
    # egyeznie" szabály közvetlen (==) egyenlőségvizsgálat nélküli
    # kiértékeléséhez (CODING_STANDARDS.md 7. szakasz).
    _spacer_diameter_equality_epsilon_mm = 1e-9
    if (
        config.use_dowels
        and config.use_spacers
        and config.dowel is not None
        and config.gap is not None
        and abs(config.dowel.spacer_diameter_mm - config.gap.spacer_diameter_mm)
        > _spacer_diameter_equality_epsilon_mm
    ):
        raise PipelineConfigurationError(
            "A DowelParams.spacer_diameter_mm "
            f"({config.dowel.spacer_diameter_mm}) nem egyezik a "
            f"GapParams.spacer_diameter_mm értékével "
            f"({config.gap.spacer_diameter_mm}) — DOWEL_SYSTEM_SPEC.md és "
            "GAP_SYSTEM_SPEC.md 5. szakasz szerint a Project felelőssége "
            "ezek egyeztetése."
        )


def import_mesh_preview(params: MeshImportParams) -> Mesh:
    """A Mesh Import engine (`import_mesh()`) önálló hívása GUI-előnézethez.

    Kizárólag a `import_mesh()` hívását végzi el, a `params` mezőit
    ugyanúgy szétbontva, ahogy `run_pipeline()` is teszi a mesh-import
    lépésben — más engine-t nem hív, azon felül nem validál, amit maga az
    `import_mesh()` már elvégez. Ez a függvény kizárólag GUI-előnézet
    célra készült (a fájlválasztás utáni azonnali 3D megjelenítéshez), és
    nem helyettesíti a `run_pipeline()`-on belüli tényleges mesh-importot.

    Args:
        params: a Mesh Import engine kívülről állítandó paraméterei.

    Returns:
        A betöltött és validált Mesh.

    Raises:
        SliceDesignerError: az `import_mesh()` saját, dokumentált kivétele
            (pl. `InvalidMeshError`) — változatlanul továbbterjed.
    """
    return import_mesh(
        file_path=params.file_path,
        origin_alignment=params.origin_alignment,
        min_plausible_size_mm=params.min_plausible_size_mm,
        max_plausible_size_mm=params.max_plausible_size_mm,
    )


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """A rögzített engine-pipeline feltételes, végponttól-végpontig futtatása.

    Lásd a modul-docstringet és ADR-0004: a `config.use_dowels`/
    `use_spacers`/`use_backplate` kapcsolók alapján a Dowel/Gap/Backplate
    Engine feltételesen fut le; a többi lépés mindig lefut.

    Args:
        config: a pipeline teljes bemenete (kapcsolók + engine-paraméterek).

    Returns:
        A pipeline minden lépésének releváns kimenete.

    Raises:
        PipelineConfigurationError: mindhárom kapcsoló ki van kapcsolva,
            vagy egy bekapcsolt kapcsolóhoz nem tartozik paraméter-objektum.
        SliceDesignerError: bármelyik meghívott engine saját, dokumentált
            kivétele (pl. `InvalidMeshError`, `InvalidSliceError`) —
            változatlanul továbbterjed (fail-fast).
    """
    _validate_config(config)

    mesh = import_mesh(
        file_path=config.mesh_import.file_path,
        origin_alignment=config.mesh_import.origin_alignment,
        min_plausible_size_mm=config.mesh_import.min_plausible_size_mm,
        max_plausible_size_mm=config.mesh_import.max_plausible_size_mm,
    )

    slice_set = create_slice_set(
        mesh,
        slice_thickness_mm=config.slicing.slice_thickness_mm,
        slice_axis=config.slicing.slice_axis,
        gap_mm=config.slicing.gap_mm,
        max_scale_tolerance=config.slicing.max_scale_tolerance,
    )

    dowel_positions: tuple[DowelPosition, ...] = ()
    if config.use_dowels:
        dowel_params = _require_params(
            config.dowel, switch_name="use_dowels", params_name="dowel"
        )
        slice_set, dowel_positions = apply_dowels(
            slice_set,
            dowel_diameter_mm=dowel_params.dowel_diameter_mm,
            spacer_diameter_mm=dowel_params.spacer_diameter_mm,
            min_edge_clearance_mm=dowel_params.min_edge_clearance_mm,
            dowel_count_per_region=dowel_params.dowel_count_per_region,
            min_dowels_per_region=dowel_params.min_dowels_per_region,
            blind_hole_cap_mm=dowel_params.blind_hole_cap_mm,
            manual_dowel_positions=dowel_params.manual_dowel_positions,
        )

    spacers: tuple[Spacer, ...] = ()
    if config.use_spacers:
        gap_params = _require_params(
            config.gap, switch_name="use_spacers", params_name="gap"
        )
        slice_set, spacers = apply_gap(
            slice_set,
            spacer_diameter_mm=gap_params.spacer_diameter_mm,
            dowel_positions=dowel_positions,
            spacer_count_per_gap=gap_params.spacer_count_per_gap,
            min_spacers_per_region=gap_params.min_spacers_per_region,
        )

    backplate: Backplate | None = None
    backplate_tabs: tuple[Tab, ...] = ()
    if config.use_backplate:
        backplate_params = _require_params(
            config.backplate, switch_name="use_backplate", params_name="backplate"
        )
        pre_backplate_slice_set = slice_set
        slice_set, backplate = apply_backplate(
            slice_set,
            backplate_normal_axis=backplate_params.backplate_normal_axis,
            backplate_thickness_mm=backplate_params.backplate_thickness_mm,
            tab_length_mm=backplate_params.tab_length_mm,
            backplate_plane_tolerance_mm=backplate_params.backplate_plane_tolerance_mm,
            backplate_margin_mm=backplate_params.backplate_margin_mm,
            tab_spacing_mm=backplate_params.tab_spacing_mm,
            tab_edge_margin_mm=backplate_params.tab_edge_margin_mm,
            slice_tab_overrides=backplate_params.slice_tab_overrides,
            non_backplate_islands=backplate_params.non_backplate_islands,
            material_reference=backplate_params.material_reference,
        )
        # apply_backplate() a csap-pozíciókat (Tab-lista) nem adja vissza,
        # csak a velük már kiegészített Slice Set-et és a Backplate-et — a
        # Backplate-oldali numbering-hez (apply_numbering_to_backplate())
        # szükséges Tab-lista előállításához place_backplate_tabs()
        # ugyanazon, dokumentált paraméterekkel, ugyanazon (Backplate előtti)
        # Slice Set-en újra meghívásra kerül; determinisztikus engine-ek
        # mellett (CODING_STANDARDS.md 7. szakasz) ez ugyanazt a Tab-listát
        # adja, mint amit apply_backplate() belsőleg már felhasznált.
        _, backplate_tabs = place_backplate_tabs(
            pre_backplate_slice_set,
            backplate_normal_axis=backplate_params.backplate_normal_axis,
            backplate_thickness_mm=backplate_params.backplate_thickness_mm,
            tab_length_mm=backplate_params.tab_length_mm,
            backplate_plane_tolerance_mm=backplate_params.backplate_plane_tolerance_mm,
            tab_spacing_mm=backplate_params.tab_spacing_mm,
            tab_edge_margin_mm=backplate_params.tab_edge_margin_mm,
            slice_tab_overrides=backplate_params.slice_tab_overrides,
            non_backplate_islands=backplate_params.non_backplate_islands,
        )

    slice_set = apply_numbering(
        slice_set,
        numbering_normal_axis=config.numbering.numbering_normal_axis,
        numbering_direction_axis_sign=config.numbering.numbering_direction_axis_sign,
        numbering_height_mm=config.numbering.numbering_height_mm,
        numbering_min_height_mm=config.numbering.numbering_min_height_mm,
        numbering_margin_mm=config.numbering.numbering_margin_mm,
        slice_numbering_overrides=config.numbering.slice_numbering_overrides,
    )

    if backplate is not None:
        backplate = apply_numbering_to_backplate(
            slice_set,
            backplate,
            backplate_tabs,
            numbering_height_mm=config.numbering.numbering_height_mm,
            numbering_min_height_mm=config.numbering.numbering_min_height_mm,
            numbering_margin_mm=config.numbering.numbering_margin_mm,
        )

    parts_by_material = prepare_nesting_parts(
        slice_set,
        material_definitions=config.nesting.material_definitions,
        slice_material_id=config.nesting.slice_material_id,
        seam_marking_height_mm=config.nesting.seam_marking_height_mm,
        backplate=backplate if config.use_backplate else None,
        backplate_material_id=(
            config.nesting.backplate_material_id if config.use_backplate else None
        ),
        spacers=spacers if config.use_spacers else (),
        spacer_material_id=(
            config.nesting.spacer_material_id if config.use_spacers else None
        ),
        nesting_rotation_mode=config.nesting.nesting_rotation_mode,
        seam_marking_min_height_mm=config.nesting.seam_marking_min_height_mm,
        seam_marking_margin_mm=config.nesting.seam_marking_margin_mm,
    )

    nests = create_nests(
        parts_by_material,
        material_definitions=config.nesting.material_definitions,
        nesting_rotation_mode=config.nesting.nesting_rotation_mode,
    )

    exports = export_nests_to_dxf(
        nests,
        output_directory=config.dxf_export.output_directory,
        dxf_version=config.dxf_export.dxf_version,
        cut_layer_name=config.dxf_export.cut_layer_name,
        cut_layer_color=config.dxf_export.cut_layer_color,
        engrave_layer_name=config.dxf_export.engrave_layer_name,
        engrave_layer_color=config.dxf_export.engrave_layer_color,
        output_filename_pattern=config.dxf_export.output_filename_pattern,
    )

    return PipelineResult(
        mesh=mesh,
        slice_set=slice_set,
        dowel_positions=dowel_positions,
        spacers=spacers,
        backplate=backplate,
        nests=nests,
        exports=exports,
    )
