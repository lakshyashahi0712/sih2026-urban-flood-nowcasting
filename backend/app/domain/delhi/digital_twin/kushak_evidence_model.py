"""Evidence-Constrained Kushak Hydraulic Model (Phase 8A).

The first scientifically defensible Kushak model representation that can
run end-to-end through the existing Phase 7D hydraulic engine while
explicitly separating, at every input:

- documented / model-derived information  (OFFICIAL_MODEL_VALUE)
- measured / observed information         (OBSERVED / OFFICIAL)
- effective / inferred parameters         (INFERRED_EFFECTIVE label,
                                           ASSUMED at the engine boundary)
- UNKNOWN / unavailable information       (UNKNOWN, never filled)

This is NOT calibration, NOT ML, and NOT a claim of surveyed or as-built
Kushak geometry. Effective scenario cross-sections are COMPUTATIONAL
EFFECTIVE SCENARIO PROFILES built from documented bounds; every profile
is explicitly named effective/inferred/not-surveyed.

Provenance mapping (no new provenance categories are introduced; the
existing ProvenanceStatus enum and hydraulic_geometry weakest-link rules
are reused):

- DMP longitudinal invert      -> OFFICIAL_MODEL_VALUE
- NGT JIR structural dims      -> OBSERVED/OFFICIAL (visual, bounded)
- NIT52 4.0-5.0 m barrel class -> OFFICIAL + PROCUREMENT_SPECIFICATION
- Effective profile points     -> ASSUMED (profile provenance = ASSUMED
                                  by weakest link; DMP bed elevations
                                  retain OFFICIAL_MODEL_VALUE per point)
- Catchment areas              -> PROVISIONAL / DERIVED
- Unknown rainfall hours       -> UNKNOWN (None), never zero-filled
- Phase 7D16 multipliers       -> INFERRED_EFFECTIVE (scenario label);
                                  engine receives ASSUMED
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .hydraulic_geometry import CrossSectionProfile, StationPoint, profile_provenance
from .hydraulic_integrated_orchestrator import (
    IntegratedRunResult,
    run_integrated_simulation,
)
from .hydraulic_time_state import SimulationState, SimulationStateStatus
from .kushak_rainfall_scenario import load_june_2024_forcing
from .models import ProvenanceStatus

# Repo-rooted evidence artifacts (already acquired; never retyped here).
_CURATED_JSON = (
    Path(__file__).resolve().parents[5]
    / "data" / "delhi" / "raw" / "drainage"
    / "kushak_longitudinal_profile_curated.json"
)
_CHAINAGE_CSV = (
    Path(__file__).resolve().parents[5]
    / "data" / "delhi" / "derived" / "research"
    / "kushak_junction_chainages_digitized.csv"
)


class KushakModelStatus(str, Enum):
    """Explicit model status: runnable-as-scenario is independent of
    blocked as-built claims. A model can be RUNNABLE_AS_SCENARIO while
    still blocked for real/as-built hydraulic claims."""

    RUNNABLE_AS_SCENARIO = "RUNNABLE_AS_SCENARIO"
    PARTIALLY_CONSTRAINED = "PARTIALLY_CONSTRAINED"
    BLOCKED_MISSING_OBSERVATION = "BLOCKED_MISSING_OBSERVATION"
    BLOCKED_MISSING_GEOMETRY = "BLOCKED_MISSING_GEOMETRY"


# ---------------------------------------------------------------------------
# Evidence records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DMPBackboneNode:
    """One DMP 2018 Appendix XII longitudinal backbone node.

    invert provenance is OFFICIAL_MODEL_VALUE: the official
    departmental-record longitudinal geometry as digitized and
    model-corrected by IIT Delhi — NOT a field survey certificate and
    NOT current/as-built geometry.
    """

    junction: str
    profile_name: str
    top_msl_m: float
    old_invert_msl_m: float
    new_invert_msl_m: float
    iitd_corrected: bool
    invert_provenance: ProvenanceStatus = ProvenanceStatus.OFFICIAL_MODEL_VALUE


@dataclass(frozen=True)
class StructuralBound:
    """A current structural bound from an official field record."""

    quantity: str
    value: str
    provenance: ProvenanceStatus
    source: str
    note: str


# NGT Joint Inspection Report, 05-03-2025 (CEs of MCD + I&FC; NGT order
# 09-04-2025). Current/observed structural bounds — visual and bounded,
# never exact hydraulic clear dimensions beyond what is documented.
NGT_JIR_BOUNDS: Tuple[StructuralBound, ...] = (
    StructuralBound(
        quantity="covered_structure_length",
        value="~1000 m (Kushak Bus Depot covered structure)",
        provenance=ProvenanceStatus.OFFICIAL,
        source="NGT Joint Inspection Report 05-03-2025 (CEs MCD + I&FC)",
        note="field inspection; visual/bounded",
    ),
    StructuralBound(
        quantity="total_structure_width",
        value="50 m",
        provenance=ProvenanceStatus.OBSERVED,
        source="NGT Joint Inspection Report 05-03-2025",
        note="observed total width; per-bay width is DERIVED (50/5), not quoted",
    ),
    StructuralBound(
        quantity="bays",
        value="5 equal bays (~10 m each derived)",
        provenance=ProvenanceStatus.OFFICIAL,
        source="NGT Joint Inspection Report 05-03-2025",
        note="bay count observed; ~10 m/bay is derived, not quoted",
    ),
    StructuralBound(
        quantity="visual_depth",
        value="3.5-4.5 m",
        provenance=ProvenanceStatus.OBSERVED,
        source="NGT Joint Inspection Report 05-03-2025",
        note="'as per the visual assessment'; bounds only, not a surveyed depth",
    ),
    StructuralBound(
        quantity="access_openings",
        value="1.5 x 1.5 m @ ~50 m spacing",
        provenance=ProvenanceStatus.OBSERVED,
        source="NGT Joint Inspection Report 05-03-2025",
        note="structural openings; not hydraulic clear dimensions",
    ),
    StructuralBound(
        quantity="silt_chambers",
        value="2.50 x 1.15 m @ ~100 m spacing",
        provenance=ProvenanceStatus.OBSERVED,
        source="NGT Joint Inspection Report 05-03-2025",
        note="structural chambers; not hydraulic clear dimensions",
    ),
    StructuralBound(
        quantity="silt_depth_at_inspection",
        value="1.5-3 ft in all five bays",
        provenance=ProvenanceStatus.OBSERVED,
        source="NGT Joint Inspection Report 05-03-2025",
        note="pre-monsoon 2025 condition; desilting occurred afterwards",
    ),
)

# NDMC NIT52 (52/EE(R-III)/2025-26), work_396329.zip,
# sha256 ba3067a1cae7a331f45f2f98e07d0ef1ed07f955be0d23871dda3028ca7054e0.
# PROCUREMENT_SPECIFICATION ONLY — never as-built geometry.
NIT52_PROCUREMENT = {
    "package": "work_396329.zip",
    "sha256": "ba3067a1cae7a331f45f2f98e07d0ef1ed07f955be0d23871dda3028ca7054e0",
    "spec_class": "PROCUREMENT_SPECIFICATION",
    "provenance": ProvenanceStatus.OFFICIAL,
    "barrel_size_class_m": (4.0, 5.0),
    "note": (
        "covered barrel procurement size class 4.00 m +25% (4.0-5.0 m). "
        "Specification only — NOT as-built geometry. 290 m robotic sonar "
        "silt estimation is a future deliverable, not acquired data; "
        "21,406 m3 desilting is an indirect procurement quantity, not geometry."
    ),
}

# Verified DMP Manning model values (OFFICIAL/MODEL_VALUE, not surveyed).
DMP_MANNING_N = {
    "rcc_box": 0.012,
    "circular_concrete": 0.013,
    "smooth_impervious": 0.014,
    "irregular_open_drain": 0.025,
    "provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
}

# Mapped corridor evidence (mapped/model corridor, not surveyed hydraulics).
MAPPED_CORRIDOR = {
    "total_corridor_m": 5027.56,
    "upstream_mapped_tunnel_m": 2318.5,
    "open_mapped_segments_m": 2709.1,
    "provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
    "note": "OSM/DMP-controlled mapped corridor; mapped/model evidence only",
}


# ---------------------------------------------------------------------------
# Catchment scenarios
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CatchmentScenario:
    """An explicit catchment scenario — DERIVED/PROVISIONAL, never
    authoritative. No silently-chosen 'true' catchment exists."""

    scenario_id: str
    area_km2: float
    provenance: ProvenanceStatus = ProvenanceStatus.PROVISIONAL
    basis: str = ""
    note: str = ""


CATCHMENT_SCENARIOS: Dict[str, CatchmentScenario] = {
    "WORKING_27_66": CatchmentScenario(
        scenario_id="WORKING_27_66",
        area_km2=27.66,
        provenance=ProvenanceStatus.PROVISIONAL,
        basis="DERIVED/PROVISIONAL D8 project watershed (working)",
        note="working watershed; NOT authoritative Kushak catchment",
    ),
    "SENSITIVITY_28_40": CatchmentScenario(
        scenario_id="SENSITIVITY_28_40",
        area_km2=28.40,
        provenance=ProvenanceStatus.PROVISIONAL,
        basis="DERIVED sensitivity result, 3 m burn (kushak_burn_sensitivity_audit)",
        note="sensitivity watershed; NOT authoritative Kushak catchment",
    ),
}
# Historical ~35.4 km2 remains UNRESOLVED — represented only as UNKNOWN.
CATCHMENT_HISTORICAL_KM2: Optional[float] = None  # UNKNOWN, never fabricated


# ---------------------------------------------------------------------------
# Hydraulic scenarios (Phase 7D16 bounded, INFERRED_EFFECTIVE, NOT calibrated)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class KushakHydraulicScenario:
    """One effective hydraulic scenario within the defensible Phase 7D16
    sampled ranges. Every selected value is an INFERRED_EFFECTIVE scenario
    assumption; the source ranges are retained alongside so no selected
    value can be mistaken for an observed or calibrated parameter."""

    scenario_id: str
    mult_box: float
    mult_open: float
    f_open_depot: float
    mult_box_range: Tuple[float, float]
    mult_open_range: Tuple[float, float]
    f_open_depot_range: Tuple[float, float]
    description: str
    basis: str

    @property
    def effective_manning_n_box(self) -> float:
        """n_effective = n_base / multiplier (multiplier = n_base/n_tested
        per the 7D16 provenance basis)."""
        return DMP_MANNING_N["rcc_box"] / self.mult_box

    @property
    def effective_manning_n_open(self) -> float:
        return DMP_MANNING_N["irregular_open_drain"] / self.mult_open


# Phase 7D16 defensible sampled ranges (retained with every scenario).
MULT_BOX_RANGE = (0.800, 0.923)
MULT_OPEN_RANGE = (0.714, 0.893)
F_OPEN_DEPOT_RANGE = (0.400, 1.000)

KUSHAK_HYDRAULIC_SCENARIOS: Dict[str, KushakHydraulicScenario] = {
    "CONSERVATIVE": KushakHydraulicScenario(
        scenario_id="CONSERVATIVE",
        mult_box=0.800,
        mult_open=0.714,
        f_open_depot=0.700,
        mult_box_range=MULT_BOX_RANGE,
        mult_open_range=MULT_OPEN_RANGE,
        f_open_depot_range=F_OPEN_DEPOT_RANGE,
        description=(
            "Lower effective conveyance assumption within the 7D16 range "
            "without imposing the strongest depot blockage."
        ),
        basis=(
            "INFERRED_EFFECTIVE scenario selection at the low ends of the "
            "Phase 7D16 sampled ranges; NOT calibrated, NOT observed."
        ),
    ),
    "CENTRAL": KushakHydraulicScenario(
        scenario_id="CENTRAL",
        mult_box=0.862,
        mult_open=0.804,
        f_open_depot=0.700,
        mult_box_range=MULT_BOX_RANGE,
        mult_open_range=MULT_OPEN_RANGE,
        f_open_depot_range=F_OPEN_DEPOT_RANGE,
        description=(
            "Envelope-midpoint central scenario (7D16 behavioral medians "
            "for the multipliers; mid-range depot open fraction)."
        ),
        basis=(
            "INFERRED_EFFECTIVE central scenario selection (7D16 medians "
            "0.862 / 0.804); explicitly INFERRED/EFFECTIVE, NOT calibrated."
        ),
    ),
    "DEGRADED_CAPACITY": KushakHydraulicScenario(
        scenario_id="DEGRADED_CAPACITY",
        mult_box=0.800,
        mult_open=0.714,
        f_open_depot=0.400,
        mult_box_range=MULT_BOX_RANGE,
        mult_open_range=MULT_OPEN_RANGE,
        f_open_depot_range=F_OPEN_DEPOT_RANGE,
        description=(
            "Lower effective conveyance plus the strongest depot blockage "
            "assumption in the defensible range."
        ),
        basis=(
            "INFERRED_EFFECTIVE scenario selection; f_open_depot=0.400 is "
            "linked explicitly to the NGT JIR 05-03-2025 observed condition "
            "of flow passing through only 2 of 5 bays (2/5 = 0.4) with "
            "1.5-3 ft silt in all bays — observed evidence used as a "
            "scenario bound, NOT a calibrated parameter."
        ),
    ),
}


# ---------------------------------------------------------------------------
# DMP longitudinal backbone (loaded, never retyped)
# ---------------------------------------------------------------------------


def load_dmp_backbone(json_path: Path = _CURATED_JSON) -> List[DMPBackboneNode]:
    """Load the 84-node DMP Appendix XII backbone from the curated JSON.

    The three Kushak profiles (KushakNallah 63 + KushakNalla Part II 17 +
    Kushak Nalla Part II lower 6) with J_5105 / J_6182 shared between
    profiles -> 84 unique nodes. Every invert keeps OFFICIAL_MODEL_VALUE
    provenance; IITD corrections (old != new) are flagged, never hidden.
    """
    with open(json_path, encoding="utf-8") as fh:
        data = json.load(fh)
    profiles = data["ordered_longitudinal_profiles"]
    nodes: List[DMPBackboneNode] = []
    seen = set()
    for name in ("KushakNallah", "KushakNalla Part II", "Kushak Nalla Part II"):
        for entry in profiles[name]:
            jid = entry["junction"]
            if jid in seen:
                continue  # shared junction (J_5105 / J_6182) counted once
            seen.add(jid)
            nodes.append(DMPBackboneNode(
                junction=jid,
                profile_name=name,
                top_msl_m=entry["top_msl_m"],
                old_invert_msl_m=entry["old_invert_msl_m"],
                new_invert_msl_m=entry["new_invert_msl_m"],
                iitd_corrected=entry["old_invert_msl_m"] != entry["new_invert_msl_m"],
            ))
    return nodes


def backbone_slope_m_per_m(
    chainage_csv: Path = _CHAINAGE_CSV,
    upstream_junction: str = "J_3055",
    downstream_junction: str = "J_5105",
) -> Optional[float]:
    """DERIVED reach slope from DMP inverts and digitized chainage.

    (invert_up - invert_dn) / (chainage_dn - chainage_up). Returns None
    (UNKNOWN) if either junction lacks a resolved chainage — never a
    fabricated slope. The digitized chainage carries its own documented
    uncertainty (upstream origin uncertainty is large); the slope is a
    model/derived quantity, not a surveyed gradient.
    """
    found: Dict[str, Tuple[float, float]] = {}
    with open(chainage_csv, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            jid = row["junction"]
            raw = (row["chainage_m"] or "").strip()
            if jid in (upstream_junction, downstream_junction) and raw:
                found.setdefault(jid, (float(raw), float(row["new_invert_m"])))
    if upstream_junction not in found or downstream_junction not in found:
        return None
    (ch_u, inv_u) = found[upstream_junction]
    (ch_d, inv_d) = found[downstream_junction]
    if ch_d <= ch_u:
        return None
    return (inv_u - inv_d) / (ch_d - ch_u)


# ---------------------------------------------------------------------------
# Effective computational scenario profiles (NOT surveyed geometry)
# ---------------------------------------------------------------------------

COVERED_EFFECTIVE_PROFILE_ID = (
    "kushak-covered-INFERRED_EFFECTIVE-NOT_SURVEYED"
)
OPEN_EFFECTIVE_PROFILE_ID = (
    "kushak-open-INFERRED_EFFECTIVE-NOT_SURVEYED"
)


def covered_effective_profile(
    scenario: KushakHydraulicScenario,
    backbone: Optional[List[DMPBackboneNode]] = None,
    width_m: float = 4.5,   # midpoint of NIT52 4.0-5.0 m procurement class
    depth_m: float = 4.0,   # midpoint of NGT JIR 3.5-4.5 m visual depth
) -> Tuple[CrossSectionProfile, Dict[str, object]]:
    """Build the COMPUTATIONAL EFFECTIVE SCENARIO PROFILE for the covered
    reach. NOT surveyed, NOT as-built geometry.

    - Bed elevation = the DMP longitudinal invert at the upstream backbone
      head (J_3055, 216.841 m, OFFICIAL_MODEL_VALUE) — never an arbitrary
      datum such as 100.0 m.
    - Width/depth shape comes from documented class midpoints (NIT52
      procurement class, JIR visual depth); every shape-derived point is
      ASSUMED. Weakest-link profile provenance is therefore ASSUMED.
    - Source evidence is retained in the returned metadata.
    """
    if backbone is None:
        backbone = load_dmp_backbone()
    head = next(n for n in backbone if n.junction == "J_3055")
    bed = head.new_invert_msl_m
    profile = CrossSectionProfile([
        StationPoint(-width_m / 2 - 0.001, bed + depth_m, ProvenanceStatus.ASSUMED),
        StationPoint(-width_m / 2, bed, ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        StationPoint(width_m / 2, bed, ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        StationPoint(width_m / 2 + 0.001, bed + depth_m, ProvenanceStatus.ASSUMED),
    ], cross_section_id=COVERED_EFFECTIVE_PROFILE_ID)
    metadata = {
        "profile_id": COVERED_EFFECTIVE_PROFILE_ID,
        "representation": "COMPUTATIONAL_EFFECTIVE_SCENARIO_PROFILE",
        "is_surveyed": False,
        "is_as_built": False,
        "profile_provenance": profile_provenance(profile).value,
        "bed_elevation_m": bed,
        "bed_source": (
            "DMP 2018 Appendix XII longitudinal invert at J_3055 "
            "(OFFICIAL_MODEL_VALUE; not a survey certificate)"
        ),
        "bed_provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE.value,
        "width_m": width_m,
        "width_basis": "midpoint of NIT52 4.0-5.0 m PROCUREMENT_SPECIFICATION class (OFFICIAL spec, not as-built)",
        "depth_m": depth_m,
        "depth_basis": "midpoint of NGT JIR 3.5-4.5 m visual depth (OBSERVED bounds, not surveyed)",
        "manning_n_effective": scenario.effective_manning_n_box,
        "manning_n_basis": (
            f"DMP RCC box n=0.012 (OFFICIAL_MODEL_VALUE) / mult_box="
            f"{scenario.mult_box} (INFERRED_EFFECTIVE scenario selection)"
        ),
        "scenario_id": scenario.scenario_id,
    }
    return profile, metadata


def open_effective_profile(
    scenario: KushakHydraulicScenario,
    backbone: Optional[List[DMPBackboneNode]] = None,
    bottom_width_m: float = 10.0,  # DMP Part II bottom width (MODEL_VALUE)
    depth_m: float = 3.5,          # model depth class (7D16 R2a section)
) -> Tuple[CrossSectionProfile, Dict[str, object]]:
    """COMPUTATIONAL EFFECTIVE SCENARIO PROFILE for the open reach —
    same rules as the covered profile: bed at a DMP Part II invert
    (J_6182), shape ASSUMED, profile explicitly not-surveyed."""
    if backbone is None:
        backbone = load_dmp_backbone()
    node = next(n for n in backbone if n.junction == "J_6182")
    bed = node.new_invert_msl_m
    profile = CrossSectionProfile([
        StationPoint(-bottom_width_m / 2 - 0.001, bed + depth_m, ProvenanceStatus.ASSUMED),
        StationPoint(-bottom_width_m / 2, bed, ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        StationPoint(bottom_width_m / 2, bed, ProvenanceStatus.OFFICIAL_MODEL_VALUE),
        StationPoint(bottom_width_m / 2 + 0.001, bed + depth_m, ProvenanceStatus.ASSUMED),
    ], cross_section_id=OPEN_EFFECTIVE_PROFILE_ID)
    metadata = {
        "profile_id": OPEN_EFFECTIVE_PROFILE_ID,
        "representation": "COMPUTATIONAL_EFFECTIVE_SCENARIO_PROFILE",
        "is_surveyed": False,
        "is_as_built": False,
        "profile_provenance": profile_provenance(profile).value,
        "bed_elevation_m": bed,
        "bed_source": "DMP 2018 Appendix XII invert at J_6182 (OFFICIAL_MODEL_VALUE)",
        "bed_provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE.value,
        "bottom_width_m": bottom_width_m,
        "bottom_width_basis": "DMP Part II bottom width 10.0 m (OFFICIAL_MODEL_VALUE, template-suspect; shape applied as ASSUMED)",
        "depth_m": depth_m,
        "depth_basis": "model depth class 3.5 m (ASSUMED, 7D16 R2a section)",
        "manning_n_effective": scenario.effective_manning_n_open,
        "manning_n_basis": (
            f"DMP irregular open drain n=0.025 (OFFICIAL_MODEL_VALUE) / "
            f"mult_open={scenario.mult_open} (INFERRED_EFFECTIVE scenario selection)"
        ),
        "scenario_id": scenario.scenario_id,
    }
    return profile, metadata


# ---------------------------------------------------------------------------
# Reach classes
# ---------------------------------------------------------------------------

REACH_CLASSES = {
    "covered_upstream_mapped": {
        "span_m": (0.0, 2318.5),
        "length_m": 2318.5,
        "label": "covered / upstream mapped reach (mapped corridor evidence)",
        "provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        "note": "mapped/model corridor; no hydraulic cross-section inferred from the label",
    },
    "open_reach": {
        "span_m": (2318.5, 3700.0),
        "length_m": 1381.5,
        "label": "open reach (mapped corridor evidence)",
        "provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        "note": "mapped/model corridor; no hydraulic cross-section inferred from the label",
    },
    "bus_depot_constrained": {
        "span_m": (3700.0, 4700.0),
        "length_m": 1000.0,
        "label": "Bus Depot constrained structural reach (NGT JIR structural bounds)",
        "provenance": ProvenanceStatus.OFFICIAL,
        "note": "structural bounds (50 m / 5 bays / silt) are OBSERVED/OFFICIAL; no hydraulic cross-section inferred",
    },
    "remaining_mapped_downstream": {
        "span_m": (4700.0, 5027.56),
        "length_m": 327.56,
        "label": "remaining mapped downstream corridor (mapped corridor evidence)",
        "provenance": ProvenanceStatus.OFFICIAL_MODEL_VALUE,
        "note": "mapped/model corridor; no hydraulic cross-section inferred from the label",
    },
}


# ---------------------------------------------------------------------------
# The model contract
# ---------------------------------------------------------------------------


@dataclass
class KushakEvidenceModel:
    """The Evidence-Constrained Kushak Hydraulic Model.

    Explicitly separates MODEL_VALUE / OBSERVED-OFFICIAL / DERIVED /
    ASSUMED / UNKNOWN / EFFECTIVE-INFERRED inputs. Runnable as an
    evidence-constrained scenario while blocked for real/as-built claims.
    """

    model_id: str = "kushak-evidence-constrained"
    version: str = "8A-v1"
    backbone: List[DMPBackboneNode] = field(default_factory=list)
    status: KushakModelStatus = KushakModelStatus.RUNNABLE_AS_SCENARIO
    blocked_missing_geometry: List[str] = field(default_factory=list)
    blocked_missing_observation: List[str] = field(default_factory=list)
    provenance_summary: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "KushakEvidenceModel":
        """Load the model with its evidence inventory and explicit status.

        Status is RUNNABLE_AS_SCENARIO (the scenario chain runs end-to-end
        on effective profiles) while the blocked lists record what is
        missing for any real/as-built claim:
        - current surveyed bed profile / instrumented cross-sections
        - calibrated roughness (only DMP model values + INFERRED_EFFECTIVE
          scenario multipliers exist)
        - Kushak stage/discharge observations (only downstream Yamuna
          stage and binary waterlogging points exist)
        """
        blocked_geometry = [
            "current surveyed bed profile (Nov-2024 I&FC bathymetric survey output not public)",
            "instrumented cross-sections / NIT-52 drawings (bidder-restricted)",
            "as-built clear hydraulic dimensions (post-2018 desilting state UNKNOWN)",
        ]
        blocked_observation = [
            "Kushak stage/discharge observations (none exist; CWC Yamuna stage is downstream context only)",
            "binary waterlogging registry points carry no depth and mostly no coordinates",
            "continuous hourly rainfall for the June-2024 event (overlap-dependent hours UNKNOWN)",
        ]
        return cls(
            backbone=load_dmp_backbone(),
            status=KushakModelStatus.RUNNABLE_AS_SCENARIO,
            blocked_missing_geometry=blocked_geometry,
            blocked_missing_observation=blocked_observation,
            provenance_summary={
                "dmp_longitudinal_invert": ProvenanceStatus.OFFICIAL_MODEL_VALUE.value,
                "ngt_jir_structural_dimensions": "OBSERVED/OFFICIAL (visual, bounded field evidence)",
                "nit52_barrel_class": "OFFICIAL PROCUREMENT_SPECIFICATION",
                "effective_scenario_profiles": "ASSUMED / INFERRED_EFFECTIVE (NOT surveyed)",
                "catchment": "DERIVED/PROVISIONAL",
                "unknown_rainfall_hours": "UNKNOWN (None, never zero-filled)",
                "phase7d16_multipliers": "INFERRED_EFFECTIVE scenario parameters, not calibrated",
                "mapped_corridor": ProvenanceStatus.OFFICIAL_MODEL_VALUE.value,
                "dmp_manning_n": ProvenanceStatus.OFFICIAL_MODEL_VALUE.value,
            },
        )


# ---------------------------------------------------------------------------
# Scenario runner (feeds the existing Phase 7D engine)
# ---------------------------------------------------------------------------

# Explicit scenario assumption for the event-water-balance runoff
# coefficient (same convention as the 7D-19 scenario; ASSUMED, never
# calibrated).
DEFAULT_RUNOFF_C = 0.75


def run_kushak_evidence_scenario(
    hydraulic_scenario: KushakHydraulicScenario,
    catchment: CatchmentScenario,
    runoff_coefficient: float = DEFAULT_RUNOFF_C,
    initial_storage_m3: float = 10000.0,
    initial_depth_m: float = 1.0,
    forcing=None,
) -> IntegratedRunResult:
    """Run one evidence-constrained scenario through the Phase 7D engine.

    - Forcing is the existing corrected June 28 2024 series
      (kushak_rainfall_scenario.load_june_2024_forcing): the direct
      91.0 mm hour and verified zeros pass through; overlap-dependent
      derived hours are UNKNOWN (None). The engine stops at the first
      UNKNOWN timestep and returns PARTIAL — never zero-filled, never
      interpolated.
    - Catchment is an explicit DERIVED/PROVISIONAL scenario.
    - The hydraulic chain runs on the covered COMPUTATIONAL EFFECTIVE
      SCENARIO PROFILE (bed at the DMP J_3055 invert) with the
      scenario's effective Manning n (INFERRED_EFFECTIVE; ASSUMED at the
      engine boundary) and the DERIVED backbone slope.
    - Resulting states are DERIVED scenario outputs, never observed
      Kushak hydraulic states.
    """
    if forcing is None:
        forcing = load_june_2024_forcing()
    backbone = load_dmp_backbone()
    slope = backbone_slope_m_per_m()
    profile, profile_meta = covered_effective_profile(hydraulic_scenario, backbone)

    initial = SimulationState(
        timestamp=forcing.timesteps[0].start,
        location_id="KUSHAK-EFFECTIVE-SCENARIO",
        status=SimulationStateStatus.COMPUTED,
        stage_m=profile_meta["bed_elevation_m"] + initial_depth_m,
        storage_m3=initial_storage_m3,
        provenance=ProvenanceStatus.DERIVED,
    )

    result = run_integrated_simulation(
        initial_state=initial,
        timesteps=forcing.timesteps,
        rainfall_depth_mm=forcing.depths_mm,
        catchment_area_km2=catchment.area_km2,
        runoff_coefficient=runoff_coefficient,
        profile=profile,
        manning_n=hydraulic_scenario.effective_manning_n_box,
        slope=slope,
        catchment_area_provenance=ProvenanceStatus.PROVISIONAL,
        runoff_coefficient_provenance=ProvenanceStatus.ASSUMED,
        explicit_outflow_m3_s=0.0,
        explicit_outflow_provenance=ProvenanceStatus.ASSUMED,
        lateral_inflow_m3_s=0.0,
        lateral_inflow_provenance=ProvenanceStatus.ASSUMED,
        manning_n_provenance=ProvenanceStatus.ASSUMED,
        slope_provenance=ProvenanceStatus.DERIVED,
        source_id=f"kushak-evidence-{hydraulic_scenario.scenario_id.lower()}",
    )
    result.diagnostics.append(
        "PHASE 8A evidence-constrained scenario: effective profile "
        f"'{profile_meta['profile_id']}' (NOT surveyed/as-built), bed at "
        "DMP J_3055 invert (OFFICIAL_MODEL_VALUE); Manning n "
        f"{hydraulic_scenario.effective_manning_n_box:.4f} = DMP 0.012 / "
        f"mult_box {hydraulic_scenario.mult_box:.3f} (INFERRED_EFFECTIVE, not "
        "calibrated); catchment "
        f"{catchment.area_km2} km2 (DERIVED/PROVISIONAL); states are "
        "DERIVED scenario outputs, never observed Kushak states."
    )
    return result
