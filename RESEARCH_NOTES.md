# RESEARCH_NOTES.md

## Phase 2.7: Mumbai Rain Mesonet Integration

- [x] Create `MumbaiRainMesonet` adapter to ingest observed rainfall data (15m/1h/24h windows).
- [x] Update provenance models to support new source types (`MESONET`, `NWP_CORRECTED`).
- [x] Implement `CompositeRainfallProvider` hierarchy: Radar -> Mesonet -> NWP (with correction).
- [x] Implement `_apply_bounded_correction` method in `CompositeRainfallProvider`.
- [x] Update `CompositeRainfallProvider.fetch_rainfall` to fetch NWP when Mesonet data is available and apply the correction.
- [ ] Implement tests for station parsing, timestamp alignment, stale observations, missing observations, correction bounds, fallback behavior, and provenance.
- [ ] Verify existing rainfall/flood tests.
