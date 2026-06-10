from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[1]
levels_dir = root / "levels"
errors = []

if not levels_dir.exists() or not levels_dir.is_dir():
    errors.append("missing levels directory")
else:
    level_files = list(levels_dir.glob("*.json"))
    if not level_files:
        errors.append("no level json files found in levels directory")
    
    for lfile in level_files:
        try:
            content = lfile.read_text(encoding="utf-8")
            data = json.loads(content)
            
            # Check mandatory keys
            for key in ("level_id", "name", "grid", "legend", "enemy_rules"):
                if key not in data:
                    errors.append(f"{lfile.name}: missing key '{key}'")
            
            if "grid" in data:
                grid = data["grid"]
                if not isinstance(grid, list) or not all(isinstance(row, str) for row in grid):
                    errors.append(f"{lfile.name}: 'grid' must be a list of strings")
                    continue
                if not grid:
                    errors.append(f"{lfile.name}: 'grid' is empty")
                    continue
                
                # Check grid row length consistency
                row_len = len(grid[0])
                for idx, row in enumerate(grid):
                    if len(row) != row_len:
                        errors.append(f"{lfile.name}: grid row {idx} has length {len(row)}, expected {row_len}")
                
                # Check player spawn presence
                has_player = any("P" in row for row in grid)
                if not has_player:
                    errors.append(f"{lfile.name}: grid lacks player start ('P')")
                
                # Check boundaries for enemy rules
                if "enemy_rules" in data:
                    for idx, rule in enumerate(data["enemy_rules"]):
                        if "start" not in rule:
                            errors.append(f"{lfile.name}: enemy_rules index {idx} lacks 'start' position")
                            continue
                        pos = rule["start"]
                        if not isinstance(pos, list) or len(pos) != 2:
                            errors.append(f"{lfile.name}: enemy start position {pos} must be [x, y] coordinates")
                            continue
                        x, y = pos
                        if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]):
                            errors.append(f"{lfile.name}: enemy start {pos} out of grid bounds")
                            
                # Check boundaries for audio landmarks
                if "audio_landmarks" in data:
                    for idx, landmark in enumerate(data["audio_landmarks"]):
                        if "position" not in landmark:
                            errors.append(f"{lfile.name}: landmark index {idx} lacks 'position'")
                            continue
                        pos = landmark["position"]
                        if not isinstance(pos, list) or len(pos) != 2:
                            errors.append(f"{lfile.name}: landmark position {pos} must be [x, y] coordinates")
                            continue
                        x, y = pos
                        if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[0]):
                            errors.append(f"{lfile.name}: landmark position {pos} out of grid bounds")
                            
        except Exception as exc:
            errors.append(f"{lfile.name}: JSON parse failure: {exc}")

if errors:
    print("Level validation failed:")
    print("\n".join(errors))
    sys.exit(1)

print("All level configuration files passed validation")
