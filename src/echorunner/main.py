"""EchoRunner game entry point."""
from __future__ import annotations

import argparse
import logging




def run_audio_qa_test(app: EchoRunnerApp, suite: str) -> int:
    """Runs designated spatial, masking, or speech audio QA test scenes."""
    import time
    from echorunner.audio.openal_backend import CueEvent

    print(f"\n--- Running Audio QA Test Suite: {suite} ---")

    if not app.audio_backend or not app.audio_backend.enabled:
        print("Error: Audio backend is not enabled.")
        return 1

    backend = app.audio_backend

    if suite == "spatial":
        print("Scene 1: Left/Center/Right Panning")
        print("Playing at Left...")
        cue = CueEvent(cue_id="test_spatial_1", file_id="pellet_tick", priority=50, spatial=True, position=(-5.0, 0.0, 1.0))
        backend.play_cue(cue)
        time.sleep(1.0)
        
        print("Playing at Center...")
        cue.position = (0.0, 0.0, 1.0)
        backend.play_cue(cue)
        time.sleep(1.0)
        
        print("Playing at Right...")
        cue.position = (5.0, 0.0, 1.0)
        backend.play_cue(cue)
        time.sleep(1.5)

        print("Scene 2: Front/Back Panning")
        print("Playing at Front...")
        cue2 = CueEvent(cue_id="test_spatial_2", file_id="collision_warning", priority=50, spatial=True, position=(0.0, 0.0, -5.0))
        backend.play_cue(cue2)
        time.sleep(1.0)
        
        print("Playing at Back...")
        cue2.position = (0.0, 0.0, 5.0)
        backend.play_cue(cue2)
        time.sleep(1.5)

        print("Scene 3: Enemy Approach")
        cue3 = CueEvent(cue_id="test_spatial_3", file_id="enemy_ambusher_loop", priority=50, spatial=True, position=(0.0, 0.0, 10.0))
        backend.play_cue(cue3)
        for dist in range(10, 0, -2):
            print(f"Enemy distance: {dist} units...")
            cue3.position = (0.0, 0.0, float(dist))
            time.sleep(0.5)
        backend.stop_cue("test_spatial_3")
        time.sleep(0.5)
        print("Spatial QA suite completed successfully.")

    elif suite == "masking":
        print("Scene 4: Red Warning Masking (Ducking)")
        print("Playing low-priority background cue (priority 10)...")
        music_cue = CueEvent(cue_id="music_loop", file_id="landmark_safe_loop", priority=10, spatial=False, gain=0.8)
        backend.play_cue(music_cue)
        time.sleep(2.0)
        
        print("Playing high-priority danger cue (priority 90)... ducking should trigger!")
        danger_cue = CueEvent(cue_id="danger_alarm", file_id="enemy_near_red", priority=90, spatial=False, gain=1.0)
        backend.play_cue(danger_cue)
        time.sleep(3.0)
        
        backend.stop_cue("danger_alarm")
        backend.stop_cue("music_loop")
        time.sleep(0.5)

        print("Scene 6: Mono Fallback")
        print("Enabling mono fallback mode...")
        backend.mono_mode = True
        mono_cue = CueEvent(cue_id="mono_test", file_id="pellet_tick", priority=50, spatial=True, position=(-5.0, 0.0, 1.0))
        backend.play_cue(mono_cue)
        print("Played sound mapped to left (-5.0, 0.0, 1.0). Sound should be central with collapsed panning.")
        time.sleep(1.5)
        backend.mono_mode = False
        print("Masking QA suite completed successfully.")

    elif suite == "speech":
        print("Scene 5: Speech Interruption")
        if app.speech_manager:
            print("Playing initial speech message...")
            app.speech_manager.speak("audio_calibration_intro")
            time.sleep(1.0)
            print("Interrupting with a higher priority tutorial instruction...")
            app.speech_manager.speak("tutorial_prompt")
            time.sleep(4.0)
        else:
            print("Speech manager not initialized.")
        print("Speech QA suite completed successfully.")
    else:
        print(f"Unknown suite: {suite}. Available suites: spatial, masking, speech")
        return 1
        
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parses command line arguments, configures logging, and launches EchoRunner."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    import sys
    args_list = argv if argv is not None else sys.argv[1:]

    # Check for export subcommand
    if args_list and args_list[0] == "export":
        parser = argparse.ArgumentParser(prog="echorunner export")
        parser.add_argument("--session", default="latest", help="Session ID to export or delete")
        parser.add_argument("--anonymized", action="store_true", help="Anonymize telemetry data")
        parser.add_argument("--delete", action="store_true", help="Delete local session telemetry for privacy compliance")
        
        args = parser.parse_args(args_list[1:])
        from echorunner.research.study import export_session, delete_session_telemetry
        if args.delete:
            delete_session_telemetry(args.session)
        else:
            export_session(args.session, anonymized=args.anonymized)
        return 0

    # Normal game launch options
    parser = argparse.ArgumentParser(prog="echorunner")
    parser.add_argument(
        "--audio-test",
        action="store_true",
        help="Run the audio calibration/test scene",
    )
    parser.add_argument(
        "--suite",
        type=str,
        help="Audio QA test suite (spatial, masking, speech)",
    )
    parser.add_argument(
        "--tutorial", action="store_true", help="Start tutorial flow"
    )
    parser.add_argument(
        "--dev", action="store_true", help="Start developer trainer view"
    )
    parser.add_argument(
        "--trainer", action="store_true", help="Start developer trainer view"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run simulation without graphics/audio",
    )
    parser.add_argument(
        "--bot",
        type=str,
        default="safe_scan",
        help="Type of bot to run in headless mode (wall_hugger, random, safe_scan, perfect)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of simulation runs in headless mode",
    )
    parser.add_argument(
        "--study",
        action="store_true",
        help="Start HCI research study mode",
    )
    parser.add_argument(
        "--participant",
        type=str,
        help="Participant ID for study mode",
    )
    parser.add_argument(
        "--level",
        type=str,
        help="Level ID to load for the study session",
    )
    
    args = parser.parse_args(args_list)

    if args.headless:
        from echorunner.bot.runner import run_headless_simulation
        level = args.level or "level_01_training_loop"
        run_headless_simulation(level_id=level, bot_type=args.bot, runs=args.runs)
        return 0

    from echorunner.app import EchoRunnerApp

    app = EchoRunnerApp()
    
    # Configure config file for trainer view if --trainer is passed
    if args.trainer or args.dev:
        # We can set dev_mode or config defaults
        pass

    app.initialize(study=args.study, participant_id=args.participant, level_id=args.level)

    if args.audio_test:
        if args.suite:
            exit_code = run_audio_qa_test(app, args.suite)
            app.shutdown()
            return exit_code
        else:
            if app.speech_manager:
                app.speech_manager.speak("audio_calibration_intro")
    elif args.tutorial:
        from echorunner.app import AppState
        app.transition_to(AppState.TUTORIAL_MENU)

    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
