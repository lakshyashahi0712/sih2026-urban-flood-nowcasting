"""NetworkBuilder for converting raster drainage outputs to vector drainage network."""

from __future__ import annotations

import numpy as np
from affine import Affine
from typing import Dict, List, Tuple, Optional

try:
    from backend.app.domain.drainage.models import DrainageChannel, DrainageNode, DrainageNetwork, NodeType, Provenance
    from backend.app.infrastructure.drainage.raster_engine import RasterEngine
except ImportError:
    from app.domain.drainage.models import DrainageChannel, DrainageNode, DrainageNetwork, NodeType, Provenance
    from app.infrastructure.drainage.raster_engine import RasterEngine


class NetworkBuilder:
    """Builds a DrainageNetwork from RasterEngine outputs."""

    def __init__(self, engine: RasterEngine):
        """Initialize with a processed RasterEngine.

        Args:
            engine: A RasterEngine that has been processed through
                    load_and_preprocess, condition_dem, compute_flow_direction,
                    compute_flow_accumulation, and apply_threshold.
        """
        self.engine = engine
        self._validate_engine_state()

        self.stream_mask = engine.get_stream_mask()
        self.flow_dir = engine.get_flow_direction()
        self.filled_dem = engine.get_filled_dem()
        meta = engine.get_metadata()
        self.transform: Affine = meta['transform']
        self.crs: str = str(meta['crs'])
        self.cell_size: float = abs(self.transform.a)

        self.D8_DIRS = {
            'E': 1, 'SE': 2, 'S': 4, 'SW': 8,
            'W': 16, 'NW': 32, 'N': 64, 'NE': 128,
        }
        self.D8_DIRS_REV = {v: k for k, v in self.D8_DIRS.items()}
        self.D8_OFFSETS = {
            'E': (0, 1), 'SE': (1, 1), 'S': (1, 0), 'SW': (1, -1),
            'W': (0, -1), 'NW': (-1, -1), 'N': (-1, 0), 'NE': (-1, 1),
        }

        self.height, self.width = self.stream_mask.shape
        self._upstream_count: Optional[np.ndarray] = None
        self._nodes: Dict[str, DrainageNode] = {}
        self._channels: Dict[str, DrainageChannel] = {}

    def _validate_engine_state(self) -> None:
        """Check that the engine has been fully processed."""
        if self.engine._stream_mask is None:
            raise RuntimeError("Stream mask not generated. Call apply_threshold first.")
        if self.engine._flow_dir is None:
            raise RuntimeError("Flow direction not computed. Call compute_flow_direction first.")
        if self.engine._filled_dem is None:
            raise RuntimeError("DEM not conditioned. Call condition_dem first.")
        if self.engine._drainage_area is None:
            raise RuntimeError("Drainage area not computed. Call compute_flow_accumulation first.")

    def _compute_upstream_count(self) -> np.ndarray:
        """Compute the number of upstream neighbors for each cell in the stream mask."""
        upstream_count = np.zeros_like(self.stream_mask, dtype=int)
        for r in range(self.height):
            for c in range(self.width):
                if not self.stream_mask[r, c]:
                    continue
                dir_val = self.flow_dir[r, c]
                if dir_val == 0:
                    continue
                dir_name = self.D8_DIRS_REV.get(dir_val)
                if dir_name is None:
                    continue
                dr, dc = self.D8_OFFSETS[dir_name]
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width and self.stream_mask[nr, nc]:
                    upstream_count[nr, nc] += 1
        return upstream_count

    def _is_node(self, r: int, c: int) -> Tuple[bool, Optional[NodeType]]:
        """Determine if a cell is a node (junction, outlet, or inlet) and its type."""
        if not self.stream_mask[r, c]:
            return False, None
        if self.flow_dir[r, c] == 0:
            return True, NodeType.OUTLET
        if self._upstream_count[r, c] > 1:
            return True, NodeType.JUNCTION
        if self._upstream_count[r, c] == 0:
            return True, NodeType.INLET
        return False, None

    def _get_downstream(self, r: int, c: int) -> Optional[Tuple[int, int]]:
        """Get the downstream neighbor coordinates, or None if sink or out of bounds."""
        dir_val = self.flow_dir[r, c]
        if dir_val == 0:
            return None
        dir_name = self.D8_DIRS_REV.get(dir_val)
        if dir_name is None:
            return None
        dr, dc = self.D8_OFFSETS[dir_name]
        nr, nc = r + dr, c + dc
        if 0 <= nr < self.height and 0 <= nc < self.width and self.stream_mask[nr, nc]:
            return (nr, nc)
        return None

    def _step_length(self, r: int, c: int, dr: int, dc: int) -> float:
        """Calculate the length of a step from (r, c) to (r+dr, c+dc)."""
        if dr == 0 or dc == 0:
            return self.cell_size
        else:
            return self.cell_size * np.sqrt(2)

    def build_network(self) -> DrainageNetwork:
        """Build the drainage network from the raster outputs.

        Returns:
            A DrainageNetwork containing nodes, channels, and CRS.
        """
        self._upstream_count = self._compute_upstream_count()

        for r in range(self.height):
            for c in range(self.width):
                is_node, node_type = self._is_node(r, c)
                if not is_node:
                    continue
                node_id = f"n_{r}_{c}"
                x, y = self.transform * (c, r)
                elevation = float(self.filled_dem[r, c])
                self._nodes[node_id] = DrainageNode(
                    id=node_id,
                    x=x,
                    y=y,
                    elevation_m=elevation,
                    node_type=node_type,
                    provenance=Provenance.DEM_DERIVED
                )

        visited = set()
        for r in range(self.height):
            for c in range(self.width):
                if not self.stream_mask[r, c]:
                    continue
                if self._upstream_count[r, c] == 0 or self._upstream_count[r, c] > 1:
                    if self.flow_dir[r, c] == 0 and self._upstream_count[r, c] == 0:
                        continue

                    path = [(r, c)]
                    current_r, current_c = r, c
                    total_length = 0.0
                    visited.add((current_r, current_c))

                    while True:
                        downstream = self._get_downstream(current_r, current_c)
                        if downstream is None:
                            break
                        nr, nc = downstream

                        # CRITICAL: a downstream cell that is itself a node
                        # (junction/inlet/outlet) is ALWAYS a valid channel
                        # endpoint, even if a different trace reached it
                        # first -- convergence is exactly what makes it a
                        # junction. Only bail out for a non-node cell that's
                        # already visited (defensive guard against cycles,
                        # which shouldn't occur given the DAG guarantee).
                        is_downstream_node, _ = self._is_node(nr, nc)
                        if not is_downstream_node and (nr, nc) in visited:
                            break

                        dir_name = self.D8_DIRS_REV[self.flow_dir[current_r, current_c]]
                        dr, dc = self.D8_OFFSETS[dir_name]
                        step = self._step_length(current_r, current_c, dr, dc)
                        total_length += step
                        current_r, current_c = nr, nc
                        visited.add((current_r, current_c))
                        path.append((current_r, current_c))

                        if is_downstream_node and (current_r, current_c) != (r, c):
                            break

                    if len(path) > 1:
                        start_id = f"n_{path[0][0]}_{path[0][1]}"
                        end_id = f"n_{path[-1][0]}_{path[-1][1]}"
                        if start_id in self._nodes and end_id in self._nodes:
                            channel_id = f"ch_{start_id}_{end_id}"
                            if channel_id not in self._channels:
                                self._channels[channel_id] = DrainageChannel(
                                    id=channel_id,
                                    upstream_node_id=start_id,
                                    downstream_node_id=end_id,
                                    length_m=total_length,
                                    provenance=Provenance.DEM_DERIVED
                                )

        return DrainageNetwork(
            nodes=self._nodes,
            channels=self._channels,
            crs=self.crs
        )