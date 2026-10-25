"""OSM Overpass API & Street Network Fetcher with robust fallback."""
import logging
from core.routing_engine import create_synthetic_accessible_subgraph
import networkx as nx

logger = logging.getLogger(__name__)


def fetch_walk_network(center_lat: float, center_lon: float, dist_m: int = 800) -> nx.MultiDiGraph:
    """Fetches real pedestrian network from OpenStreetMap via OSMnx.
    
    Falls back gracefully to a synthetic accessible graph on network/rate-limit timeout.
    """
    try:
        import osmnx as ox
        # Configure strict pedestrian routing
        ox.settings.log_console = False
        ox.settings.use_cache = True
        ox.settings.timeout = 10
        
        g = ox.graph_from_point(
            (center_lat, center_lon),
            dist=dist_m,
            network_type="walk",
            simplify=True
        )
        if len(g.nodes) > 0:
            return g
    except Exception as exc:
        logger.warning(f"OSMnx real-time fetch fallback triggered: {exc}")

    # Fallback guarantees 100% runnable offline capability
    return create_synthetic_accessible_subgraph(center_lat, center_lon, radius_m=dist_m)
