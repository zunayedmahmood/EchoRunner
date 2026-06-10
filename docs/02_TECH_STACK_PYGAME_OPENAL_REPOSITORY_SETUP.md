# EchoRunner Tech Stack, Python/Pygame Setup, and Repository Plan

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Technology choices

### 1.1 Python 3.11+

Use Python because the team can iterate quickly, write readable gameplay systems, and integrate HCI research tooling without heavy engine overhead.

Recommended version:

```bash
python --version
# Python 3.11.x or 3.12.x
```

### 1.2 Pygame or Pygame-CE

Use Pygame for:

- window creation;
- keyboard events;
- fixed game loop timing;
- 2D trainer dashboard;
- image loading and sprite drawing;
- debug overlays;
- lightweight packaging.

Recommended package:

```text
pygame-ce>=2.5
```

Pygame-CE is usually preferred for new projects because it is actively maintained, but plain `pygame` can be used if environment compatibility requires it.

### 1.3 OpenAL Soft

Use OpenAL Soft as the preferred runtime implementation of OpenAL for cross-platform spatial audio.

OpenAL responsibilities:

- device/context management;
- sound buffers;
- positional sound sources;
- listener position/orientation;
- gain/pitch/rolloff;
- mono spatial SFX;
- speech and UI cues as non-spatial or listener-relative sources.

### 1.4 Python OpenAL binding approach

The team has two practical choices:

#### Option A — Thin `ctypes` wrapper around OpenAL Soft

This is the recommended long-term path because it avoids dependency uncertainty.

Create:

```text
src/echorunner/audio/openal_ctypes.py
```

It loads:

- Windows: `OpenAL32.dll`
- Linux: `libopenal.so.1` or `libopenal.so`
- macOS: `libopenal.dylib` or framework path

It exposes only the subset EchoRunner needs:

```python
open_device()
close_device()
create_context()
destroy_context()
gen_buffers()
buffer_data()
gen_sources()
source_play()
source_stop()
source_set_position()
source_set_gain()
listener_set_position()
listener_set_orientation()
get_error()
```

#### Option B — Existing Python OpenAL package

This can speed up prototyping, but the team must verify maintenance, packaging, and binary compatibility. If used, wrap it behind the same internal interface so it can be replaced later.

### 1.5 Pygame mixer policy

Do not build core gameplay audio on `pygame.mixer` because it is mainly channel-based 2D mixing. It does not give the source/listener spatial model EchoRunner needs.

Allowed uses:

- emergency fallback if OpenAL fails;
- quick developer preview;
- optional non-spatial menu playback during early MVP.

Final target:

```text
OpenAL = real gameplay audio
Pygame = input + trainer graphics + timing
```

## 2. Dependency file

`requirements.txt` should start like this:

```text
pygame-ce>=2.5.0
numpy>=1.26
PyYAML>=6.0
pydantic>=2.7
pytest>=8.0
pytest-cov>=5.0
rich>=13.7
```

Optional but useful:

```text
soundfile>=0.12
platformdirs>=4.2
pyinstaller>=6.0
```

For audio generation during development, use system tools:

```text
espeak or espeak-ng for generated speech placeholders
ffmpeg for audio conversion/normalization if available
```

## 3. `pyproject.toml` target

```toml
[project]
name = "echorunner"
version = "0.1.0"
description = "Blind-first Python/Pygame sound-maze game with OpenAL spatial audio"
requires-python = ">=3.11"
dependencies = [
    "pygame-ce>=2.5.0",
    "numpy>=1.26",
    "PyYAML>=6.0",
    "pydantic>=2.7",
    "rich>=13.7",
]

[project.scripts]
echorunner = "echorunner.main:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

## 4. Environment setup commands

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m echorunner
```

### Linux/macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m echorunner
```

## 5. OpenAL installation commands

### Windows

Bundle OpenAL Soft with the packaged build where possible. During development, install OpenAL Soft and ensure `OpenAL32.dll` is on PATH or next to the executable.

Runtime lookup order:

```text
1. packaged lib/ directory
2. executable directory
3. system PATH
4. known OpenAL Soft install directory
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install libopenal1 libopenal-dev
```

### Fedora

```bash
sudo dnf install openal-soft openal-soft-devel
```

### Arch

```bash
sudo pacman -S openal
```

### macOS

```bash
brew install openal-soft
```

The app should still show a useful error if OpenAL is missing:

```text
EchoRunner could not start spatial audio.
Install OpenAL Soft or switch to fallback audio mode from settings.
```

## 6. Recommended module map

```text
src/echorunner/main.py
    Entry point.

src/echorunner/app.py
    Boot, state loop, shutdown.

src/echorunner/input/mapper.py
    Raw Pygame keys to commands.

src/echorunner/simulation/world.py
    Level grid, tile metadata, coordinate system.

src/echorunner/simulation/player.py
    Player movement, queued turns, collision with walls.

src/echorunner/simulation/enemy.py
    Enemy state machine and targeting.

src/echorunner/simulation/rules.py
    Pellets, power mode, level clear, life loss.

src/echorunner/cues/planner.py
    Creates CueEvents from world state.

src/echorunner/audio/openal_backend.py
    High-level OpenAL backend.

src/echorunner/audio/openal_ctypes.py
    Low-level OpenAL wrapper.

src/echorunner/audio/speech.py
    Speech line selection and playback.

src/echorunner/trainer_view/renderer.py
    Visual mirror.

src/echorunner/telemetry/logger.py
    JSONL event logging.
```

## 7. File formats

### Level JSON

```json
{
  "level_id": "level_01_training_loop",
  "name": "Training Loop",
  "grid": ["########", "#P....E#", "#.#.##.#", "#o....R#", "########"],
  "legend": {
    "#": "wall",
    ".": "echo_orb",
    "P": "player_start",
    "E": "enemy_start",
    "o": "resonance_core",
    "R": "safe_reorient"
  },
  "audio_landmarks": [
    {"id": "safe_loop", "position": [6,3], "cue": "landmark_safe_loop"}
  ]
}
```

### Cue manifest

```json
{
  "cue_id": "enemy_near_red",
  "file": "soundLibrary/wav/enemy_near_red.wav",
  "priority": 100,
  "spatial": true,
  "loop": false,
  "duck_music_db": -12,
  "description": "Immediate enemy collision warning"
}
```

### Telemetry event

```json
{"t": 12.240, "type": "cue_played", "cue_id": "enemy_near_red", "threat": "red"}
```

## 8. Development rules

- The simulation layer must run without audio or graphics.
- Audio cue planning must be deterministic given the same state.
- No raw key constants outside input mapper.
- No direct OpenAL calls outside the audio backend.
- No visual-only state.
- All settings must be changeable by keyboard.
- Every mode change must be spoken or earcon-coded.
- Every failure must have a replay/explanation path.
