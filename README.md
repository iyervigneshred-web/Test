# Julian Clips Engine

This version is focused on **actually generating Opus-like clips** from a YouTube link (not just mock metadata).

## What it does now

- Accepts a YouTube URL and runs a generation pipeline (`/generate/from-youtube`)
- Downloads source video with `yt-dlp`
- Builds ranked candidate moments using a viral scoring heuristic
- Cuts clips with `ffmpeg` into 9:16 output
- Applies Julian watermark defaults:
  - 25% size
  - 80% opacity
  - positioned below subtitle region
- Returns generated clip paths and exact commands executed
- Supports `dry_run=true` to preview the full pipeline safely

## API Endpoints

- `GET /health`
- `POST /projects`
- `GET /projects`
- `POST /ingest/youtube`
- `POST /generate/from-youtube`
- `GET /rules/master`
- `GET /learning/weekly-report`
- `POST /learning/approve`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open Swagger UI:

- `http://127.0.0.1:8000/docs`

## Example request

```json
{
  "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "output_dir": "./outputs",
  "desired_clip_count": 5,
  "clip_length_seconds": 45,
  "watermark_asset_path": "./assets/julian-watermark.png",
  "dry_run": true
}
```

## Notes

- For real rendering (`dry_run=false`), install `yt-dlp`, `ffmpeg`, and `ffprobe`.
- Current transcription/viral ranking is heuristic-driven and intentionally simple for speed; this is the next area to upgrade.
- This remains a clean-room implementation and does not copy proprietary source code.


## Readiness

- Ready for local MVP testing with `dry_run=true` immediately.
- For full rendering (`dry_run=false`), install runtime binaries and add watermark PNG at `./assets/julian-watermark.png`.
- Includes API smoke tests under `tests/`.
