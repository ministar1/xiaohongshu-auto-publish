from __future__ import annotations

import json

import pytest

from xiaohongshu_auto_publish.errors import MediaValidationError
from xiaohongshu_auto_publish.media.manifest import MediaManifest, MediaValidationStage, validate_image_file


def test_media_manifest_missing_file_warns_then_blocks(app_config: object) -> None:
    task_dir = app_config.project_root / "workspace" / "task-1"
    (task_dir / "media").mkdir(parents=True)
    (task_dir / "media" / "media_manifest.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "path": "media/images/a.png",
                        "role": "cover",
                        "width": 100,
                        "height": 100,
                        "ratio": "1:1",
                        "description": "图",
                        "is_cover_candidate": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    manifest = MediaManifest.load(task_dir)
    assert manifest.validate(MediaValidationStage.FORMAT, require_cover=True).issues[0].severity == "warn"
    assert manifest.validate(MediaValidationStage.PACKAGE, require_cover=True).issues[0].severity == "block"


def test_validate_image_file_magic_bytes(app_config: object) -> None:
    path = app_config.project_root / "a.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\nxxxx")
    assert validate_image_file(path).passed
    bad = app_config.project_root / "bad.png"
    bad.write_bytes(b"bad")
    assert not validate_image_file(bad).passed


def test_media_manifest_rejects_path_escape(app_config: object) -> None:
    task_dir = app_config.project_root / "workspace" / "task-1"
    (task_dir / "media").mkdir(parents=True)
    (task_dir / "media" / "media_manifest.json").write_text(
        '{"items":[{"path":"../x.png","role":"cover","width":1,"height":1,"ratio":"1:1","description":"x","is_cover_candidate":true}]}',
        encoding="utf-8",
    )
    with pytest.raises(MediaValidationError):
        MediaManifest.load(task_dir)
