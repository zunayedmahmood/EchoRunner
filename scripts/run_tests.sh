#!/usr/bin/env bash
set -e
source .venv/bin/activate 2>/dev/null || true
pytest tests/unit
pytest tests/integration
python scripts/validate_audio_manifest.py
python scripts/validate_assets.py
python scripts/validate_levels.py
