========================================================================
                      ECHORUNNER - FIRST RUN GUIDE
========================================================================

Welcome to EchoRunner, a spatial audio navigation game designed to be
fully playable without vision.

------------------------------------------------------------------------
QUICK START
------------------------------------------------------------------------
1. Extract all files to a directory on your machine.
2. Launch 'EchoRunner.exe'.
3. Follow the audio prompts to calibrate your headphones (Left/Right).

------------------------------------------------------------------------
DEPENDENCIES & SETUP (ALL OS)
------------------------------------------------------------------------
EchoRunner utilizes OpenAL Soft for realistic 3D binaural audio simulation.

You can configure OpenAL automatically on any operating system by running:
  python scripts/setup_openal.py

- On Windows: This will download 'soft_oal.dll' and place it as 'OpenAL32.dll'
  in the game directory automatically.
- On Linux/macOS: This will try to install the system-wide package via apt-get,
  dnf, or Homebrew.

Alternatively, you can manually download and install OpenAL from:
  https://www.openal.org/downloads/
  or https://openal-soft.org/

------------------------------------------------------------------------
CONTROLS
------------------------------------------------------------------------
- Arrow Keys or WASD: Move / Navigate
- Spacebar: Trigger Echo Location Scan
- Escape: Open Pause Menu / Quit
- M: Toggle Mono/Stereo (in Audio Calibration mode)

Enjoy the run!
