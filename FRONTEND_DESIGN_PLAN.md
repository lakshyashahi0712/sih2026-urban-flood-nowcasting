# FloodNowcast Frontend Design Plan

## Subject Matter Analysis
**Product**: Urban Flood Nowcast System for Emergency Operations Center
**Audience**: Emergency operators, civil engineers, disaster management officials during active flood events
**Primary Job**: Provide rapid situational awareness and decision support for evacuation routes, resource allocation, and public warnings during 0-3 hour flood outlook and historical event analysis

## Design Token System

### Color Palette
Inspired by monsoon hydrology and emergency visibility requirements:

- **Base Neutrals** (for operational clarity under stress):
  - `--monsoon-deep`: #0a1a2f (Deep water/night - replaces navy topbar)
  - `--monsoon-mid`: #1e3a5f (Water depth indicator)
  - `--monsoon-shallow`: #3b6a8f (Shallow water/transition)
  - `--monsoon-surface`: #e6f0f5 (Water surface reflection - background)
  - `--alert-clear`: #ffffff (Maximum legibility)

- **Hydrological Data Encoding** (replaces generic blue accent):
  - `--flow-velocity`: #2563eb (Water movement - primary interactive elements)
  - `--infiltration`: #059669 (Soil absorption - secondary actions)
  - `--surface-runoff`: #dc2626 (Overland flow - warnings/critical)
  - `--groundwater`: #7c3aed (Subsurface - informational)
  - `--evaporation`: #f59e0b (Flux dissipation - metrics)

- **Flood Depth Encoding** (scientifically distinctive, replaces generic YORB):
  - `--depth-0`: #f0f9ff (No water - nearly white with blue tint)
  - `--depth-0-25`: #e0f2fe (Ankle-deep)
  - `--depth-0-5`: #bae6fd (Calf-deep - action threshold)
  - `--depth-1.0`: #7dd3fc (Waist-deep - evacuation consideration)
  - `--depth-1.5`: #38bdf8 (Chest-deep - high risk)
  - `--depth-2.0`: #0ea5e9 (Head-deep - extreme danger)
  - `--depth-3.0+`: #0284c7 (Submerged - critical infrastructure)

- **Emergency Semantics** (reserved for alerts only):
  - `--alert-imminent`: #dc2626 (Flash flood imminent)
  - `--alert-active`: #ea580c (Flooding occurring)
  - `--alert-recording`: #16a34a (Monitoring active)

### Typography
**Primary Typeface**: Inter (optimized for technical data and emergency readability)
- **Display/Headings**: Inter SemiBold 600 (clear hierarchy without aggression)
- **Body/Data**: Inter Regular 400 (optimal for rapid scanning of metrics)
- **Numeric**: Space Mono (monospace for precise data alignment in popups/tables)
- **Scale**: Based on 4px grid with 1.5 ratio (4, 6, 8, 10, 12, 14, 16, 20, 24, 32, 40, 48, 64)

### Layout Concept
**Operational Dashboard Priorities**:
1. **Immediate Threat Assessment** (top-center glance value)
2. **Spatial Context** (map as primary canvas)
3. **Actionable Intelligence** (left panel: timeline, resources, threats)
4. **Validation & Provenance** (right panel: ground truth, model confidence)

**Spatial Organization**:
```
+--------------------------------------------------+
| TOP BAR: System ID | LOCATION | MODE STATUS     |
+------------------+------------------+-----------------+
| MAP VIEW (70%)   | LEFT PANEL (30%) |                 |
|                  | TIMELINE         |                 |
|                  | STATUS CARDS     |                 |
|                  | RESOURCES        |                 |
+------------------+------------------+-----------------+
| LEGEND           |                  | PROVENANCE      |
+--------------------------------------------------+
```

**Alignment**: Left-aligned for operational consistency (emergency protocols favor left-to-right scanning), numeric data right-aligned within containers for comparison.

### Design Principles
1. **Hydrological Honesty**: Visual encoding follows water physics principles (depth = opacity/value, flow = direction/motion)
2. **Emergency Legibility**: Critical information perceivable in <3 seconds under stress (high contrast, size hierarchy)
3. **Scene Integrity**: Map remains primary focus - UI elements recede unless active
4. **Decision Confidence**: Clear visualization of uncertainty (provenance, model skill, validation gaps)
5. **Monsoon Context**: Design respects Mumbai's cultural relationship with rain (reverence, not fear)

## Review Against Generic Defaults

**Avoided Defaults**:
- ❌ No warm cream background → using water-reflective surface with hydrological depth encoding
- ❌ No single accent color → multi-dimensional color encoding for different water processes
- ❌ No broadsheet layout → operational dashboard prioritizing map + threat assessment
- ❌ No SaaS-card kit → elevation-based panel system with hydraulic pressure metaphor
- ❌ No tracked-out ALL-CAPS eyebrow → technical labels in sentence case with meaningful abbreviations
- ❌ No meta strings with middle dots → clear operational language
- ❌ No 'WORD — fragment' labels → complete descriptive phrases
- ❌ No tinted near-black → true neutrals with water-inspired depth
- ❌ No monospace for small data → reserved for precise alignment where needed

**Distinctive Choices Made**:
- ✅ Color encodes hydrological processes (not just aesthetic)
- ✅ Typography hierarchy supports rapid technical comprehension
- ✅ Layout follows emergency decision flow: threat → location → action → validation
- ✅ Design grounded in Mumbai monsoon context and flood physics