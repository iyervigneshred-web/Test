from dataclasses import dataclass


@dataclass
class ViralFeatureSet:
    hook_strength: float
    emotion_peak: float
    novelty: float
    clarity: float
    retention_proxy: float


def viral_score(features: ViralFeatureSet) -> float:
    """Simple weighted scoring model used as a placeholder until training loop is connected."""
    score = (
        features.hook_strength * 0.30
        + features.emotion_peak * 0.20
        + features.novelty * 0.20
        + features.clarity * 0.15
        + features.retention_proxy * 0.15
    )
    return max(0.0, min(score, 1.0))


def explain_score(features: ViralFeatureSet) -> str:
    highlights = []
    if features.hook_strength >= 0.75:
        highlights.append("strong opening hook")
    if features.emotion_peak >= 0.7:
        highlights.append("high emotional intensity")
    if features.novelty >= 0.7:
        highlights.append("novel insight")
    if features.retention_proxy >= 0.7:
        highlights.append("high retention potential")
    if not highlights:
        highlights.append("balanced but moderate signals")
    return ", ".join(highlights)
