// Typed API client for the Delhi/Kushak V2 backend surface.
// All calls are relative (same-origin) — the Vite dev server proxies /api
// to the backend, and in production the app is served behind the same host.

// ---------------------------------------------------------------------------
// Shared provenance vocabulary (mirrors the backend's explicit state model)
// ---------------------------------------------------------------------------

export type OperationalStatus =
  | 'COMPUTED'
  | 'EXECUTED'
  | 'NOT_EXECUTED'
  | 'BLOCKED_MISSING_FORCING'
  | 'UNAVAILABLE'
  | 'STALE'
  | 'UNKNOWN';

// ---------------------------------------------------------------------------
// Status
// ---------------------------------------------------------------------------

export interface DelhiStatus {
  system: string;
  generated_at: string;
  objective: string;
  components: {
    reach_chain: { reach_ids: string[]; total_length_m: number; order: string };
    ensemble: { member_count: number; axes: Record<string, string[]>; deterministic: boolean };
    historical_events: {
      catalogued: number;
      executable: string[];
      canonical_validation_events: string[];
    };
    nowcast: {
      reference_point: string;
      latitude: number;
      longitude: number;
      forcing: string;
      horizon_hours: number;
    };
  };
  capabilities: string[];
  explicit_non_claims: string[];
}

// ---------------------------------------------------------------------------
// Ensemble
// ---------------------------------------------------------------------------

export interface EnsembleMember {
  member_id: string;
  hydraulic_scenario: {
    id: string;
    mult_box: number;
    mult_open: number;
    f_open_depot: number;
    mult_box_range: [number, number];
    mult_open_range: [number, number];
    f_open_depot_range: [number, number];
    provenance: string;
    description: string;
  };
  catchment_scenario: {
    id: string;
    area_km2: number;
    provenance: string;
    basis: string;
    note: string;
  };
  runoff_coefficient: { value: number; provenance: string };
  description: string;
}

export interface EnsembleResponse {
  member_count: number;
  deterministic: boolean;
  construction: string;
  members: EnsembleMember[];
}

// ---------------------------------------------------------------------------
// Network
// ---------------------------------------------------------------------------

export interface NetworkReach {
  reach_id: string;
  start_chainage_m: number;
  end_chainage_m: number;
  length_m: number;
  reach_type: string;
  label: string;
  tier: string;
  provenance: string;
  hydraulic_status: string;
  profile_reference: string | null;
  note: string | null;
}

export interface NetworkResponse {
  order: string[];
  terminal_reach: string;
  total_length_m: number;
  catchment_note: string;
  reaches: NetworkReach[];
}

// ---------------------------------------------------------------------------
// Events + replay
// ---------------------------------------------------------------------------

// 28B replay status vocabulary (from the declarative event manifest)
export type ReplayStatus = 'EXECUTABLE' | 'PARTIAL' | 'UNKNOWN' | 'CONTROL';

export interface EventCatalogEntry {
  event_id: string;
  canonical_event_id: string | null;
  event_window: string;
  qualification: string;
  rainfall_resolution: string;
  operational_state: string;
  evidence_notes: string;
  replay_status: ReplayStatus;
  executable_status: string;
  replay_claim: string;
  observation_status: string;
  spatial_attribution_status: string;
  forcing: {
    available: boolean;
    availability: string;
    forcing_id: string | null;
    bins: string | null;
  };
  preserved_final_classification: string | null;
  runtime_replay_available: boolean;
}

export interface EventsResponse {
  catalog_size: number;
  executable_event_ids: string[];
  partial_event_ids: string[];
  events: EventCatalogEntry[];
}

export interface ReplayForcingBin {
  lead_hour: number;
  depth_mm: number | null;
  units: string;
  provenance: string;
}

export interface ChainStepReach {
  reach_id: string;
  hydraulic_status: string;
  storage_m3: number | null;
  stage_m: number | null;
  incoming_flow_m3_s: number | null;
  actual_outflow_m3_s: number | null;
  transferred_m3_s: number | null;
  capacity_m3_s: number | null;
  balance_residual_m3_s: number | null;
}

