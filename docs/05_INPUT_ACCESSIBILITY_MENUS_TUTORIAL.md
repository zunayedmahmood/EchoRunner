# EchoRunner Input, Accessibility, Menus, and Tutorial Implementation

> Source alignment: This workplan updates the previous Sound-Maze package into **EchoRunner**, a Python + Pygame game with OpenAL spatial audio. It follows the blind-first design doctrine from the supplied Sound-Maze plan, the local-first/accessibility/research workflow from the HCI toolkit guide, and the OpenAL device/context/buffer/source/listener model from the OpenAL Programmer's Guide.

## 1. Accessibility stance

EchoRunner is designed around ability, not deficit. Blind players can build strong mental maps when a game provides stable landmarks, directional sound, predictable rhythm, and replayable instructions.

Do not depend on screen-reader output during action gameplay. Real-time play needs short cues and earcons. Screen readers are useful for menus and settings, but live gameplay should be self-voicing and cue-driven.

## 2. Input abstraction

Raw keyboard events must be converted into semantic commands.

```python
class Command(Enum):
    MOVE_UP = auto()
    MOVE_DOWN = auto()
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    SCAN_SHORT = auto()
    SCAN_DEEP = auto()
    REPEAT_LAST = auto()
    HELP = auto()
    CONFIRM = auto()
    BACK = auto()
    PAUSE = auto()
    TOGGLE_TRAINER = auto()
    AUDIO_TEST = auto()
```

This allows remapping later without rewriting gameplay.

## 3. Default controls

| Action | Primary keys | Alternative keys |
|---|---|---|
| Move up | Up Arrow | W |
| Move down | Down Arrow | S |
| Move left | Left Arrow | A |
| Move right | Right Arrow | D |
| Confirm/select | Enter | Return |
| Back/cancel | Escape | Backspace |
| Pause | Escape/P | P |
| Short scan | Space | Numpad 0 |
| Deep scan | Shift + Space | Tab |
| Repeat last speech | R | F5 |
| Context help | H | F1 |
| Audio calibration | F2 | — |
| Toggle cue density | F3 | — |
| Toggle trainer view | F9 | — |
| Mute music | F10 | — |
| Quit confirmation | Alt + F4 or menu | — |

## 4. Optional six-key accessibility layout

For experiments with custom six-key devices, map six physical keys to semantic actions:

| Six-key action | Suggested keyboard key | Meaning |
|---|---:|---|
| Left navigation | S | Move/choose left |
| Up navigation | D | Move/choose up |
| Scan/repeat | F | Short scan or repeat current item |
| Confirm/help | J | Confirm in menus, help in gameplay when held |
| Down navigation | K | Move/choose down |
| Right navigation | L | Move/choose right |

This layout keeps both hands on the home row and can be adapted to a Braille-style controller later. Do not make it the only supported input until tested with users.

## 5. Input forgiveness

Blind-first action games must not require visual-frame precision.

Rules:

- Movement can be queued before a junction.
- Held movement continues movement.
- Opposite direction should reverse when legal.
- Scan should not cancel movement unless configured.
- Menu repeat/help must never change selection accidentally.
- Tutorial should give hints after repeated invalid inputs.

## 6. Menu accessibility

Menu design:

```text
One selection at a time.
Speech reads current item.
Up/down changes item.
Enter selects.
R repeats.
H gives explanation.
Esc backs out.
```

Avoid visual-only menus, hover states, dragging, sliders without keyboard control, and decorative text that screen readers might read as clutter.

### Slider pattern

For volume/speech speed:

```text
Left/Right decrease/increase.
Speech says: "Speech volume seventy percent."
Enter confirms.
R repeats.
```

## 7. First-launch onboarding

The first launch must be gentle and clear.

Suggested sequence:

1. Speak game title and basic controls.
2. Ask for headphone calibration.
3. Offer tutorial.
4. Teach one concept at a time.
5. Do not show a complex settings menu first.

## 8. Tutorial module design

Each tutorial module should contain:

- one primary lesson;
- safe practice environment;
- short entry speech;
- one or two cue sounds to learn;
- success confirmation;
- optional retry;
- no sudden threats unless the module is about threats.

### Module 1 — Hear walls

Entry speech:

```text
Tutorial one. Hear walls. Move with arrow keys or W A S D. If you face a wall, you will hear a knock. Try moving right.
```

Success:

```text
Good. That soft step means you moved. The knock means wall.
```

### Module 2 — Turn at junctions

Entry speech:

```text
Tutorial two. Junctions. When paths open, you will hear direction cues. You can press a turn early and EchoRunner will turn at the next legal tile.
```

### Module 3 — Collect echo orbs

Entry speech:

```text
Tutorial three. Echo orbs. Collect every orb in the maze. Each orb makes a light tick. Clear a row to hear a brighter sound.
```

### Module 4 — Scan

Entry speech:

```text
Tutorial four. Scan. Press Space for a short scan. Scan tells you useful choices, not every tile.
```

### Module 5 — Enemy warning

Entry speech:

```text
Tutorial five. Enemy warning. Green is nearby. Amber means danger soon. Red means turn or escape now.
```

### Module 6 — Resonance core

Entry speech:

```text
Tutorial six. Resonance core. A resonance core turns danger around for a short time. Listen for the countdown before power ends.
```

### Module 7 — Real level

Entry speech:

```text
Final tutorial. Use movement, scan, orbs, enemies, and power together. You can press H for help at any time.
```

## 9. Cue density modes

### Beginner

- more speech;
- more junction summaries;
- slower enemy speed;
- longer warnings;
- movement ticks on;
- death explanations detailed.

### Standard

- short speech;
- event-based cues;
- scan required for longer summaries;
- normal speed.

### Expert

- minimal speech;
- fewer reward cues;
- stronger reliance on landmarks;
- higher movement clock;
- warnings still mandatory for fairness.

## 10. Low-stress mode

Low-stress mode should include:

- reduced enemy speed;
- no sudden loud sounds;
- longer red warning window;
- optional no-death practice;
- power mode duration extended;
- simplified enemy behavior.

This is not "easy mode" as a stigma. Present it as comfort/accessibility.

## 11. Screen reader compatibility

For menus and launcher:

- provide plain text labels;
- avoid constantly changing text while screen reader is focused;
- do not trap keyboard focus;
- allow command-line launch options;
- provide `--plain-menu` mode if needed.

Gameplay itself should not require an external screen reader.

## 12. Speech interrupt policy

Speech must be interruptible by urgent cues.

Priority order:

```text
life lost / collision
red threat
power ending
player requested scan
tutorial instruction
menu speech
ambient narration
```

If red threat happens while speech is playing, duck or stop the speech.

## 13. Accessibility testing tasks

Each build must be tested with:

- keyboard only;
- monitor off by developer;
- headphones;
- mono speaker mode;
- low-stress mode;
- high cue density;
- speech repeat;
- tutorial replay;
- trainer view on/off.
