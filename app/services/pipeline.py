from datetime import datetime
from uuid import uuid4

from app.models import ClipCandidate, LearningMetric, LearningReport, MasterEditorRules, WatermarkConfig
from app.services.scoring import ViralFeatureSet, explain_score, viral_score


DEFAULT_WATERMARK = WatermarkConfig(
    asset_path="./assets/julian-watermark.png",
    size_pct=25,
    opacity_pct=80,
    position="below_subtitles",
)

DEFAULT_RULES = MasterEditorRules(
    enforce_template=True,
    watermark_required=True,
    min_caption_confidence=0.92,
    min_hook_score=0.7,
    no_mid_word_cuts=True,
    speaker_visible_min_ratio=0.6,
)


def build_ffmpeg_watermark_filter(video_width: int, video_height: int) -> str:
    """
    Filter-complex graph:
    1) normalize source to 9:16 canvas
    2) scale watermark to configured size
    3) apply opacity and place watermark below subtitle band
    """
    target_w = int(video_width * DEFAULT_WATERMARK.size_pct / 100)
    margin_x = int(video_width * 0.04)
    subtitle_band_top = int(video_height * 0.78)
    y_pos = max(0, subtitle_band_top + int(video_height * 0.02))
    alpha = DEFAULT_WATERMARK.opacity_pct / 100

    return (
        f"[0:v]scale={video_width}:{video_height}:force_original_aspect_ratio=increase,"
        f"crop={video_width}:{video_height}[base];"
        f"[1:v]scale={target_w}:-1,format=rgba,colorchannelmixer=aa={alpha}[wm];"
        f"[base][wm]overlay={margin_x}:{y_pos}[outv]"
    )


def generate_clip_candidates(desired_count: int) -> list[ClipCandidate]:
    clips = []
    for idx in range(desired_count):
        features = ViralFeatureSet(
            hook_strength=0.72 + (idx % 3) * 0.06,
            emotion_peak=0.61 + (idx % 4) * 0.05,
            novelty=0.58 + (idx % 2) * 0.13,
            clarity=0.80,
            retention_proxy=0.66 + (idx % 5) * 0.04,
        )
        score = viral_score(features)
        clips.append(
            ClipCandidate(
                id=str(uuid4()),
                title=f"Candidate clip {idx + 1}",
                reason=explain_score(features),
                score=score,
                start_seconds=float(idx * 35),
                end_seconds=float(idx * 35 + 45),
            )
        )
    clips.sort(key=lambda c: c.score, reverse=True)
    return clips


def weekly_learning_report() -> LearningReport:
    metrics = [
        LearningMetric(name="avg_watch_time_ratio", baseline=0.34, current=0.41, goal=0.45),
        LearningMetric(name="share_rate", baseline=0.021, current=0.029, goal=0.035),
        LearningMetric(name="hook_retention_3s", baseline=0.62, current=0.71, goal=0.75),
        LearningMetric(name="caption_readability_pass_rate", baseline=0.89, current=0.95, goal=0.97),
    ]
    recommendation = "Approve model if 3 of 4 metrics trend up for two consecutive weeks."
    return LearningReport(
        week_start=datetime.utcnow(),
        metrics=metrics,
        recommendation=recommendation,
        ready_for_human_review=True,
    )