export interface ChainStep {
  time_start: string | null;
  time_end: string | null;
  reaches: ChainStepReach[];
  classifications: {
    reach_id: string;
    classification: string;
    status: string;
    provenance: string;
    tier: string;
  }[];
}

export interface ReplayMember {
  member_id: string;
  inflow_conversion_status: string;
  inflow_steps: { time: string; discharge_m3_s: number | null }[];
  inflow_volume_m3: number | null;
  chain_steps: ChainStep[];
  validation: {
    event_id: string | null;
    source_class: string;
    validation_result: string;
    temporal_match: string;
    spatial_match: string;
    timestamp_precision: string;
    result_provenance: string;
    diagnostic: string;
  };
  diagnostics: string[];
}

export interface EventReplayResponse {
  event_id: string;
  canonical_event_id: string | null;
  event_window: string;
  rainfall_resolution: string;
  operational_state: string;
  observed_empirical_outcome: string;
  qualification: string;
  evidence_notes: string;
  cwc_state: string;
  generated_at: string;
  runtime_status: 'EXECUTED' | 'PARTIAL_EXECUTED' | 'NOT_EXECUTED';
  replay_status?: ReplayStatus;
  executable_status?: string;
  replay_claim?: string;
  reason?: string;
  forcing?: {
    forcing_id: string;
    anchor_start: string | null;
    bins: ReplayForcingBin[];
    resolution_preserved: boolean;
    note: string;
  } | null;
  ensemble_size?: number;
  members?: ReplayMember[];
  counters?: Record<string, number>;
  integrity_checks?: Record<string, string>;
  claim_policy: string;
}

// 28C replay artifact (reproducible record; separated from operational outputs)
export interface ReplayArtifact {
  artifact_schema: string;
  event_id: string;
  resolved_event_id: string;
  event_window: string;
  forcing_source: string | null;
  forcing_resolution: string;
  forcing_provenance: string;
  forcing_timesteps:
    | {
        index: number;
        time_start: string;
        time_end: string;
        duration_hours: number;
        depth_mm: number | null;
        provenance: string;
      }[]
    | [];
  ensemble_members: string[];
  runtime_status: string;
  hydraulic_states: Record<string, Record<string, unknown>[]>;
  routing_states: Record<string, Record<string, unknown>[]>;
  uncertainty_states: Record<string, unknown>;
  validation_status: Record<string, unknown>;
  observation_matches: Record<string, unknown>[];
  unknown_intervals: Record<string, unknown>[];
  blocked_intervals: Record<string, unknown>[];
  generation_timestamp: string;
  repository_revision: string;
  replay_claim: string;
  reason?: string;
}

export interface ReplaySummaryRecord {
  event_id: string;
  resolved_event_id: string;
  event_window: string;
  rainfall_resolution: string;
  operational_state: string;
  observed_empirical_outcome: string;
  forcing_found: string;
  runtime_executed: string;
  ensemble_members_executed: number;
  chain_timesteps_executed: number;
  validation_calls: number;
  runtime_model_state: string;
  mass_balance_check: string;
  final_classification: string;
}

export interface ReplaySummaryResponse {
  generated_at: string;
  records: ReplaySummaryRecord[];
  system_flags: Record<string, string>;
  verdict: string;
  claim_policy: string;
}

// ---------------------------------------------------------------------------
// Nowcast
// ---------------------------------------------------------------------------

export interface ForecastBin {
  time_start: string;
  time_end: string;
  depth_mm: number | null;
  provenance: string;
}

export interface NowcastMember {
  member_id: string;
  hydraulic_scenario_id: string;
  catchment_scenario_id: string;
  runoff_coefficient: number;
  inflow_status: string;
  inflow_steps: { time: string; discharge_m3_s: number | null }[];
  inflow_volume_m3: number | null;
  reach_states: Record<
    string,
    {
      time_start: string;
      time_end: string;
      hydraulic_status: string;
      storage_m3: number | null;
      stage_m: number | null;
      incoming_flow_m3_s: number | null;
      actual_outflow_m3_s: number | null;
      transferred_downstream_m3_s: number | null;
      balance_residual_m3_s: number | null;
    }[]
  >;
  classifications: {
    reach_id: string;
    classification: string;
    status: string;
    provenance: string;
  }[][];
  diagnostics: string[];
}

