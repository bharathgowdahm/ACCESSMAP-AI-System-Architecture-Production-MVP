"""Constrained Routing Engine with Multi-Objective Graph Search."""
from dataclasses import dataclass
import math
from typing import Any
from core.accessibility_scoring import AccessDNAScore, SegmentAttributes, compute_access_dna
from core.schemas import MobilityProfileSchema
import networkx as nx
from shapely.geometry import Point


@dataclass
class CalculatedRoute:
    path_coords: list[tuple[float, float]]
    total_distance_m: float
    estimated_time_min: float
    dna_score: AccessDNAScore
    nodes: list[int]
    is_accessible: bool
    summary_label: str


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in meters."""
    r = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def create_synthetic_accessible_subgraph(
    center_lat: float,
    center_lon: float,
    radius_m: float = 800.0
) -> nx.MultiDiGraph:
    """Builds a deterministic walkable street grid for testing and fallback routing."""
    g = nx.MultiDiGraph()
    # 5x5 grid offset by delta degrees (~111 km/deg latitude)
    step = (radius_m / 111320.0) / 2.0
    node_id = 1
    matrix = {}

    for i in range(-2, 3):
        for j in range(-2, 3):
            lat = center_lat + (i * step)
            lon = center_lon + (j * (step / math.cos(math.radians(center_lat))))
            g.add_node(node_id, y=lat, x=lon)
            matrix[(i, j)] = node_id
            node_id += 1

    # Connect grid bi-directionally with realistic accessibility attributes
    for i in range(-2, 3):
        for j in range(-2, 3):
            curr = matrix[(i, j)]
            for di, dj, is_stairs, slope in [(0, 1, False, 2.0), (1, 0, (i == 0 and j == 0), 12.0)]:
                ni, nj = i + di, j + dj
                if (ni, nj) in matrix:
                    nbr = matrix[(ni, nj)]
                    dist = haversine_distance(
                        g.nodes[curr]["y"], g.nodes[curr]["x"],
                        g.nodes[nbr]["y"], g.nodes[nbr]["x"]
                    )
                    # Add forward and reverse edges
                    for u, v in [(curr, nbr), (nbr, curr)]:
                        g.add_edge(
                            u, v,
                            length=dist,
                            highway="footway" if not is_stairs else "steps",
                            surface="paved" if not is_stairs else "concrete",
                            incline=f"{slope}%" if slope else "0%",
                            kerb="lowered" if not is_stairs else "raised",
                            width="1.8" if not is_stairs else "0.8"
                        )
    return g


class AccessibleRoutingEngine:
    """Graph routing engine with hard mobility constraints and soft penalty weights."""

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def _find_nearest_node(self, lat: float, lon: float) -> int:
        best_node = None
        min_dist = float("inf")
        for node, data in self.graph.nodes(data=True):
            d = haversine_distance(lat, lon, data["y"], data["x"])
            if d < min_dist:
                min_dist = d
                best_node = node
        if best_node is None:
            raise ValueError("Graph contains no nodes.")
        return best_node

    def calculate_routes(
        self,
        origin_lat: float, origin_lon: float,
        dest_lat: float, dest_lon: float,
        profile: MobilityProfileSchema,
        active_obstacles: list[Any] | None = None
    ) -> list[CalculatedRoute]:
        """Calculates:
        1. Direct Shortest Route (unconstrained baseline)
        2. MobilityMatch™ Constrained Accessible Route
        """
        source = self._find_nearest_node(origin_lat, origin_lon)
        target = self._find_nearest_node(dest_lat, dest_lon)

        if source == target:
            return []

        # 1. Direct Shortest Path
        try:
            shortest_path = nx.shortest_path(self.graph, source=source, target=target, weight="length")
            shortest_route = self._assemble_route(shortest_path, profile, active_obstacles, label="Direct Route")
        except nx.NetworkXNoPath:
            shortest_route = None

        # 2. Accessible Path with Dynamic Weighting
        def access_weight(u: int, v: int, edge_dict: dict) -> float:
            data = edge_dict.get(0, edge_dict)
            base_len = float(data.get("length", 10.0))
            is_steps = data.get("highway") == "steps" or "step" in str(data.get("highway", ""))

            # Hard Constraint Check
            if profile.requires_step_free and is_steps:
                return float("inf")

            penalty = 1.0
            # Width constraint
            try:
                width = float(data.get("width", 1.5))
                if width < profile.min_width_meters:
                    if profile.requires_step_free:
                        return float("inf")
                    penalty += 3.0
            except (ValueError, TypeError):
                pass

            # Obstacle check
            if active_obstacles:
                edge_lat = (self.graph.nodes[u]["y"] + self.graph.nodes[v]["y"]) / 2.0
                edge_lon = (self.graph.nodes[u]["x"] + self.graph.nodes[v]["x"]) / 2.0
                for obs in active_obstacles:
                    if haversine_distance(edge_lat, edge_lon, obs.latitude, obs.longitude) < 25.0:
                        if profile.avoid_unverified_obstacles:
                            return float("inf")
                        penalty += 10.0

            return base_len * penalty

        try:
            accessible_path = nx.shortest_path(self.graph, source=source, target=target, weight=access_weight)
            accessible_route = self._assemble_route(accessible_path, profile, active_obstacles, label="AccessDNA™ Optimized Route")
        except nx.NetworkXNoPath:
            accessible_route = None

        results = []
        if accessible_route:
            results.append(accessible_route)
        if shortest_route and (not accessible_route or shortest_route.nodes != accessible_route.nodes):
            results.append(shortest_route)

        return results

    def _assemble_route(
        self,
        node_list: list[int],
        profile: MobilityProfileSchema,
        active_obstacles: list[Any] | None,
        label: str
    ) -> CalculatedRoute:
        coords = []
        total_dist = 0.0
        has_stairs = False
        all_smooth = True
        max_slope = 0.0
        missing_count = 0

        for idx in range(len(node_list) - 1):
            u = node_list[idx]
            v = node_list[idx + 1]
            u_data = self.graph.nodes[u]
            coords.append((u_data["y"], u_data["x"]))

            # Extract edge attributes
            edge_data = self.graph.get_edge_data(u, v)
            data = edge_data.get(0, edge_data) if edge_data else {}

            total_dist += float(data.get("length", 10.0))
            if data.get("highway") == "steps":
                has_stairs = True
            if data.get("surface") not in ("paved", "asphalt", "concrete"):
                all_smooth = False
            try:
                slope_str = str(data.get("incline", "0%")).replace("%", "")
                max_slope = max(max_slope, float(slope_str))
            except ValueError:
                missing_count += 1

        # Append terminal coordinate
        target_data = self.graph.nodes[node_list[-1]]
        coords.append((target_data["y"], target_data["x"]))

        # Aggregate segment evaluation
        segment_rep = SegmentAttributes(
            length_m=total_dist,
            is_step_free=(not has_stairs),
            surface_smooth=all_smooth,
            estimated_slope_pct=max_slope if max_slope > 0 else None,
            width_m=1.8,
            curb_ramp_present=True if not has_stairs else False,
            active_obstacle_count=0
        )
        dna_score = compute_access_dna(segment_rep, profile)

        # Average pedestrian walking pace with wheelchair baseline: ~0.9 m/s (3.24 km/h)
        travel_time_min = round(total_dist / (0.9 * 60.0), 1)

        is_accessible = dna_score.overall_score >= 60.0 and (not has_stairs if profile.requires_step_free else True)

        return CalculatedRoute(
            path_coords=coords,
            total_distance_m=round(total_dist, 1),
            estimated_time_min=travel_time_min,
            dna_score=dna_score,
            nodes=node_list,
            is_accessible=is_accessible,
            summary_label=label
        )
