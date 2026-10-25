"""TrustLayer™ & BarrierPulse™ Community Verification Algorithms."""
from datetime import datetime, timezone
import math


def compute_barrier_pulse_freshness(created_at: datetime, half_life_days: float = 30.0) -> float:
    """Decays report influence over time via exponential half-life formula.
    
    Freshness = e^(-ln(2) * delta_days / half_life)
    """
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    delta_days = max(0.0, (now - created_at).total_seconds() / 86400.0)
    decay_constant = math.log(2) / half_life_days
    return math.exp(-decay_constant * delta_days)


def calculate_trust_layer_score(
    confirmations_count: int,
    disputes_count: int,
    author_reputation: int,
    created_at: datetime
) -> float:
    """Computes a transparent trust confidence score between 0.05 and 1.0.
    
    Prevents single-user bias and integrates temporal freshness.
    """
    freshness = compute_barrier_pulse_freshness(created_at)
    author_factor = min(max(author_reputation, 1), 100) / 100.0

    # Net balance of confirmations vs disputes
    net_votes = confirmations_count - (disputes_count * 1.5)
    
    # Sigmoidal vote weight: 1 / (1 + e^(-0.8 * net_votes))
    vote_confidence = 1.0 / (1.0 + math.exp(-0.8 * net_votes)) if net_votes >= 0 else 0.1

    final_score = (vote_confidence * 0.50) + (freshness * 0.30) + (author_factor * 0.20)
    return round(min(max(final_score, 0.05), 1.0), 3)