export interface NowcastResponse {
  status: OperationalStatus;
  generated_at: string;
  forecast: {
    status: OperationalStatus;
    source: string;
    reference_point: string;
    latitude: number;
    longitude: number;
    acquired_at: string | null;
    bins: ForecastBin[];
    diagnostics: string[];
  };
  envelope_inflow: {
    time_start: string;
    time_end: string;
    forecast_depth_mm: number | null;
    min_m3_s: number | null;
    median_m3_s: number | null;
    max_m3_s: number | null;
    computed_members: number;
    unknown_members: number;
  }[];
  members: NowcastMember[];
  diagnostics: string[];
  horizon_note: string;
  claim_policy: string;
  drainage_loading?: EdgeLoading[];
  depth_estimates?: Record<string, DepthEstimate>;
  surface?: SurfaceResponse | { status: string; reason?: string };
}

// ---------------------------------------------------------------------------
// Geo layers
// ---------------------------------------------------------------------------

export interface GeoLayerResponse {
  layer_id: string;
  label: string;
  provenance: string;
  source_path: string;
  feature_count: number;
  geojson: unknown;
}

export interface LayersResponse {
  layers: { layer_id: string; label: string; provenance: string }[];
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, { signal });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body && typeof body.detail === 'string') detail = body.detail;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

