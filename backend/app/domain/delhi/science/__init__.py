"""Scientific evaluation framework for the Delhi/Kushak system.

Subpackages/modules:
- observation_registry: machine-readable registry of ALL historical
  observations with tier classification and usability gating.
- metrics: pure metric functions (rainfall/stage/discharge/extent/
  occurrence) that refuse inadequate inputs.
- validation: evidence-sufficiency gate + event-separated evaluation.
- calibration: parameter bounds registry, objective gate, GLUE-style
  behavioral screening, anti-overfitting audit.
- identifiability: one-at-a-time sensitivity on real model runs.
- uncertainty: uncertainty decomposition per event.
- ml_pipeline: physics-guided ML augmentation (residual/probability),
  event-grouped evaluation, production gating, model registry.

SCIENTIFIC CONTRACT: the physics digital twin remains the sole
authoritative model. Every capability here is additive, optional, and
gated by evidence sufficiency; anything unsupported is reported
NOT_COMPUTABLE with its reason rather than fabricated.
"""
