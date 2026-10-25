"""RouteExplain™ Explainable AI Route Justification Generator."""
from core.routing_engine import CalculatedRoute
from core.schemas import MobilityProfileSchema


def generate_route_explanation(route: CalculatedRoute, profile: MobilityProfileSchema) -> dict[str, str]:
    """Produces explainable insights detailing route recommendations and uncertainties."""
    dna = route.dna_score
    positives = []
    cautions = []

    if dna.step_free_score == 100.0:
        positives.append("100% verified step-free path compliant with zero-step policy.")
    elif profile.requires_step_free:
        cautions.append("Contains steps or unverified level changes which violate profile constraints.")

    if dna.surface_score >= 80.0:
        positives.append("Smooth pavement suitable for low-rolling-resistance mobility aids.")
    else:
        cautions.append("Irregular surface or cobblestones reported along sections.")

    if dna.slope_score == 100.0:
        positives.append(f"Incline remains safely below maximum configured slope ({profile.max_slope_pct}%).")
    else:
        cautions.append(f"Exceeds desired {profile.max_slope_pct}% grade; requires increased push exertion or assist.")

    # Uncertainty disclosure
    uncertainty_text = (
        "High confidence based on verified OSM data and local confirmations."
        if dna.confidence_score >= 80.0
        else f"Data uncertainty ({100.0 - dna.confidence_score:.0f}% unverified). " + "; ".join(dna.missing_data_reasons)
    )

    return {
        "summary": f"{route.summary_label} scored {dna.overall_score}/100 AccessDNA™ suitability.",
        "positives": " ".join(positives) if positives else "Direct transit corridor.",
        "cautions": " ".join(cautions) if cautions else "No major structural barriers reported.",
        "uncertainty": uncertainty_text,
        "disclaimer": "Safety Guarantee Notice: Crowd reports and public GIS maps can change unexpectedly due to construction or weather. Always assess live conditions before proceeding."
    }