export const delhiApi = {
  getStatus: (signal?: AbortSignal) => getJson<DelhiStatus>('/api/delhi/status', signal),
  getEnsemble: (signal?: AbortSignal) => getJson<EnsembleResponse>('/api/delhi/ensemble', signal),
  getNetwork: (signal?: AbortSignal) => getJson<NetworkResponse>('/api/delhi/network', signal),
  getEvents: (signal?: AbortSignal) => getJson<EventsResponse>('/api/delhi/events', signal),
  getEventReplay: (eventId: string, refresh = false, signal?: AbortSignal) =>
    getJson<EventReplayResponse>(
      `/api/delhi/events/${encodeURIComponent(eventId)}/replay${refresh ? '?refresh=true' : ''}`,
      signal,
    ),
  getEventDepth: (eventId: string, timestepIndex: number, signal?: AbortSignal) =>
    getJson<{
      event_id: string;
      mode: string;
      step: { max_depth_cm: number | null; flooded_cells: number; flood_state: string; depth_cells: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[]; depth_polygons?: { type: string; features: unknown[] }; source_type: string };
      claim_policy: string;
    }>(
      `/api/delhi/events/${encodeURIComponent(eventId)}/depth?timestep_index=${timestepIndex}`,
      signal,
    ),
  getEventArtifact: (eventId: string, signal?: AbortSignal) =>
    getJson<ReplayArtifact>(
      `/api/delhi/events/${encodeURIComponent(eventId)}/artifact`,
      signal,
    ),
  getReplaySummary: (signal?: AbortSignal) =>
    getJson<ReplaySummaryResponse>('/api/delhi/replay/summary', signal),
  getNowcast: (refresh = false, signal?: AbortSignal) =>
    getJson<NowcastResponse>(`/api/delhi/nowcast${refresh ? '?refresh=true' : ''}`, signal),
  getGeoLayer: (layerId: string, signal?: AbortSignal) =>
    getJson<GeoLayerResponse>(`/api/delhi/geo/${encodeURIComponent(layerId)}`, signal),
  getLayers: (signal?: AbortSignal) => getJson<LayersResponse>('/api/delhi/layers', signal),
  getSafeRoute: (params: SafeRouteParams, signal?: AbortSignal) => {
    const q = new URLSearchParams({
      origin_lon: String(params.origin[0]),
      origin_lat: String(params.origin[1]),
      dest_lon: String(params.destination[0]),
      dest_lat: String(params.destination[1]),
      mode: params.mode,
      departure_hour: String(params.departure_hour ?? 0),
      timestep_index: String(params.timestep_index ?? 0),
    });
    if (params.event_id) q.set('event_id', params.event_id);
    return getJson<SafeRouteResponse>(`/api/delhi/safe-route?${q.toString()}`, signal);
  },
  getModelScience: (signal?: AbortSignal) =>
    getJson<ModelScienceResponse>('/api/delhi/model-science', signal),
  getLiveState: (refresh = false, horizon = 'ALL', signal?: AbortSignal) =>
    getJson<LiveStateResponse>(
      `/api/delhi/live-state?horizon=${encodeURIComponent(horizon)}${refresh ? '&refresh=true' : ''}`,
      signal,
    ),
  getWhatIf: (rainfallMmH: number, signal?: AbortSignal) =>
    getJson<WhatIfResponse>(
      `/api/delhi/scenario/what-if?rainfall_mm_h=${rainfallMmH}`,
      signal,
    ),
  getWhatIfPresets: (signal?: AbortSignal) =>
    getJson<{ presets_mm_h: number[]; mode: string; claim: string }>(
      '/api/delhi/scenario/what-if/presets',
      signal,
    ),
  getScenarioSafeRoute: (
    params: { origin: [number, number]; destination: [number, number]; rainfall_mm_h: number },
    signal?: AbortSignal,
  ) => {
    const q = new URLSearchParams({
      origin_lon: String(params.origin[0]),
      origin_lat: String(params.origin[1]),
      dest_lon: String(params.destination[0]),
      dest_lat: String(params.destination[1]),
      rainfall_mm_h: String(params.rainfall_mm_h),
    });
    return getJson<ScenarioSafeRouteResponse>(`/api/delhi/scenario/safe-route?${q.toString()}`, signal);
  },
  getDrainageGraph: (signal?: AbortSignal) =>
    getJson<DrainageGraphResponse>('/api/delhi/drainage-graph', signal),
  getDrainageLoading: (
    params: { mode: 'live' | 'historical'; departure_hour?: number; event_id?: string; timestep_index?: number },
    signal?: AbortSignal,
  ) => {
    const q = new URLSearchParams({
      mode: params.mode,
      departure_hour: String(params.departure_hour ?? 0),
      timestep_index: String(params.timestep_index ?? 0),
    });
    if (params.event_id) q.set('event_id', params.event_id);
    return getJson<{ status: string; edges: EdgeLoading[] }>(
      `/api/delhi/drainage-graph/loading?${q.toString()}`,
      signal,
    );
  },
  getSurface: (
    params: { mode: 'live' | 'historical'; departure_hour?: number; event_id?: string; timestep_index?: number },
    signal?: AbortSignal,
  ) => {
    const q = new URLSearchParams({
      mode: params.mode,
      departure_hour: String(params.departure_hour ?? 0),
      timestep_index: String(params.timestep_index ?? 0),
    });
    if (params.event_id) q.set('event_id', params.event_id);
    return getJson<SurfaceResponse>(`/api/delhi/surface?${q.toString()}`, signal);
  },
  getRadarComposite: (signal?: AbortSignal) =>
    getJson<RadarCompositeResponse>('/api/delhi/rainfall/composite', signal),
  scenarioList: (signal?: AbortSignal) =>
    getJson<{ scenarios: ScenarioMeta[]; default_demo_scenario: string; claim_policy: string }>(
      '/api/scenarios',
      signal,
    ),
  scenarioConfig: (signal?: AbortSignal) =>
    getJson<{ thresholds_cm: Record<string, number>; routing_hazard_cm: number; routing_exclude_cm: number }>(
      '/api/scenarios/config',
      signal,
    ),
  scenarioRun: async (scenarioId: string) => {
    const res = await fetch(`/api/scenarios/${scenarioId}/run`, { method: 'POST' });
    if (!res.ok) {
      throw new Error(`scenario run failed (${res.status})`);
    }
    return (await res.json()) as { run_id: string; scenario_id: string; status: string };
  },
  scenarioStatus: (scenarioId: string, runId: string) =>
    getJson<{ run_id: string; scenario_id: string; status: string }>(
      `/api/scenarios/${scenarioId}/status?run_id=${runId}`,
    ),
  scenarioResults: (scenarioId: string, runId: string, timestepIndex?: number) =>
    getJson<ScenarioRunResult>(
      `/api/scenarios/${scenarioId}/results?run_id=${runId}${timestepIndex !== undefined ? `&timestep_index=${timestepIndex}` : ''}`,
    ),
  scenarioValidation: (scenarioId: string, runId: string) =>
    getJson<{ category: string; aggregated: Record<string, unknown>; claim_policy: string }>(
      `/api/scenarios/${scenarioId}/validation?run_id=${runId}`,
    ),
  getSegmentEvidence: (
    segmentId: string,
    params: { mode: 'live' | 'historical'; departure_hour?: number; event_id?: string; timestep_index?: number },
    signal?: AbortSignal,
  ) => {
    const q = new URLSearchParams({
      mode: params.mode,
      departure_hour: String(params.departure_hour ?? 0),
      timestep_index: String(params.timestep_index ?? 0),
    });
    if (params.event_id) q.set('event_id', params.event_id);
    return getJson<SegmentEvidence>(
      `/api/delhi/safe-route/segments/${encodeURIComponent(segmentId)}?${q.toString()}`,
      signal,
    );
  },
};

