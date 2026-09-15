"""Unit tests for the hydraulic network solver (Phases 7B/7C).

Phase 7C: steady-state flow conservation and propagation tests.
All networks are small and hand-checkable.
"""

from __future__ import annotations

import pytest

from backend.app.domain.delhi.digital_twin.hydraulic_network_solver import (
    HydraulicNetworkSolver,
    ReachFlowResult,
)
from backend.app.domain.delhi.digital_twin.hydraulic_contract import (
    HydraulicDataset,
    HydraulicNode,
    OpenChannelReach,
    ProvenancedValue,
    InflowAttachment,
    DownstreamBoundary,
)
from backend.app.domain.delhi.digital_twin.models import ProvenanceStatus


def make_node(node_id, node_type="JUNCTION", downstream=None, upstream=None):
    return HydraulicNode(
        node_id=node_id,
        easting=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        northing=ProvenancedValue(value=0.0, provenance=ProvenanceStatus.OBSERVED),
        invert_elev_m=ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
        node_type=node_type,
        upstream_connections=list(upstream or []),
        downstream_connections=list(downstream or []),
    )


def make_reach(reach_id, upstream_node, downstream_node, manning_n=0.015):
    return OpenChannelReach(
        reach_id=reach_id,
        upstream_node_id=upstream_node,
        downstream_node_id=downstream_node,
        chainage_profile=[],
        geometry_representation="TABULATED",
        width_m=ProvenancedValue(value=5.0, provenance=ProvenanceStatus.OBSERVED),
        depth_m=ProvenancedValue(value=2.0, provenance=ProvenanceStatus.OBSERVED),
        slope_m_per_m=ProvenancedValue(value=0.005, provenance=ProvenanceStatus.OBSERVED),
        length_m=ProvenancedValue(value=100.0, provenance=ProvenanceStatus.OBSERVED),
        manning_n=ProvenancedValue(value=manning_n, provenance=ProvenanceStatus.OBSERVED),
        structure_refs=[],
        cross_section_refs=[],
    )


VALID_GEOM = (  # rectangular: area = 5*2 = 10, perimeter = 5 + 2*2 = 9
    ProvenancedValue(value=10.0, provenance=ProvenanceStatus.OBSERVED),
    ProvenancedValue(value=9.0, provenance=ProvenanceStatus.OBSERVED),
)


def create_test_dataset():
    """Simple two-node, one-reach dataset (Phase 7B baseline)."""
    dataset = HydraulicDataset(
        nodes=[make_node("N1", downstream=["N2"]), make_node("N2", "OUTFALL", upstream=["N1"])],
        open_channel_reaches=[make_reach("R1", "N1", "N2")],
    )
    return dataset


def solve_with_inflow(dataset, inflows=None, geometry=None, zero_nodes=None):
    """Build a solver, supply explicit external inflows, and solve."""
    solver = HydraulicNetworkSolver(dataset, zero_inflow_node_ids=zero_nodes)
    for node_id, inflow_id, discharge in inflows or []:
        solver.set_external_inflow(node_id, inflow_id, discharge)
    results, errors = solver.solve(geometry or {"R1": VALID_GEOM})
    return solver, results, errors


def by_reach(results):
    return {r.reach_id: r for r in results}


def test_single_inflow_propagates_unchanged_through_one_reach():
    """Test 1: single upstream inflow propagates unchanged through one reach."""
    dataset = create_test_dataset()
    solver, results, errors = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 20.0)]
    )
    assert len(errors) == 0
    r = by_reach(results)["R1"]
    assert r.status == "COMPUTED"
    assert r.propagated_flow_m3_s == 20.0  # conserved exactly, no attenuation
    # Manning capacity for this geometry is ~50.6 (see Phase 7B test)
    assert r.capacity_m3_s is not None
    assert 50.0 < r.capacity_m3_s < 51.0
    assert r.capacity_exceeded is False


