# Phase 8B Step 2 — Reach-Resolved Effective Profiles + Provenance Ledger

**Status**: IMPLEMENTED (representation only — NO routing)
**Predecessor**: Phase 8B Step 1 (three-tier contract, `kushak_tiered_model.py`)
**Module**: `backend/app/domain/delhi/digital_twin/kushak_reaches_tiered.py`

## 1. What this step adds

The locked Phase 8A single-chain scenario is extended to a reach-resolved
representation of the Kushak corridor. Four model reaches in deterministic
upstream→downstream order, spans copied exactly from Phase 8A
`REACH_CLASSES` (mapped/model corridor):

| Reach | Span (m) | Type | Tier | Profile |
|---|---|---|---|---|
| UG-01 | 0.0 – 2318.5 | COVERED_UNDERGROUND | TIER_B | **none — HYDRAULICALLY_BLOCKED** (conduit geometry UNKNOWN) |
| OC-01 | 2318.5 – 3700.0 | OPEN | TIER_B | `kushak-oc01-open-INFERRED_EFFECTIVE-NOT_SURVEYED` |
| CD-01 | 3700.0 – 4700.0 | COVERED_BAY_CONSTRAINED | TIER_B | `kushak-cd01-covered-INFERRED_EFFECTIVE-NOT_SURVEYED` |
| OC-02 | 4700.0 – 5027.56 | OPEN | TIER_B | `kushak-oc02-open-INFERRED_EFFECTIVE-NOT_SURVEYED` |

- `KushakModelReach` validates finite chainages, end > start; and
  `validate_reach_ordering` enforces a contiguous corridor (no silent
  overlaps/gaps).
- `build_reach_effective_profile` reuses the locked Phase 8A profile
  builders (`open_effective_profile` for OC-01/OC-02,
  `covered_effective_profile` for CD-01). UG-01 cannot be built — calling
  with UG-01 raises; no effective profile may be invented for it.
- `build_provenance_ledger` is a deterministic per-reach ledger
  (reach_id, quantity, value/reference, provenance class, tier, source,
  status, note) distinguishing: DMP backbone → `OFFICIAL_MODEL_VALUE`;
  NGT JIR bounds → OBSERVED/OFFICIAL (indirect, bounded); NIT52 4–5 m →
  `PROCUREMENT_SPECIFICATION`; multipliers → INFERRED_EFFECTIVE/ASSUMED;
  catchment → DERIVED/PROVISIONAL; UG-01 geometry and downstream boundary
  → UNKNOWN/blocked (`value=None`, never filled).

## 2. Scientific rules preserved

- All reach profiles are EFFECTIVE SCENARIO PROFILES — `is_surveyed=False`,
  `is_as_built=False`, aggregate provenance ASSUMED.
- NIT52 remains PROCUREMENT_SPECIFICATION (never measured geometry);
  DMP data remains OFFICIAL_MODEL_VALUE (never "current geometry").
- Tier A remains satisfiable ONLY by explicit
  `SurveyEvidenceClass.OFFICIAL_SURVEY_OBSERVED` / `OFFICIAL_AS_BUILT`
  (locked Step 1); current real Kushak evidence stays Tier C.
- UNKNOWN stays UNKNOWN: UG-01 barrel geometry and the downstream
  boundary stage are `None`, never fabricated.

## 3. Intentionally not implemented (later steps)

No routing, no serial flow propagation, no continuity, no timestep
changes, no new Manning equations, no calibration, no rainfall changes,
no ML, no lateral inflow, no downstream boundary assumption, no
UI/API changes.

## 4. Validation

```
python -m pytest -q app/domain/delhi/digital_twin/test_kushak_reaches_tiered.py \
  app/domain/delhi/digital_twin/test_kushak_tiered_model.py \
  app/domain/delhi/digital_twin/test_kushak_evidence_model.py -p no:warnings
```

Result: **56 passed, 0 failed** (18 Step-2 + 17 Step-1 + 21 Phase 8A).
