# EchoRunner Cross-OS Support, Build, Export, and Packaging

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Target platforms

EchoRunner should support:

```text
Windows 10/11
Ubuntu/Debian Linux and similar distributions
macOS Apple Silicon and Intel where practical
```

Because OpenAL and Pygame both interact with OS-level audio/video systems, cross-OS support must be designed from the beginning.

## 2. Cross-OS constraints

| Area | Risk | Mitigation |
|---|---|---|
| OpenAL library loading | DLL/SO/DYLIB path differs | central loader with search paths |
| Audio devices | device names differ | default device fallback + settings |
| Pygame display | headless/test environments fail | headless test mode |
| Paths | Windows slash differences | use `pathlib` only |
| Fonts | missing fonts | bundle accessible font or use system fallback |
| TTS | OS voices differ | use generated WAV speech assets for core lines |
| Packaging | binary libs missing | bundle OpenAL Soft where legal/practical |

## 3. Runtime folders

Use `platformdirs` or explicit local paths.

Development:

```text
./data/sessions/
./data/user_settings.json
./logs/
```

Installed app:

```text
User data dir/EchoRunner/sessions/
User config dir/EchoRunner/settings.json
User log dir/EchoRunner/logs/
```

## 4. Build modes

### Development mode

```bash
python -m echorunner --dev --trainer
```

### Audio diagnostic mode

```bash
python -m echorunner --audio-test
```

### Headless simulation test

```bash
python -m echorunner --headless --level level_01_training_loop --bot safe_scan
```

### Research session mode

```bash
python -m echorunner --study --participant P01 --level level_01_training_loop
```

## 5. PyInstaller packaging

Basic command:

```bash
pyinstaller --name EchoRunner --windowed --onefile src/echorunner/main.py
```

For real builds, prefer `.spec` file to include:

```text
assets/
audio/
levels/
config/
OpenAL Soft binary
license files
```

## 6. Windows packaging notes

Include:

```text
EchoRunner.exe
OpenAL32.dll
assets/
audio/
levels/
config/
README_FIRST_RUN.txt
```

Test on a clean Windows machine without Python installed.

## 7. Linux packaging notes

Options:

- standalone folder;
- AppImage;
- `.deb` later.

Check dependencies:

```bash
ldd EchoRunner | grep -i openal
```

Provide install helper:

```bash
sudo apt install libopenal1
```

## 8. macOS packaging notes

Options:

- app bundle;
- zipped standalone folder for internal testing;
- signed/notarized release later.

OpenAL Soft dylib path must be resolved carefully. Test both Apple Silicon and Intel if release audience requires it.

## 9. Export system

EchoRunner should export:

```text
session summary markdown
telemetry JSONL
replay JSON
settings snapshot
anonymized report
optional SUS/NASA-TLX CSV if study mode is used
```

Export command:

```bash
echorunner export --session latest --anonymized
```

## 10. Build checklist

- [ ] Pygame window opens.
- [ ] OpenAL device/context starts.
- [ ] Speech files load.
- [ ] SFX files load.
- [ ] Level JSON loads.
- [ ] Trainer view renders.
- [ ] Audio calibration works.
- [ ] Quit closes OpenAL cleanly.
- [ ] Packaged app runs on clean OS.
- [ ] User can play tutorial with monitor off.

## 11. Versioning

Use semantic-ish versions:

```text
0.1.0 audio boot prototype
0.2.0 tutorial slice
0.3.0 first playable level
0.4.0 research alpha
0.5.0 cross-OS beta
1.0.0 public release
```

## 12. Release notes template

```markdown
# EchoRunner v0.x.x

## New
- ...

## Audio changes
- ...

## Accessibility changes
- ...

## Known issues
- ...

## Test status
- Windows: pass/fail
- Linux: pass/fail
- macOS: pass/fail
- Audio-only playthrough: pass/fail
```
