from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[1]
manifest = root / "assetLibrary" / "manifest.json"
errors = []

if not manifest.exists():
    errors.append("missing assetLibrary/manifest.json")
else:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assets = data.get("assets", [])
        if not assets:
            errors.append("assets list in manifest is empty")
        for item in assets:
            if "path" not in item:
                errors.append(f"missing path key in asset item: {item}")
                continue
            path = root / item["path"]
            if not path.exists():
                errors.append(f"missing asset file: {item['path']}")
            elif path.suffix.lower().lstrip(".") != item.get("format", "").lower():
                errors.append(f"format mismatch for asset: {item['path']} (expected {item.get('format')})")
    except Exception as exc:
        errors.append(f"failed to parse asset manifest: {exc}")

if errors:
    print("Visual asset manifest validation failed:")
    print("\n".join(errors))
    sys.exit(1)

print("Visual asset manifest validation passed")
