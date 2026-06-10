# EchoRunner Player Controls, Game Goals, and Onboarding Script

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

This file is written for the player-facing experience. It should be used by developers, audio designers, tutorial writers, and testers. The same text is also reflected in generated speech files in `soundLibrary/speech/`.

## 1. Player promise

EchoRunner is a game you can play by listening. You do not need to see the screen. The game will tell you what matters through sound, rhythm, direction, and short spoken help.

## 2. Game goal

Your goal is to:

1. collect every echo orb in the maze;
2. avoid enemies that chase you;
3. use resonance cores to make enemies vulnerable for a short time;
4. learn routes by sound;
5. clear the level and improve your route.

Player-facing speech:

```text
Your goal is to collect every echo orb in the maze, avoid enemies, use resonance cores to reverse danger for a short time, and clear the level by learning the maze through sound.
```

Audio files:

```text
soundLibrary/speech/en/wav/game_goal_en.wav
soundLibrary/speech/bn/wav/game_goal_bn.wav
```

## 3. Basic controls

### Movement

```text
Arrow keys or W A S D move your runner.
You can press a turn a little early. EchoRunner will turn when the path opens.
```

### Menu

```text
Up and Down choose menu items.
Enter selects.
Escape goes back.
R repeats the last spoken message.
H gives help.
```

### Gameplay help

```text
Space gives a short scan.
Shift plus Space gives a deeper scan.
R repeats the last spoken message.
H explains your current goal.
P or Escape pauses.
F2 starts audio calibration.
F3 changes cue detail.
F9 turns trainer view on or off.
```

## 4. First launch spoken script

```text
Welcome to EchoRunner. This game is played by listening. Use arrow keys or W A S D to move. Press Enter to choose. Press Space to scan. Press R to repeat. Press H for help. For best results, use headphones. The first option is Start Tutorial.
```

Implementation:

- play on first launch;
- show as text on trainer view;
- save `first_launch_completed = true` after calibration or tutorial start;
- allow replay from Help menu.

## 5. Audio calibration script

```text
Audio calibration. You will hear left, center, and right. If the direction sounds wrong, use mono mode or check your headphones.
```

Then play:

```text
Left.
Center.
Right.
```

Ask:

```text
Did the directions sound correct? Press Enter for yes, Space to repeat, or M for mono mode.
```

## 6. Tutorial introduction

```text
Start Tutorial. EchoRunner will teach one sound at a time. You can repeat instructions with R. You can pause with Escape. There is no penalty in tutorial.
```

## 7. Tutorial scripts

### Tutorial 1 — Walls and movement

```text
Tutorial one. Hear walls. Move with arrow keys or W A S D. A soft step means you moved. A knock means wall. Try moving right now.
```

### Tutorial 2 — Junctions and turns

```text
Tutorial two. Junctions. A junction is a place where paths split. When a path opens, you will hear a direction cue. You can press a turn early.
```

### Tutorial 3 — Echo orbs

```text
Tutorial three. Echo orbs. Collect every orb. Each orb makes a light tick. When a route is cleared, you will hear a brighter sound.
```

### Tutorial 4 — Scan

```text
Tutorial four. Scan. Press Space for a short scan. Scan tells you useful choices, such as pellets left, danger forward, or wall right.
```

### Tutorial 5 — Enemy danger

```text
Tutorial five. Enemy danger. Green means an enemy is nearby. Amber means danger soon. Red means turn, escape, or use power now.
```

### Tutorial 6 — Resonance core

```text
Tutorial six. Resonance core. A resonance core turns danger around for a short time. Listen for the countdown before power ends.
```

### Tutorial 7 — Real level practice

```text
Final tutorial. Use movement, scan, echo orbs, enemy warnings, and resonance cores together. Press H for help at any time.
```

## 8. Gameplay help script

When the player presses H during a level:

```text
You are playing EchoRunner. Collect all echo orbs. Avoid enemies. Space scans nearby choices. Red danger means change direction now. Resonance cores make enemies vulnerable for a short time. Press R to repeat this help, or Escape to pause.
```

## 9. Scan examples

Short scan examples should be dynamic.

```text
Left has pellets. Forward has danger far. Right is blocked. Back returns to the safe loop.
```

```text
Forward is safe. Left has a resonance core. Right has amber danger.
```

```text
You are in the safe pocket. Two paths open: left to pellets, right to the center gate.
```

## 10. Death explanation scripts

Death explanations must be specific.

Bad:

```text
You died.
```

Good:

```text
Hunter caught you from the left corridor. You had a safe turn behind you.
```

```text
Ambusher reached the junction before you. Try scanning before entering the center path.
```

```text
Power ended before you touched the enemy. Listen for the countdown and turn away when danger returns.
```

## 11. Pause menu spoken script

```text
Paused. Options are Resume, Repeat goal, Repeat controls, Audio calibration, Cue detail, Restart level, and Quit to main menu. Use Up and Down, then Enter.
```

## 12. Cue meaning cheat sheet

| Sound | Meaning | Player action |
|---|---|---|
| soft step | you moved | keep route or turn |
| wall knock | blocked | choose another direction |
| light tick | orb collected | continue collecting |
| brighter tick | route segment clear | plan next route |
| open direction chime | path available | choose direction |
| green enemy cue | enemy nearby | stay aware |
| amber enemy cue | danger soon | prepare turn/scan |
| red enemy cue | danger now | turn, escape, or use power |
| power transform | resonance active | enemies vulnerable |
| countdown | power ending | stop chasing enemies |
| level cadence | level clear | listen to score/results |

## 13. When to introduce controls

Do not read the entire controls manual on every launch.

Recommended timing:

```text
First launch: core controls only.
Audio calibration: direction controls only.
Tutorial module: teach only the controls needed now.
Gameplay H: repeat full short help.
Pause menu: offer full controls.
Settings: offer key remapping details.
```

## 14. Player-facing accessibility notes

Speak these in settings/help, not during action:

```text
You can change cue detail, speech speed, volume, low-stress mode, mono mode, and headphones mode from settings. All settings work by keyboard.
```

## 15. Implementation checklist

- [ ] Every script line has a text file.
- [ ] Every script line has an English WAV.
- [ ] Important scripts have Bangla draft WAV.
- [ ] Player can replay every instruction.
- [ ] Speech does not block red danger cues.
- [ ] Tutorial introduces one new idea at a time.
- [ ] Trainer view displays current instruction text.
- [ ] Scripts are versioned so updated audio can be regenerated.
