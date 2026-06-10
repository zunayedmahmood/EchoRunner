# EchoRunner Workplan + Asset and Sound Library

EchoRunner is a blind-first sound-maze chase game planned for **Python + Pygame** with **OpenAL / OpenAL Soft** for spatial/directional audio.

This package contains the updated implementation workplan, visual asset library, generated SFX, generated speech audio files, starter level JSONs, HCI study templates, run scripts, and implementation scaffolding.

## Key update from the previous package

- Project renamed to **EchoRunner**.
- Main implementation stack changed to **Python 3.11+ + Pygame/Pygame-CE**.
- Spatial gameplay audio is designed around **OpenAL**, not Pygame mixer.
- Speech files are now generated as WAV files in English and Bangla draft folders.
- Added a dedicated player-facing controls/goals/onboarding file.
- Expanded game workflow, state machine, tutorial behaviour, OpenAL integration, cross-OS packaging, and testing docs.

## Quick Start & Setup

### 1. Setup Virtual Environment
Run the setup script for your platform:
- **Linux/macOS**: `bash scripts/setup_venv.sh`
- **Windows**: Run `scripts/setup_venv.ps1` in PowerShell

### 2. Setup OpenAL Soft (Spatial Audio)
EchoRunner uses OpenAL for 3D binaural spatial audio. To install it or download the required DLL automatically, run:
```bash
# On Linux/macOS:
python3 scripts/setup_openal.py

# On Windows:
python scripts/setup_openal.py
```
This script will:
- **Windows**: Automatically download the official OpenAL Soft binaries and place `OpenAL32.dll` directly in the project root folder.
- **Linux**: Attempt to install system-wide OpenAL (`libopenal1` / `openal-soft`) using `apt-get` or `dnf`.
- **macOS**: Attempt to install `openal-soft` using Homebrew.

### 3. Run the Game
- **Linux/macOS**: `bash scripts/run_game.sh`
- **Windows**: `scripts/run_game.bat`

## Start reading

1. `docs/01_PROJECT_MASTERPLAN_ARCHITECTURE.md`
2. `docs/06_OPENAL_PYGAME_SPATIAL_AUDIO_IMPLEMENTATION.md`
3. `docs/08_PLAYER_CONTROLS_GOALS_ONBOARDING_SCRIPT.md`
4. `docs/12_TESTING_QA_RESEARCH_PROTOCOL_RUN_COMMANDS.md`

## Important note

Generated audio and art assets are implementation placeholders. They are original and usable for prototyping, but final release should replace them with professionally produced and user-tested assets while keeping filenames and cue meanings stable.
