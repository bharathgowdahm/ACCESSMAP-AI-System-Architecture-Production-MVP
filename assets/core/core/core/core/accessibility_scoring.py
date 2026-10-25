"""AccessDNA™ Personalized Accessibility Scoring Engine.

Computes a deterministic route suitability score (0-100) and an explicit
uncertainty metric based on data completeness and community reports.
"""
from dataclasses import dataclass
from core.schemas import MobilityProfileSchema


@dataclass
class SegmentAttributes:
    length_m: float
    is_step_free: bool | None
    surface_smooth: bool | None
    estimated_slope_pct: float | None
    width_m: float | None
    curb_ramp_present: bool | None
    active_obstacle_count: int = 0


@dataclass
class AccessDNAScore:
    overall_score: float        # 0 to 100
    confidence_score: float     # 0 to 100
    step_free_score: float
    surface_score: float
    slope_score: float
    width_score: float
    curb_ramp_score: float
    obstacle_penalty: float
    missing_data_reasons: list[str]


def compute_access_dna(segment: SegmentAttributes, profile: MobilityProfileSchema) -> AccessDNAScore:
    """Calculates weighted multi-factor suitability with explicit uncertainty tracking."""
    reasons: list[str] = []
    known_factors = 0
    total_factors = 5

    # 1. Step-Free Connectivity (Weight 25%)
    if segment.is_step_free is None:
        reasons.append("Step-free status unknown")
        step_free_val = 40.0  # Conservative unknown estimate
    else:
        known_factors += 1
        if profile.requires_step_free and not segment.is_step_free:
            step_free_val = 0.0
        else:
            step_free_val = 100.0 if segment.is_step_free else 30.0

    # 2. Surface Quality (Weight 20%)
    if segment.surface_smooth is None:
        reasons.append("Surface smoothness not verified")
        surface_val = 50.0
    else:
        known_factors += 1
        if profile.avoid_unpaved and not segment.surface_smooth:
            surface_val = 20.0
        else:
            surface_val = 100.0 if segment.surface_smooth else 40.0

    # 3. Slope Suitability (Weight 20%)
    if segment.estimated_slope_pct is None:
        reasons.append("Incline and elevation data missing")
        slope_val = 50.0
    else:
        known_factors += 1
        if segment.estimated_slope_pct > profile.max_slope_pct:
            excess = segment.estimated_slope_pct - profile.max_slope_pct
            slope_val = max(0.0, 100.0 - (excess * 25.0))
        else:
            slope_val = 100.0

    # 4. Pathway Width (Weight 15%)
    if segment.width_m is None:
        reasons.append("Pathway clearance width not mapped")
        width_val = 50.0
    else:
        known_factors += 1
        if segment.width_m < profile.min_width_meters:
            width_val = 0.0
        else:
            width_val = 100.0

    # 5. Curb Ramp Availability (Weight 10%)
    if segment.curb_ramp_present is None:
        reasons.append("Curb transition status unknown")
        curb_val = 40.0
    else:
        known_factors += 1
        curb_val = 100.0 if segment.curb_ramp_present else 10.0

    # 6. Obstacle Penalties (Weight 10%)
    penalty = min(segment.active_obstacle_count * 30.0, 100.0)
    obstacle_val = max(0.0, 100.0 - penalty)

    # Weighted calculation
    overall = (
        (step_free_val * 0.25) +
        (surface_val * 0.20) +
        (slope_val * 0.20) +
        (width_val * 0.15) +
        (curb_val * 0.10) +
        (obstacle_val * 0.10)
    )

    confidence = (known_factors / total_factors) * 100.0

    return AccessDNAScore(
        overall_score=round(overall, 1),
        confidence_score=round(confidence, 1),
        step_free_score=step_free_val,
        surface_score=surface_val,
        slope_score=slope_val,
        width_score=width_val,
        curb_ramp_score=curb_val,
        obstacle_penalty=penalty,
        missing_data_reasons=reasons
    )
