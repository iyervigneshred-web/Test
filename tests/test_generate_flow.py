from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_from_youtube_dry_run():
    payload = {
        "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "output_dir": "./outputs/test",
        "desired_clip_count": 2,
        "clip_length_seconds": 45,
        "watermark_asset_path": "./assets/julian-watermark.png",
        "dry_run": True,
    }
    response = client.post("/generate/from-youtube", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body["clips"]) == 2
    assert len(body["executed_commands"]) >= 4
    assert body["source_video_path"].endswith("source.mp4")
