# Model Identifiability

Method: one-at-a-time sensitivity over the documented parameter ranges on
genuine runtime runs (EV-01 forcing), plus an observation-side
classification. Output: `parameter_sensitivity.csv`.

Finding for every conveyance multiplier
(`mult_box` / `mult_open` / `f_open_depot`):

- Influence channel: the modeled Manning **capacity echo** — which is
  **not computed under current contracts** (capacity requires a stage,
  and stage is UNKNOWN by contract; under the docum
