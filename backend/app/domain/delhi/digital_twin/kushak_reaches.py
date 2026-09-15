"""Kushak Drainage Reach fixtures for Phase 2B.

Defensive population of DrainageReach objects based on
the final forensic audit (DELHI_KUSHAK_ENGINEERING_GEOMETRY_FINAL_AUDIT.md).
Only length and name are populated from OFFICIAL assertions.
All geometric and hydraulic properties remain UNKNOWN per provenance safety.
"""

from .models import DrainageReach, ProvenanceStatus


# Reach 1: Africa Avenue Underground Box Culvert
kushak_reach_1 = DrainageReach(
    id="kushak_reach_1",
    name="Africa Avenue Underground Box Culvert",
    length_m=2319.0,
    length_provenance=ProvenanceStatus.OFFICIAL,
    width_m=None,
    width_provenance=ProvenanceStatus.UNKNOWN,
    depth_m=None,
    depth_provenance=ProvenanceStatus.UNKNOWN,
    slope_m_per_m=None,
    slope_provenance=ProvenanceStatus.UNKNOWN,
    notes="Underground box culvert; internal hydraulic dimensions unknown."
)


# Reach 2: Open & Deck-Covered Canal
kushak_reach_2 = DrainageReach(
    id="kushak_reach_2",
    name="Open & Deck-Covered Canal",
    length_m=2709.0,
    length_provenance=ProvenanceStatus.OFFICIAL,
    width_m=None,
    width_provenance=ProvenanceStatus.UNKNOWN,
    depth_m=None,
    depth_provenance=ProvenanceStatus.UNKNOWN,
    slope_m_per_m=None,
    slope_provenance=ProvenanceStatus.UNKNOWN,
    notes="Includes bus-depot covered section and open reach; covered deck "
          "width is structural/contextual, not hydraulic clear width; hydraulic "
          "clear geometry remains unknown."
)