// ---------------------------------------------------------------------------
// Safe routing (flood-aware; ONE engine, LIVE + HISTORICAL modes)
// ---------------------------------------------------------------------------

export interface RouteRiskSummary {
  blocked_segments: number;
  elevated_risk_segments: number;
  unknown_segments: number;
  low_risk_segments: number;
}

export interface RoutePayload {
  edges: string[];
  geometry: { type: string; coordinates: [number, number][] };
  risk_segments: {
    type: 'FeatureCollection';
    features: {
      properties: { segment_id: string; risk_state: string; name: string };
      geometry: { type: string; coordinates: [number, number][] };
    }[];
  };
  total_distance_km: number;
  estimated_travel_time_min: number;
  flood_risk_summary: RouteRiskSummary;
  route_state: string;
  risk_penalty_s: number;
}

export interface SafeRouteResponse {
  status: string;
  mode: 'LIVE' | 'HISTORICAL';
  event_id: string | null;
  timestep_index: number | null;
  route_run_id: string;
  generated_at: string;
  origin: { coords: [number, number]; snapped_road: string; snap_distance_m: number };
  destination: { coords: [number, number]; snapped_road: string; snap_distance_m: number };
  recommended_route: RoutePayload;
  alternative_route: RoutePayload | null;
  no_alternative_reason: string | null;
  route_comparison: {
    recommended: RouteRiskSummary & {
      distance_km: number;
      travel_time_min: number;
      risk_penalty_s: number;
    };
    alternative: (RouteRiskSummary & {
      distance_km: number;
      travel_time_min: number;
      risk_penalty_s: number;
    }) | null;
  };
  evidence_state: { route_state: string; reason: string; derivation: string };
  explanation: string[];
  claim_policy: string;
  provenance: Record<string, unknown> & {
    mode: string;
    event_id: string | null;
    model_timestamp: string | null;
    forcing_source: string | null;
    road_network_source: string;
    risk_mapping_method: string;
    risk_mapping_threshold_m: number;
    ensemble_members: number;
  };
  data_freshness: {
    note: string;
    rainfall_updated_at: string | null;
    hydraulic_run_updated_at: string | null;
    road_network_updated_at: string | null;
    observation_updated_at: string | null;
  };
}

export interface SegmentEvidence {
  segment_id: string;
  name?: string;
  geometry_source?: string;
  highway?: string;
  length_m?: number;
  risk_state: string;
  risk_reason: string;
  spatial_mapping: {
    method: string;
    threshold_m: number;
    threshold_provenance: string;
    mapped_reach: string | null;
    status: string;
  };
  hydraulic_state: Record<string, unknown> | null;
  mode: string;
  event_id: string | null;
  timestep_index: number | null;
  model_timestamp: string | null;
  forcing_source: string | null;
  evidence_state: string;
  error?: string;
}

