from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.models import (
    GenerateFromYouTubeRequest,
    GenerateRunResult,
    Project,
    ProjectCreate,
    StyleTemplate,
    WeeklyLearningDecision,
    YouTubeIngestRequest,
)
from app.services.clip_engine import generate_opus_like_clips
from app.services.pipeline import (
    DEFAULT_RULES,
    DEFAULT_WATERMARK,
    build_ffmpeg_watermark_filter,
    generate_clip_candidates,
    weekly_learning_report,
)

app = FastAPI(title="Julian Clips Engine", version="0.2.0")

PROJECTS: dict[str, Project] = {}
LEARNING_DECISIONS: list[WeeklyLearningDecision] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/projects", response_model=Project)
def create_project(payload: ProjectCreate) -> Project:
    project = Project(
        id=str(uuid4()),
        name=payload.name,
        description=payload.description,
        target_platforms=payload.target_platforms,
        watermark=DEFAULT_WATERMARK,
        rules=DEFAULT_RULES,
        templates=[
            StyleTemplate(
                name="Julian Core",
                description="Primary podcast clipping style with animated captions.",
                captions_style="bold white, black stroke, keyword highlight in yellow",
                framing_style="active speaker tracking with 9:16 center crop",
            )
        ],
        created_at=datetime.utcnow(),
    )
    PROJECTS[project.id] = project
    return project


@app.get("/projects", response_model=list[Project])
def list_projects() -> list[Project]:
    return list(PROJECTS.values())


@app.post("/ingest/youtube")
def ingest_youtube(payload: YouTubeIngestRequest) -> dict:
    if payload.project_id not in PROJECTS:
        raise HTTPException(status_code=404, detail="project not found")

    clips = generate_clip_candidates(payload.desired_clip_count)
    return {
        "source": str(payload.youtube_url),
        "status": "ingested",
        "clips_generated": len(clips),
        "top_clips": clips[:5],
    }


@app.post("/generate/from-youtube", response_model=GenerateRunResult)
def generate_from_youtube(payload: GenerateFromYouTubeRequest) -> GenerateRunResult:
    return generate_opus_like_clips(payload)


@app.get("/rules/master")
def master_rules() -> dict:
    return {
        "watermark": DEFAULT_WATERMARK,
        "rules": DEFAULT_RULES,
        "ffmpeg_overlay_filter_example": build_ffmpeg_watermark_filter(1080, 1920),
    }


@app.get("/learning/weekly-report")
def learning_weekly_report() -> dict:
    return weekly_learning_report().model_dump()


@app.post("/learning/approve")
def learning_approve(payload: WeeklyLearningDecision) -> dict:
    LEARNING_DECISIONS.append(payload)
    return {
        "saved": True,
        "total_decisions": len(LEARNING_DECISIONS),
        "latest": payload,
    }
