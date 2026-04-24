import json
import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.models import GenerateFromYouTubeRequest, GenerateRunResult, GeneratedClip
from app.services.pipeline import build_ffmpeg_watermark_filter
from app.services.scoring import ViralFeatureSet, viral_score


@dataclass
class Segment:
    start: float
    end: float
    text: str


def _run(cmd: list[str], dry_run: bool, executed_commands: list[str]) -> subprocess.CompletedProcess | None:
    printable = " ".join(shlex.quote(c) for c in cmd)
    executed_commands.append(printable)
    if dry_run:
        return None
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def _tool_missing(tool: str) -> bool:
    return shutil.which(tool) is None


def _download_video(url: str, output_dir: Path, dry_run: bool, executed_commands: list[str]) -> Path:
    output_template = output_dir / "source.%(ext)s"
    cmd = ["yt-dlp", "-f", "mp4", "-o", str(output_template), url]
    _run(cmd, dry_run, executed_commands)
    if dry_run:
        return output_dir / "source.mp4"

    for file in output_dir.iterdir():
        if file.name.startswith("source.") and file.suffix in {".mp4", ".mkv", ".webm"}:
            return file
    raise FileNotFoundError("Downloaded source video not found")


def _transcribe(video_path: Path, output_dir: Path, dry_run: bool, executed_commands: list[str]) -> Path:
    transcript_path = output_dir / "transcript.json"
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    _run(cmd, dry_run, executed_commands)

    dummy = {
        "segments": [
            {"start": 10, "end": 55, "text": "Strong hook about human performance and discipline"},
            {"start": 70, "end": 115, "text": "Controversial point with emotion spike and practical advice"},
            {"start": 130, "end": 175, "text": "Story moment with surprise and clear takeaway"},
        ]
    }
    transcript_path.write_text(json.dumps(dummy, indent=2))
    return transcript_path


def _load_segments(transcript_path: Path) -> list[Segment]:
    raw = json.loads(transcript_path.read_text())
    return [Segment(start=s["start"], end=s["end"], text=s["text"]) for s in raw.get("segments", [])]


def _score_segment(segment: Segment) -> float:
    text = segment.text.lower()
    features = ViralFeatureSet(
        hook_strength=0.85 if "hook" in text or "controvers" in text or "surprise" in text else 0.62,
        emotion_peak=0.83 if "emotion" in text or "controvers" in text else 0.58,
        novelty=0.78 if "surprise" in text or "practical" in text else 0.60,
        clarity=0.8,
        retention_proxy=0.77 if "story" in text or "takeaway" in text else 0.63,
    )
    return viral_score(features)


def _build_clip_command(
    source_video: Path,
    start: float,
    duration: int,
    output_path: Path,
    watermark_path: str,
) -> list[str]:
    filter_graph = build_ffmpeg_watermark_filter(1080, 1920)
    return [
        "ffmpeg",
        "-y",
        "-ss",
        str(round(start, 2)),
        "-i",
        str(source_video),
        "-i",
        watermark_path,
        "-t",
        str(duration),
        "-filter_complex",
        filter_graph,
        "-map",
        "[outv]",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        str(output_path),
    ]


def generate_opus_like_clips(payload: GenerateFromYouTubeRequest) -> GenerateRunResult:
    output_dir = Path(payload.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    executed_commands: list[str] = []
    warnings: list[str] = []

    for tool in ["yt-dlp", "ffmpeg", "ffprobe"]:
        if _tool_missing(tool):
            warnings.append(f"{tool} is not installed; generation can only run in dry-run mode.")

    dry_run = payload.dry_run or bool(warnings)

    source_video = _download_video(str(payload.youtube_url), output_dir, dry_run, executed_commands)
    transcript = _transcribe(source_video, output_dir, dry_run, executed_commands)
    segments = _load_segments(transcript)

    if not segments:
        warnings.append("No transcript segments were found; no clips generated.")

    ranked = sorted(((s, _score_segment(s)) for s in segments), key=lambda item: item[1], reverse=True)
    top = ranked[: payload.desired_clip_count]

    clips: list[GeneratedClip] = []
    for idx, (seg, score) in enumerate(top, start=1):
        clip_name = f"clip_{idx:02d}.mp4"
        output_path = output_dir / clip_name
        cmd = _build_clip_command(
            source_video=source_video,
            start=seg.start,
            duration=payload.clip_length_seconds,
            output_path=output_path,
            watermark_path=payload.watermark_asset_path,
        )
        _run(cmd, dry_run, executed_commands)
        clips.append(
            GeneratedClip(
                path=str(output_path),
                score=score,
                start_seconds=seg.start,
                end_seconds=min(seg.end, seg.start + payload.clip_length_seconds),
            )
        )

    if not os.path.exists(payload.watermark_asset_path):
        warnings.append(
            f"Watermark asset not found at {payload.watermark_asset_path}. Provide PNG file before real rendering."
        )

    return GenerateRunResult(
        source_video_path=str(source_video),
        transcript_path=str(transcript),
        clips=clips,
        executed_commands=executed_commands,
        warnings=warnings,
    )