export interface SafeRouteParams {
  origin: [number, number];
  destination: [number, number];
  mode: 'live' | 'historical';
  departure_hour?: number;
  event_id?: string;
  timestep_index?: number;
}

// ---------------------------------------------------------------------------
// V1-parity live state (NOW/+1h/+2h/+3h) + WHAT-IF scenario
// ---------------------------------------------------------------------------

export interface V1MassBalance {
  total_runoff_m3: number;
  conveyed_m3: number;
  surcharged_m3: number;
  overflow_m3: number;
  drained_out_m3: number;
}

export interface AffectedRoadEntry {
  road_id: string;
  osm_id: number;
  name: string;
  highway: string;
  max_depth_m: number;
  flooded_length_m: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE' | 'UNKNOWN';
  provenance: string;
}

export interface AffectedIntersectionEntry {
  intersection_id: string;
  name: string;
  roads_display: string;
  max_depth_m: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE' | 'UNKNOWN';
  connection_count: number;
  provenance: string;
}

export interface StreetsIntel {
  horizon: string;
  summary: {
    total_affected_roads: number;
    total_affected_intersections: number;
    max_street_depth_m: number;
    total_flooded_road_length_m: number;
    risk_counts: { CRITICAL: number; HIGH: number; MEDIUM: number; LOW: number };
  };
  affected_roads: AffectedRoadEntry[];
  affected_intersections: AffectedIntersectionEntry[];
  roads_geojson: { type: string; features: unknown[] };
  intersections_geojson: { type: string; features: unknown[] };
  provenance: Record<string, string>;
}

export interface LiveHorizonState {
  horizon: 'NOW' | '+1h' | '+2h' | '+3h';
  lead_time: string;
  rainfall_mm: number | null;
  rainfall_provenance: string;
  time_start: string | null;
  time_end: string | null;
  status: 'COMPUTED' | 'UNKNOWN_FORCING';
  max_depth_m: number | null;
  flooded_area_m2: number | null;
  flood_volume_m3: number | null;
  v1_mass_balance?: V1MassBalance;
  risk?: { text: string; description: string };
  depth_cells: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[];
  depth_polygons?: { type: string; features: unknown[] };
  streets: StreetsIntel | null;
  source_type?: string;
  provenance?: Record<string, unknown>;
}

export interface LiveStateResponse {
  rainfall_status: 'COMPUTED' | 'STALE' | 'SYNTHETIC_FALLBACK';
  rainfall_source: string;
  rainfall_acquired_at: string | null;
  diagnostics: string[];
  horizons: LiveHorizonState[];
  peak: {
    max_depth_m: number | null;
    peak_horizon: string | null;
    max_street_depth_m: number;
    total_flooded_area_m2: number;
  };
  claim_policy: string;
  provenance: Record<string, string>;
}

export interface WhatIfResponse {
  scenario: { kind: string; label: string; rainfall_mm_h: number; note: string };
  status: string;
  max_depth_m: number;
  flooded_area_m2: number;
  v1_mass_balance: V1MassBalance;
  depth_cells: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[];
  depth_polygons: { type: string; features: unknown[] };
  streets: StreetsIntel;
  source_type: string;
  provenance: Record<string, string>;
}

