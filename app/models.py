from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Platform(str, Enum):
    tiktok = "tiktok"
    instagram = "instagram"
    youtube = "youtube"


class ClipStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class WatermarkConfig(BaseModel):
    asset_path: str = Field(default="./assets/julian-watermark.png")
    size_pct: int = Field(default=25, ge=5, le=60)
    opacity_pct: int = Field(default=80, ge=20, le=100)
    position: str = Field(default="below_subtitles")


class MasterEditorRules(BaseModel):
    enforce_template: bool = True
    watermark_required: bool = True
    min_caption_confidence: float = Field(default=0.92, ge=0, le=1)
    min_hook_score: float = Field(default=0.7, ge=0, le=1)
    no_mid_word_cuts: bool = True
    speaker_visible_min_ratio: float = Field(default=0.6, ge=0, le=1)


class StyleTemplate(BaseModel):
    name: str
    description: str
    captions_style: str
    framing_style: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    target_platforms: List[Platform] = Field(
        default_factory=lambda: [Platform.tiktok, Platform.instagram, Platform.youtube]
    )


class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    target_platforms: List[Platform]
    watermark: WatermarkConfig = Field(default_factory=WatermarkConfig)
    rules: MasterEditorRules = Field(default_factory=MasterEditorRules)
    templates: List[StyleTemplate] = Field(default_factory=list)
    created_at: datetime


class YouTubeIngestRequest(BaseModel):
    project_id: str
    youtube_url: HttpUrl
    desired_clip_count: int = Field(default=12, ge=1, le=50)


class GenerateFromYouTubeRequest(BaseModel):
    youtube_url: HttpUrl
    output_dir: str = Field(default="./outputs")
    desired_clip_count: int = Field(default=10, ge=1, le=20)
    clip_length_seconds: int = Field(default=45, ge=15, le=90)
    watermark_asset_path: str = Field(default="./assets/julian-watermark.png")
    dry_run: bool = True


class ClipCandidate(BaseModel):
    id: str
    title: str
    reason: str
    score: float = Field(ge=0, le=1)
    start_seconds: float
    end_seconds: float
    status: ClipStatus = ClipStatus.queued


class GeneratedClip(BaseModel):
    path: str
    score: float
    start_seconds: float
    end_seconds: float


class GenerateRunResult(BaseModel):
    source_video_path: str
    transcript_path: Optional[str] = None
    clips: List[GeneratedClip] = Field(default_factory=list)
    executed_commands: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class WeeklyLearningDecision(BaseModel):
    week_start: datetime
    approved_by_human: bool
    approved_model_version: Optional[str] = None
    notes: Optional[str] = None


class LearningMetric(BaseModel):
    name: str
    baseline: float
    current: float
    goal: float


class LearningReport(BaseModel):
    week_start: datetime
    metrics: List[LearningMetric]
    recommendation: str
    ready_for_human_review: bool = True
