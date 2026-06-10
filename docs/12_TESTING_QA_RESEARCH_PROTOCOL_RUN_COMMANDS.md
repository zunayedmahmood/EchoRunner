# EchoRunner Testing, QA, Research Protocol, and Run Commands

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Quick start commands

### Linux/macOS

```bash
cd EchoRunner
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m echorunner --audio-test
python -m echorunner --tutorial
```

### Windows PowerShell

```powershell
cd EchoRunner
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m echorunner --audio-test
python -m echorunner --tutorial
```

## 2. Script files included

This package includes starter script files in `scripts/`:

```text
setup_venv.sh
setup_venv.ps1
run_game.sh
run_game.ps1
run_audio_test.sh
run_tests.sh
run_game.bat
dev_run.sh/dev_run.ps1/dev_run.bat retained for compatibility
```

These are templates for the final repository.

## 3. Test categories

### Unit tests

Run without Pygame display or OpenAL device.

```bash
pytest tests/unit
```

Must cover:

```text
level parser
movement rules
queued turn rules
pellet collection
power mode timer
enemy state transitions
threat classifier
cue priority sorter
settings validation
telemetry event schema
```

### Integration tests

May require Pygame dummy video driver and OpenAL installed.

```bash
pytest tests/integration
```

Must cover:

```text
Pygame boots
OpenAL backend starts
audio buffers load
source pool plays one-shots
listener orientation changes panning
speech files play listener-relative
```

### Audio QA tests

```bash
python -m echorunner --audio-test --suite spatial
python -m echorunner --audio-test --suite masking
python -m echorunner --audio-test --suite speech
```

Test scenes:

1. left/center/right;
2. front/back;
3. enemy approach;
4. red warning masking;
5. speech interruption;
6. mono fallback.

### Gameplay QA tests

```bash
python -m echorunner --headless --bot safe_scan --level level_01_training_loop
python -m echorunner --headless --bot random --level level_02_crossroads --runs 100
```

### Accessibility manual tests

- Play with monitor off.
- Play with keyboard only.
- Use headphones.
- Use mono mode.
- Use low-stress mode.
- Repeat every tutorial instruction.
- Calibrate audio from main menu and pause menu.
- Confirm red warning is unmistakable.
- Confirm death explanation is specific.

## 4. Definition of test pass

A build passes accessibility QA only if:

```text
first launch speaks instructions
menu usable without mouse
audio calibration works
tutorial can be completed audio-only
player can repeat instructions
red danger overrides lower cues
death cause is explained
settings can be changed by keyboard
```

## 5. Research protocol for blind player testing

### 5.1 Before session

- Get consent.
- Explain that the player can stop anytime.
- Ask about headphone comfort and preferred speech speed.
- Assign participant ID.
- Do not record real names in telemetry.

### 5.2 Session tasks

Suggested tasks:

1. Complete audio calibration.
2. Navigate main menu to tutorial.
3. Complete wall/movement tutorial.
4. Complete scan tutorial.
5. Escape one enemy.
6. Use resonance core.
7. Try level 1 for five minutes.
8. Explain what cues they understood or missed.

### 5.3 Observations to record

- confusion points;
- repeated wall hits;
- missed red cues;
- scan usage;
- menu navigation issues;
- speech too fast/slow;
- sound fatigue;
- trainer interventions.

### 5.4 Post-session prompts

Ask:

```text
Which sounds were clear?
Which sounds were confusing?
Did you know where enemies were?
Did you know why you lost a life?
Was speech too much or too little?
Could you imagine the maze in your mind?
What should be easier in the next version?
```

Optional instruments:

- SUS for usability;
- NASA-TLX for workload;
- short custom audio clarity scale.

## 6. Bug report template

```markdown
# EchoRunner Bug Report

## Build version

## OS and audio device

## Mode
- headphones / mono / low-stress / cue density

## Steps

## Expected

## Actual

## Was the screen needed to understand the issue?

## Logs attached
- events.jsonl
- replay.json
- settings snapshot
```

## 7. Automated CI plan

CI should run:

```bash
pytest tests/unit
python scripts/validate_assets.py
python scripts/validate_audio_manifest.py
python scripts/validate_levels.py
```

Do not require real audio hardware in basic CI. Use mock OpenAL backend for unit tests.

## 8. Release gate

Before any release:

- [ ] unit tests pass;
- [ ] level validator passes;
- [ ] audio manifest validator passes;
- [ ] Windows manual smoke test;
- [ ] Linux manual smoke test;
- [ ] macOS smoke test if supported;
- [ ] audio-only tutorial pass;
- [ ] at least two blind/low-vision playtests before public release;
- [ ] known issues documented.
