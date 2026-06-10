# EchoRunner Sound Library

This library contains original generated placeholder SFX and generated speech files for EchoRunner.

## Important folders

```text
wav/                 Existing generated SFX and earcons
speech/en/txt/       English speech transcripts
speech/en/wav/       English generated speech WAVs
speech/bn/txt/       Bangla draft speech transcripts
speech/bn/wav/       Bangla generated speech WAVs
manifest.json        Combined SFX + speech manifest
speech_manifest.json Speech-only manifest
```

## Implementation rule

Use OpenAL for gameplay audio. Most SFX should be mono and spatialized when appropriate. Speech should be listener-relative and interruptible by urgent cues.

## Quality note

Generated speech is for implementation and testing. Replace with better TTS or recorded voice before final release if the playtest team finds eSpeak unclear.