def test_two_upstream_reaches_combine_at_confluence():
    """Test 2: two upstream reaches combine at a confluence."""
    dataset = HydraulicDataset(
        nodes=[
            make_node("N1", downstream=["N3"]),
            make_node("N2", downstream=["N3"]),
            make_node("N3", "OUTFALL", upstream=["N1", "N2"]),
        ],
        open_channel_reaches=[
            make_reach("R1", "N1", "N3"),
            make_reach("R2", "N2", "N3"),
        ],
    )
    _, results, errors = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 10.0), ("N2", "I2", 15.0)],
        geometry={"R1": VALID_GEOM, "R2": VALID_GEOM},
    )
    assert len(errors) == 0
    res = by_reach(results)
    assert res["R1"].propagated_flow_m3_s == 10.0
    assert res["R2"].propagated_flow_m3_s == 15.0
    # N3 confluence: R1 + R2, no external inflow
    for rid in ("R1", "R2"):
        pass
    # Check conservation at N3 via the downstream reach inflow components
    n3_result = res["R1"]  # both reaches receive the conserved N3 flow? No:
    # N3 is an outfall (no outgoing reaches), so conservation shows in components.
    # Re-run attaching a downstream reach from N3 to verify the combined flow.
    dataset2 = HydraulicDataset(
        nodes=[
            make_node("N1", downstream=["N3"]),
            make_node("N2", downstream=["N3"]),
            make_node("N3", upstream=["N1", "N2"], downstream=["N4"]),
            make_node("N4", "OUTFALL", upstream=["N3"]),
        ],
        open_channel_reaches=[
            make_reach("R1", "N1", "N3"),
            make_reach("R2", "N2", "N3"),
            make_reach("R3", "N3", "N4"),
        ],
    )
    _, results2, errors2 = solve_with_inflow(
        dataset2, inflows=[("N1", "I1", 10.0), ("N2", "I2", 15.0)],
        geometry={"R1": VALID_GEOM, "R2": VALID_GEOM, "R3": VALID_GEOM},
    )
    assert len(errors2) == 0
    r3 = by_reach(results2)["R3"]
    assert r3.propagated_flow_m3_s == 25.0  # 10 + 15, conserved
    assert r3.inflow_components_m3_s == {"upstream:R1": 10.0, "upstream:R2": 15.0}
    assert set(r3.inflow_sources) == {"upstream:R1", "upstream:R2"}


def test_explicit_external_tributary_inflow_added():
    """Test 3: explicit external tributary inflow is added correctly."""
    dataset = create_test_dataset()
    # Upstream reach inflow 10 at N1 plus external tributary 5 at N1.
    _, results, errors = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 10.0), ("N1", "I2", 5.0)]
    )
    assert len(errors) == 0
    r = by_reach(results)["R1"]
    assert r.propagated_flow_m3_s == 15.0
    assert r.inflow_components_m3_s == {"external:I1": 10.0, "external:I2": 5.0}


def test_unknown_tributary_blocks_downstream_flow():
    """Test 4: missing/UNKNOWN tributary inflow blocks downstream flow."""
    dataset = HydraulicDataset(
        nodes=[
            make_node("N1", downstream=["N2"]),
            make_node("N2", upstream=["N1"], downstream=["N3"]),
            make_node("N3", "OUTFALL", upstream=["N2"]),
        ],
        open_channel_reaches=[make_reach("R1", "N1", "N2"), make_reach("R2", "N2", "N3")],
        # Lateral attachment at N2 with no discharge value anywhere:
        inflow_attachments=[InflowAttachment(
            inflow_id="LAT1",
            source_subcatchment_id="S1",
            attachment_node_id="N2",
            invert_elev_at_attachment_m=ProvenancedValue(value=9.0, provenance=ProvenanceStatus.OBSERVED),
        )],
    )
    _, results, errors = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 10.0)],
        geometry={"R1": VALID_GEOM, "R2": VALID_GEOM},
    )
    assert len(errors) == 0
    res = by_reach(results)
    # R1 (upstream of the unknown attachment) still propagates.
    assert res["R1"].status == "COMPUTED"
    assert res["R1"].propagated_flow_m3_s == 10.0
    # R2 (downstream of the unknown attachment) is blocked, NOT 10 as if zero.
    assert res["R2"].status == "BLOCKED_UNKNOWN_INFLOW"
    assert res["R2"].propagated_flow_m3_s is None
    assert "LAT1" in res["R2"].diagnostic


