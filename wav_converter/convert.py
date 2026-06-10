#!/usr/bin/env python3
import os
import sys
import glob
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from pydub import AudioSegment
from elevenlabs.client import ElevenLabs

# Load environment variables from .env file
load_dotenv()

def main():
    parser = argparse.ArgumentParser(
        description="Convert game dialog text files to speech using ElevenLabs and save as WAV."
    )
    parser.add_argument(
        "--txt-dir",
        type=str,
        default=str(Path(__file__).parent.parent / "soundLibrary" / "speech" / "en" / "txt"),
        help="Path to the directory containing source .txt files"
    )
    parser.add_argument(
        "--wav-dir",
        type=str,
        default=str(Path(__file__).parent.parent / "soundLibrary" / "speech" / "en" / "wav"),
        help="Path to the directory to save the output .wav files"
    )
    parser.add_argument(
        "--voice-id",
        type=str,
        default="Gubgw9l4dtIoQA9YZHgx",
        help="ElevenLabs Voice ID to use for speech generation"
    )
    parser.add_argument(
        "--model-id",
        type=str,
        default="eleven_v3",
        help="ElevenLabs Model ID to use for speech generation"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=12.0,
        help="Delay in seconds between requests to maintain rate limit (default: 12.0s for 5 req/min)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan files and print mapping without making API calls or modifying files"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip generation if the target wav file already exists"
    )

    args = parser.parse_args()

    # Verify text directory exists
    txt_dir = Path(args.txt_dir).resolve()
    wav_dir = Path(args.wav_dir).resolve()

    if not txt_dir.exists():
        print(f"Error: Text directory does not exist: {txt_dir}")
        sys.exit(1)

    # Ensure output directory exists
    if not args.dry_run:
        wav_dir.mkdir(parents=True, exist_ok=True)

    # Find all .txt files
    txt_files = sorted(txt_dir.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {txt_dir}")
        sys.exit(0)

    print(f"=== EchoRunner Speech Converter ===")
    print(f"Source Text Dir: {txt_dir}")
    print(f"Target WAV Dir:  {wav_dir}")
    print(f"Voice ID:        {args.voice_id}")
    print(f"Model ID:        {args.model_id}")
    print(f"Rate-limit:      {args.delay}s delay between requests (max 5 requests/min)")
    print(f"Found {len(txt_files)} text files to process.")
    print("===================================\n")

    if args.dry_run:
        print("Dry run mode active. No changes will be made.\nFile mappings:")
        for txt_path in txt_files:
            wav_name = txt_path.with_suffix(".wav").name
            target_wav = wav_dir / wav_name
            status = " [SKIPPED if existing]" if args.skip_existing and target_wav.exists() else ""
            print(f"  {txt_path.name} -> {wav_name}{status}")
        return

    # Check for ElevenLabs API Key
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        print("Error: ELEVENLABS_API_KEY not found in environment or .env file.")
        print("Please configure your api key in 'wav_converter/.env' and try again.")
        sys.exit(1)

    # Initialize ElevenLabs Client
    try:
        client = ElevenLabs(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize ElevenLabs client: {e}")
        sys.exit(1)

    # Temporary files directory
    temp_dir = Path(__file__).parent / "temp_audio"
    temp_dir.mkdir(exist_ok=True)

    processed_count = 0
    skipped_count = 0

    with tqdm(txt_files, desc="Processing files", unit="file") as pbar:
        for index, txt_path in enumerate(pbar):
            base_name = txt_path.stem
            wav_name = f"{base_name}.wav"
            target_wav = wav_dir / wav_name

            # Check skip existing condition
            if args.skip_existing and target_wav.exists():
                skipped_count += 1
                pbar.write(f"Skipped (already exists): {wav_name}")
                continue

            # Read the text content
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    text_content = f.read().strip()
            except Exception as e:
                pbar.write(f"Error reading file {txt_path.name}: {e}")
                continue

            if not text_content:
                pbar.write(f"Warning: File {txt_path.name} is empty. Skipping.")
                continue

            # Update tqdm progress info
            pbar.set_description(f"Synthesizing {wav_name}")

            # Define temporary file paths
            # The prompt requested saving as (.mp4) and then converting to .wav
            temp_mp4_path = temp_dir / f"{base_name}.mp4"

            try:
                # 1. Call ElevenLabs API
                audio_stream = client.text_to_speech.convert(
                    text=text_content,
                    voice_id=args.voice_id,
                    model_id=args.model_id,
                    output_format="mp3_44100_128",
                )

                # 2. Write response to the temporary MP4 file
                with open(temp_mp4_path, "wb") as temp_file:
                    if isinstance(audio_stream, bytes):
                        temp_file.write(audio_stream)
                    else:
                        for chunk in audio_stream:
                            if chunk:
                                temp_file.write(chunk)

                # 3. Convert MP4 to WAV using pydub
                pbar.set_description(f"Converting {wav_name} to WAV")
                audio_segment = AudioSegment.from_file(temp_mp4_path)
                audio_segment.export(target_wav, format="wav")

                # Remove temporary file
                if temp_mp4_path.exists():
                    temp_mp4_path.unlink()

                processed_count += 1
                pbar.write(f"✓ Generated: {wav_name}")

            except Exception as e:
                pbar.write(f"✗ Failed to process {txt_path.name}: {e}")
                # Ensure temporary file is cleaned up on failure
                if temp_mp4_path.exists():
                    temp_mp4_path.unlink()
                # Stop if it is a major connection/key issue
                if "api_key" in str(e).lower() or "unauthorized" in str(e).lower() or "quota" in str(e).lower():
                    print("\nAPI Error encountered. Exiting.")
                    break
                continue

            # Rate Limit Delay: 5 requests per minute spaced out = 12.0 seconds between starts
            # Apply delay if there are more files to process
            if index < len(txt_files) - 1:
                # Perform countdown in progress bar description
                steps = int(args.delay)
                fractional = args.delay - steps
                for s in range(steps, 0, -1):
                    pbar.set_description(f"Rate limit: waiting {s}s")
                    time.sleep(1)
                if fractional > 0:
                    time.sleep(fractional)

    # Clean up temp folder
    try:
        if temp_dir.exists():
            temp_dir.rmdir()
    except Exception:
        pass

    print(f"\nProcessing complete!")
    print(f"Total processed: {processed_count}")
    print(f"Total skipped:   {skipped_count}")
    print(f"All files saved in {wav_dir}")

if __name__ == "__main__":
    main()
