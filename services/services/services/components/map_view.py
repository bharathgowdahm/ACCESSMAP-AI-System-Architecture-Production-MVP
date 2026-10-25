"""Interactive Map Component with WCAG Color-Compliant Accessible Overlays."""
from core.models import AccessibilityReport
from core.routing_engine import CalculatedRoute
import folium
from streamlit_folium import st_folium


def render_accessible_map(
    center_lat: float,
    center_lon: float,
    zoom_start: int = 15,
    routes: list[CalculatedRoute] | None = None,
    reports: list[AccessibilityReport] | None = None
) -> dict:
    """Renders Folium map with high-contrast color scheme:
    - Primary Route: Electric Violet (#7456FF)
    - Shortest/Inaccessible Alternative: Amber (#F59E0B)
    - Obstacle Markers: High-visibility Red (#EF4444)
    """
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles="CartoDB positron",  # High-contrast, clean pedestrian readability
        attr="&copy; OpenStreetMap contributors &copy; CARTO"
    )

    # Render Reports
    if reports:
        for r in reports:
            color = "#EF4444" if r.severity >= 4 else "#F59E0B"
            folium.CircleMarker(
                location=[r.latitude, r.longitude],
                radius=7,
                color="#0B1020",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.85,
                tooltip=f"Barrier: {r.category} (Severity {r.severity}/5)",
                popup=folium.Popup(f"<b>{r.title}</b><br>{r.description}<br>Status: {r.status}", max_width=250)
            ).add_to(m)

    # Render Routes
    if routes:
        colors = ["#7456FF", "#F59E0B", "#00BFA6"]
        for idx, route in enumerate(routes):
            color = colors[idx % len(colors)]
            weight = 6 if idx == 0 else 4
            opacity = 0.9 if idx == 0 else 0.6
            
            folium.PolyLine(
                locations=route.path_coords,
                color=color,
                weight=weight,
                opacity=opacity,
                tooltip=f"{route.summary_label} — Score: {route.dna_score.overall_score}/100"
            ).add_to(m)

            # Route Endpoints
            folium.Marker(
                location=route.path_coords[0],
                popup="Start Point",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(m)
            folium.Marker(
                location=route.path_coords[-1],
                popup="Destination",
                icon=folium.Icon(color="black", icon="flag")
            ).add_to(m)

    return st_folium(m, width="100%", height=520, returned_objects=[])