def test_capacity_separate_from_propagated_discharge():
    """Test 5: Manning capacity remains separate from propagated discharge."""
    dataset = create_test_dataset()
    _, results, _ = solve_with_inflow(dataset, inflows=[("N1", "I1", 20.0)])
    r = by_reach(results)["R1"]
    assert r.propagated_flow_m3_s == 20.0
    assert r.capacity_m3_s is not None
    assert r.capacity_m3_s != r.propagated_flow_m3_s
    # Legacy field still carries the Manning capacity, not the propagated flow.
    assert r.flow_m3_s == r.capacity_m3_s


def test_propagated_flow_below_capacity():
    """Test 6: propagated flow below capacity."""
    dataset = create_test_dataset()
    _, results, _ = solve_with_inflow(dataset, inflows=[("N1", "I1", 20.0)])
    r = by_reach(results)["R1"]
    assert r.capacity_exceeded is False
    assert r.propagated_flow_m3_s < r.capacity_m3_s


def test_propagated_flow_above_capacity_no_invented_overflow():
    """Test 7: flow above capacity flags capacity_exceeded, invents nothing."""
    dataset = create_test_dataset()
    _, results, _ = solve_with_inflow(dataset, inflows=[("N1", "I1", 60.0)])
    r = by_reach(results)["R1"]
    assert r.capacity_exceeded is True
    assert r.propagated_flow_m3_s == 60.0  # NOT clamped to capacity
    assert r.capacity_m3_s is not None and r.capacity_m3_s < 60.0
    # No invented overflow/depth/surcharge fields exist or are populated.
    assert not hasattr(r, "overflow_volume_m3")
    assert not hasattr(r, "water_depth_m")


def test_branching_without_split_rule_is_unresolved():
    """Test 8: branching without a flow-split rule is blocked/unresolved."""
    dataset = HydraulicDataset(
        nodes=[
            make_node("N1", downstream=["N2", "N3"]),
            make_node("N2", "OUTFALL", upstream=["N1"]),
            make_node("N3", "OUTFALL", upstream=["N1"]),
        ],
        open_channel_reaches=[make_reach("R1", "N1", "N2"), make_reach("R2", "N1", "N3")],
    )
    _, results, _ = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 30.0)],
        geometry={"R1": VALID_GEOM, "R2": VALID_GEOM},
    )
    res = by_reach(results)
    for rid in ("R1", "R2"):
        assert res[rid].status == "UNRESOLVED_FLOW_SPLIT"
        assert res[rid].propagated_flow_m3_s is None or res[rid].capacity_m3_s is None
    # The full node flow is reported as diagnostic context, but no branch
    # claims it as its assigned discharge.
    assert res["R1"].capacity_m3_s is None
    assert res["R2"].capacity_m3_s is None


def test_topological_ordering_respected():
    """Test 9: topological ordering is respected (upstream solved first)."""
    dataset = HydraulicDataset(
        nodes=[
            make_node("N1", downstream=["N2"]),
            make_node("N2", upstream=["N1"], downstream=["N3"]),
            make_node("N3", upstream=["N2"], downstream=["N4"]),
            make_node("N4", "OUTFALL", upstream=["N3"]),
        ],
        open_channel_reaches=[
            make_reach("R1", "N1", "N2"),
            make_reach("R2", "N2", "N3"),
            make_reach("R3", "N3", "N4"),
        ],
    )
    _, results, errors = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 7.0)],
        geometry={"R1": VALID_GEOM, "R2": VALID_GEOM, "R3": VALID_GEOM},
    )
    assert len(errors) == 0
    res = by_reach(results)
    # Flow is conserved along the whole chain: every reach carries 7.0.
    assert res["R1"].propagated_flow_m3_s == 7.0
    assert res["R2"].propagated_flow_m3_s == 7.0
    assert res["R3"].propagated_flow_m3_s == 7.0
    assert res["R3"].inflow_components_m3_s == {"upstream:R2": 7.0}