export interface ScenarioSafeRouteResponse {
  status: string;
  mode: 'SCENARIO';
  scenario: { kind: string; label: string; rainfall_mm_h: number };
  generated_at: string;
  origin: { coords: [number, number]; snapped_road: string; snap_distance_m: number };
  destination: { coords: [number, number]; snapped_road: string; snap_distance_m: number };
  recommended_route: RoutePayload;
  alternative_route: RoutePayload | null;
  no_alternative_reason: string | null;
  evidence_state: { route_state: string; reason: string };
  explanation: string[];
  max_depth_on_route_m: number;
  claim_policy: string;
  provenance: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Scientific model performance (validation / calibration / ML gating)
// ---------------------------------------------------------------------------

export interface ModelScienceResponse {
  generated_at: string;
  production_mode: string;
  ml_status: string;
  claim_policy: string;
  observation_registry: {
    record_count: number;
    summary: Record<
      string,
      {
        count: number;
        tiers: Record<string, number>;
        usable_for_calibration: number;
        usable_for_validation: number;
        usable_for_forcing_qc: number;
      }
    >;
    gate_note: string;
  };
  quantitative_validation: {
    evidence_gate: Record<
      string,
      {
        QUANTITATIVE_VALIDATION_SUPPORTED: 'YES' | 'NO';
        relevant_observations: number;
        local_tier_ab_observations: number;
        note: string;
      }
    >;
    event_split: Record<string, string[] | string>;
    metrics: {
      metric_name: string;
      event_ids: string;
      observation_type: string;
      model_quantity: string;
      n_observations: number;
      temporal_alignment: string;
      spatial_alignment: string;
      source_tier: string;
      uncertainty: string;
      validity_status: string;
      value: number | null;
      units: string;
      reason: string;
    }[];
  };
  calibration: {
    performed: boolean;
    objective_gate: {
      objective_supported: boolean;
      local_quantitative_targets: number;
      reason: string;
      weights_provenance: string;
    };
    parameter_registry: {
      parameter_name: string;
      baseline_value: number | null;
      lower_bound: number | null;
      upper_bound: number | null;
      source: string;
      provenance: string;
      reason_for_bound: string;
      units: string;
      identifiability_status: string;
    }[];
    baseline_preserved: boolean;
    glue_screen: {
      method: string;
      seed: number;
      n_samples: number;
      n_behavioral: number;
      n_non_behavioral: number;
      behavioral_span_coverage: Record<string, number>;
      discrimination_finding: string;
    };
    audit: { checks: Record<string, string>; status: string; failed_checks: string[] };
  };
  identifiability: {
    method: string;
    sensitivity_threshold: number;
    parameters: {
      parameter_name: string;
      influence_channel: string;
      sensitivity_index: number | null;
      model_sensitive: boolean | null;
      identifiability_status: string;
      note: string;
    }[];
    summary: string;
  };
  uncertainty: {
    event_id: string;
    source: string;
    metric: string;
    value: number | null;
    detail: string;
  }[];
  ml: {
    strategy: string;
    production_mode: string;
    ml_status: string;
    gates: Record<string, string>;
    reason: string;
    fallback_contract: string;
    dataset: {
      residual_target: { status: string; reason: string };
      occurrence_target: {
        status: string;
        usable_events: number;
        positives: number;
        negatives: number;
        note: string;
      };
      event_grouped_cv: {
        strategy: string;
        min_events_for_reported_cv: number;
        gate: string;
      };
    };
  };
}

// ---------------------------------------------------------------------------
// Reconstruction products: drainage graph, loading, depth estimates, surface
// ---------------------------------------------------------------------------

export interface DrainageGraphResponse {
  generated_at: string;
  n_nodes: number;
  n_edges: number;
  provenance: string;
  nodes: { type: string; features: unknown[] };
  edges: {
    type: string;
    features: {
      properties: {
        edge_id: string;
        reach_id: string;
        length_m: number;
        capacity_min_m3_s: number;
        capacity_max_m3_s: number;
        capacity_provenance: string;
        dimension_basis: string;
      };
      geometry: { type: string; coordinates: [number, number][] };
    }[];
  };
}

export interface EdgeLoading {
  edge_id: string;
  node_id: string;
  reach_id: string;
  inflow_m3_s: number | null;
  capacity_min_m3_s: number;
  capacity_max_m3_s: number;
  status: 'NO_LOADING' | 'WITHIN_CAPACITY_RANGE' | 'POTENTIAL_OVERLOAD' | 'UNKNOWN';
  reason: string;
}

export interface DepthEstimate {
  reach_id: string;
  node_id: string;
  storage_m3: number | null;
  depth_min_cm: number | null;
  depth_max_cm: number | null;
  status: string;
  reason: string;
  provenance: string;
  caveat: string;
}

export interface SurfaceHotspot {
  lon: number;
  lat: number;
  surface_water_cm_estimated: number;
  provenance: string;
}

export interface SurfaceResponse {
  status: string;
  method: string;
  caveat: string;
  runoff_coefficient: number;
  runoff_coefficient_provenance: string;
  timesteps: {
    timestep_index: number;
    status: string;
    peak_surface_cm: number | null;
    hotspots: SurfaceHotspot[];
    per_reach_surface_inflow_m3_s: Record<string, number>;
  }[];
}

export interface RadarCompositeResponse {
  generated_at?: string;
  provenance: string;
  status: string;
  is_fallback: boolean;
  fallback_reason: string | null;
  source_name: string;
  nwp_acquired_at: string | null;
  radar_station: Record<string, unknown>;
  radar_diagnostics: {
    endpoint_key: string;
    http_status: number;
    is_accessible: boolean;
    is_quantitative: boolean;
  }[];
}

export interface NowcastDepthAndLoading {
  drainage_loading: EdgeLoading[];
  depth_estimates: Record<string, DepthEstimate>;
  surface: SurfaceResponse | { status: string; reason?: string };
}

// ---------------------------------------------------------------------------
// Synthetic scenario engine
// ---------------------------------------------------------------------------

export interface ScenarioMeta {
  scenario_id: string;
  name: string;
  description: string;
  duration_min: number;
  timestep_min: number;
  n_steps: number;
  seed: number;
  ensemble_members: number;
  drainage_modifier: number | null;
  boundary_profile: string | null;
  default_demo: boolean;
}

export interface ScenarioStep {
  timestep_index: number;
  time_start: string;
  time_end: string;
  max_depth_cm: number;
  flooded_cells: number;
  flood_state: string;
  hotspots: { lon: number; lat: number; surface_water_cm_estimated: number; provenance: string }[];
  depth_cells?: { lon: number; lat: number; depth_cm: number; flood_state: string; provenance: string }[];
  depth_polygons?: { type: string; features: { properties: { depth_cm: number; flood_state: string; color: string }; geometry: { type: string; coordinates: number[][][] } }[] };
  per_reach_surface_inflow_m3_s: Record<string, number>;
  source_type: string;
}

export interface ScenarioMember {
  member_index: number;
  member_scale: number;
  forcing_depths_mm: number[];
  inflow_m3_s: (number | null)[];
  steps: ScenarioStep[];
  max_depth_cm_traj: number[];
  edge_depths: Record<string, { depth_min_cm: number | null; depth_max_cm: number | null; status: string; reason: string }>;
  road_depths: Record<string, { depth_cm: number; depth_m: number; flood_state: string; source_type: string }>;
  drainage_loading: {
    edge_id: string;
    node_id: string;
    reach_id: string;
    inflow_m3_s: number | null;
    capacity_min_m3_s: number;
    capacity_max_m3_s: number;
    status: string;
    reason: string;
  }[];
  telemetry: {
    sensors: Record<string, string>;
    steps: { timestep_index: number; time_start: string; readings: { sensor_id: string; value: number | string | null; unit: string }[] }[];
    source_type: string;
    scenario_id: string;
  };
  source_type: string;
  scenario_id: string;
}

export interface ScenarioRunResult {
  run_id: string;
  scenario_id: string;
  scenario_name: string;
  seed: number;
  status: string;
  generated_at: string;
  generated_by: string;
  n_steps: number;
  timestep_min: number;
  duration_min: number;
  source_type: string;
  claim_policy: string;
  ensemble: boolean;
  members: ScenarioMember[];
  ensemble_envelope: { timestep_index: number; mean_depth_cm: number; min_depth_cm: number; max_depth_cm: number; spread_cm: number }[] | null;
  truth: {
    steps: { timestep_index: number; max_truth_depth_cm: number; flooded_cells: number }[];
    source_type: string;
    generation_method: string;
  };
  synthetic_validation: {
    category: string;
    note: string;
    aggregated: Record<string, unknown>;
    per_step: unknown[];
  };
  provenance: Record<string, unknown>;
}
