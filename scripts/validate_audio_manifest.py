from pathlib import Path
import json, wave, sys
root = Path(__file__).resolve().parents[1]
manifest = root / "soundLibrary" / "manifest.json"
errors = []
if not manifest.exists():
    errors.append("missing soundLibrary/manifest.json")
else:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for item in data.get("assets", []):
        path = root / item["path"]
        if not path.exists():
            errors.append(f"missing {item['path']}")
        elif path.suffix.lower() == ".wav":
            try:
                with wave.open(str(path), "rb") as w:
                    if w.getnframes() <= 0:
                        errors.append(f"empty wav {item['path']}")
            except Exception as exc:
                errors.append(f"bad wav {item['path']}: {exc}")
if errors:
    print("Audio manifest validation failed:")
    print("\n".join(errors))
    sys.exit(1)
print("Audio manifest validation passed")