def test_propagated_discharge_provenance_is_derived():
    """Test 10: provenance of propagated discharge is DERIVED/COMPUTED."""
    dataset = create_test_dataset()
    _, results, _ = solve_with_inflow(dataset, inflows=[("N1", "I1", 20.0)])
    r = by_reach(results)["R1"]
    # Propagated flow is a DERIVED result, not OBSERVED, even though the
    # external inflow itself was OBSERVED.
    assert r.propagated_flow_provenance == ProvenanceStatus.DERIVED
    # Input provenance is retained separately.
    assert r.inflow_provenance == ProvenanceStatus.OBSERVED
    assert r.geometry_provenance == (ProvenanceStatus.OBSERVED, ProvenanceStatus.OBSERVED)
    assert r.manning_provenance == ProvenanceStatus.OBSERVED


def test_no_silent_zero_substitution():
    """Test 11: no silent zero substitution for a missing inflow record."""
    dataset = create_test_dataset()
    # No external inflow supplied at N1 at all.
    _, results, _ = solve_with_inflow(dataset, inflows=None)
    r = by_reach(results)["R1"]
    assert r.status == "BLOCKED_UNKNOWN_INFLOW"
    assert r.propagated_flow_m3_s is None
    assert "no inflow record" in r.diagnostic
    # Explicitly marking the node as a zero-flow boundary changes the outcome
    # deterministically (contract-driven, not inferred).
    _, results2, _ = solve_with_inflow(
        create_test_dataset(), inflows=None, zero_nodes={"N1"}
    )
    r2 = by_reach(results2)["R1"]
    assert r2.status == "COMPUTED"
    assert r2.propagated_flow_m3_s == 0.0


def test_existing_topology_validation_remains_intact():
    """Test 12: existing Phase 7B topology validation remains intact."""
    # Missing node reference.
    dataset_missing = HydraulicDataset(
        nodes=[make_node("N1")],
        open_channel_reaches=[make_reach("R1", "N1", "N2")],
    )
    _, errors, = HydraulicNetworkSolver(dataset_missing).solve({"R1": VALID_GEOM})
    assert any("not found" in err.lower() for err in errors)

    # Cycle.
    dataset_cycle = HydraulicDataset(
        nodes=[make_node("N1", downstream=["N2"]), make_node("N2", downstream=["N1"])],
        open_channel_reaches=[make_reach("R1", "N1", "N2"), make_reach("R2", "N2", "N1")],
    )
    results, errors = HydraulicNetworkSolver(dataset_cycle).solve(
        {"R1": VALID_GEOM, "R2": VALID_GEOM}
    )
    assert any("cycle" in err.lower() for err in errors)
    assert results == []

    # Missing geometry still blocks.
    dataset = create_test_dataset()
    missing_geom = (
        ProvenancedValue(value=None, provenance=ProvenanceStatus.UNKNOWN),
        VALID_GEOM[1],
    )
    _, results, errors = solve_with_inflow(
        dataset, inflows=[("N1", "I1", 20.0)], geometry={"R1": missing_geom}
    )
    assert by_reach(results)["R1"].status == "BLOCKED_MISSING_GEOMETRY"
    # Propagated flow is still reported even though capacity is blocked.
    assert by_reach(results)["R1"].propagated_flow_m3_s == 20.0


def test_solver_uses_canonical_manning_adapter():
    """Test 13 (7D-9): the solver routes through the Phase 7D-8 adapter."""
    import backend.app.domain.delhi.digital_twin.hydraulic_network_solver as ns

    calls = []
    original = ns.calculate_capacity_from_bundle

    def spy(bundle, n, slope, **kwargs):
        calls.append((bundle, n, slope))
        return original(bundle, n, slope, **kwargs)

    ns.calculate_capacity_from_bundle = spy
    try:
        dataset = create_test_dataset()
        _, results, errors = solve_with_inflow(dataset, inflows=[("N1", "I1", 20.0)])
    finally:
        ns.calculate_capacity_from_bundle = original

    assert len(errors) == 0
    # The canonical adapter was invoked exactly once, with a COMPUTED bundle
    # carrying the reach's geometry and the reach's n/slope.
    assert len(calls) == 1
    bundle, n, slope = calls[0]
    assert bundle.status == "COMPUTED"
    assert bundle.area_m2 == pytest.approx(10.0)
    assert bundle.perimeter_m == pytest.approx(9.0)
    assert n == pytest.approx(0.015)
    assert slope == pytest.approx(0.005)
    # Result contract unchanged.
    r = by_reach(results)["R1"]
    assert r.status == "COMPUTED"
    assert r.capacity_m3_s is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
