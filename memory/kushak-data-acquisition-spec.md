---
name: kushak-data-acquisition-spec
description: Specification for minimum targeted geometry acquisition for Kushak Nallah hydraulic model.
metadata:
  type: project
---

**Why:** To upgrade physical geometry provenance to OBSERVED/OFFICIAL and resolve Phase 3I P0 geometric blockers for deterministic hydraulic network assembly.

**How to apply:** Implement the following 4-package acquisition plan:

1. **Longitudinal Profile Package:**
   - **Scope:** Full corridor (0.000km to 5.028km).
   - **Requirement:** Surveyed invert elevations at 20m intervals + hydraulic structures/breaks.
   - **Provenance:** OBSERVED (GTS datum).
   - **Uncertainty:** <0.1m.

2. **Cross-Section Package:**
   - **Scope:** CS-01 through CS-07 locations.
   - **Requirement:** Total station survey of bottom width, bank heights, side slopes, material characterization.
   - **Provenance:** OBSERVED.

3. **Africa Avenue Tunnel Package:**
   - **Scope:** Subsurface conduit (Way 44351567).
   - **Requirement:** Internal width/height, invert/soffit elevations at 50m intervals via CCTV/inspection.
   - **Provenance:** OBSERVED.

4. **Structures & Connectivity Package:**
   - **Scope:** All junction chambers, bridges, culverts, outfalls.
   - **Requirement:** Surveyed inlet/outlet inverts, crest levels, vent dimensions. Topological verification of node connections.
   - **Provenance:** OBSERVED.

**Priority Sequence:**
1. **Longitudinal Profile:** Primary invert continuity baseline; fundamental for hydraulic slope.
2. **Structures & Connectivity:** Resolves network topology/node anchors; prevents assembly failures.
3. **Cross-Sections:** Defines conveyance/storage capacity (width/depth); essential for flood routing.
4. **Africa Avenue Tunnel:** Subsurface refinement; secondary bottleneck analysis.

[[kushak-data-acquisition-spec]]
