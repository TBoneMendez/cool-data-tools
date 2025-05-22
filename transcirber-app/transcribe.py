import os
import re
import json
import datetime
import time
import warnings
import argparse
import whisper
import ffmpeg
from pydub import AudioSegment
from tqdm import tqdm
from pydub.utils import mediainfo
from transformers import MarianMTModel, MarianTokenizer
from transformers import logging as hf_logging
import shutil

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

INPUT_DIR = "input"
CONVERTED_DIR = "converted"
OUTPUT_DIR = "output"

def parse_args():
    parser = argparse.ArgumentParser(description="TBone's Transcriber App")
    parser.add_argument(
        "--clean",
        nargs="+",
        choices=["input", "output", "converted", "all"],
        help="Clean one or more folders before running",
    )
    return parser.parse_args()

def clean_directories(targets):
    mapping = {
        "input": INPUT_DIR,
        "output": OUTPUT_DIR,
        "converted": CONVERTED_DIR,
    }

    folders = mapping.values() if "all" in targets else [mapping[t] for t in targets]

    for folder in folders:
        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except Exception as e:
                print(f"⚠️ Could not delete {path}: {e}")
    print(f"🧹 Clean-up complete: {', '.join(targets)}")

def convert_to_mp3(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="mp3")

def extract_audio_from_video(video_path, audio_path):
    try:
        ffmpeg.input(video_path).output(audio_path, format='mp3', acodec='libmp3lame', ac=1, ar='16k').overwrite_output().run(quiet=True)
    except ffmpeg.Error as e:
        print(f"❌ Error extracting audio from video '{video_path}': {e}")

def format_timestamp(seconds: float) -> str:
    return str(datetime.timedelta(seconds=round(seconds, 3))).replace(".", ",")

def write_srt(segments, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")

def write_vtt(segments, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            f.write(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}\n")
            f.write(f"{seg['text'].strip()}\n\n")

def prepare_files():
    os.makedirs(CONVERTED_DIR, exist_ok=True)

    prepared_files = []
    seen = set()
    files = sorted(os.listdir(INPUT_DIR))

    print("\n🔍 Scanning input folder for audio and video files...")

    for filename in files:
        filepath = os.path.join(INPUT_DIR, filename)
        basename, ext = os.path.splitext(filename)
        ext = ext.lower()

        if ext not in [".mp3", ".wav", ".m4a", ".mp4", ".mov", ".mkv", ".webm"]:
            continue

        if os.path.exists(os.path.join(CONVERTED_DIR, f"{basename}.mp3")):
            print(f"⏩ Skipping '{basename}' — already converted and will be reused.")
            prepared_files.append((basename, os.path.join(CONVERTED_DIR, f"{basename}.mp3")))
            continue

        converted_path = os.path.join(CONVERTED_DIR, f"{basename}.mp3")

        if os.path.exists(converted_path):
            print(f"⏩ Skipping conversion for '{basename}' (already converted)")
        elif ext == ".mp3":
            print(f"🎧 Copying original MP3 '{filename}' to converted/")
            shutil.copy2(filepath, converted_path)
        elif ext in [".wav", ".m4a"]:
            print(f"🎧 Converting '{filename}' to MP3...")
            convert_to_mp3(filepath, converted_path)
        elif ext in [".mp4", ".mov", ".mkv", ".webm"]:
            print(f"🎞️ Extracting audio from video '{filename}' to MP3...")
            extract_audio_from_video(filepath, converted_path)

        if os.path.exists(converted_path):
            prepared_files.append((basename, converted_path))

    return prepared_files

def write_outputs(result, output_folder, lang_suffix):
    lang_folder = os.path.join(output_folder, lang_suffix)
    os.makedirs(lang_folder, exist_ok=True)
    base = os.path.join(lang_folder, "transcript")

    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write(result["text"])

    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    write_srt(result["segments"], base + ".srt")
    write_vtt(result["segments"], base + ".vtt")

def transcribe_files(files, language=None, model_name="base"):
    model = whisper.load_model(model_name)
    if not files:
        print("⚠️ No valid audio or video files found in the input folder. Exiting.")
        return

    done_messages = []

    for basename, mp3_path in files:
        print(f"🔊 Transcribing {basename}.mp3 with input language '{language or 'auto'}' ...")

        start_time = time.time()
        info = mediainfo(mp3_path)
        duration_sec = float(info['duration'])

        try:
            result = model.transcribe(mp3_path, language=language)
            original_lang = result.get("language", language or "unknown")
            if language is None:
                print(f"🧠 Detected language for '{basename}': {original_lang}")

            output_folder = os.path.join(OUTPUT_DIR, basename)
            os.makedirs(output_folder, exist_ok=True)

            # Save original transcription
            write_outputs(result, output_folder, lang_suffix=original_lang)

            # Define which languages to generate
            lang_targets = ["en", "no", "sv"]
            if original_lang in lang_targets:
                lang_targets.remove(original_lang)

            for target_lang in lang_targets:
                if target_lang == "en":
                    print(f"🌍 Translating {basename} transcript → English ...")
                    translated = model.transcribe(mp3_path, language=original_lang, task="translate")
                    write_outputs(translated, output_folder, lang_suffix="en")
                else:
                    print(f"🌍 Translating {basename} transcript → {target_lang.upper()} ...")
                    translated_text = translate_text(result["text"], target_lang)
                    translated_result = result.copy()
                    translated_result["text"] = translated_text
                    write_outputs(translated_result, output_folder, lang_suffix=target_lang)

            elapsed = time.time() - start_time
            done_messages.append(
                f"✅ Done transcribing and translating '{basename}.mp3' — {round(duration_sec / 60, 1)} min audio in {round(elapsed / 60, 1)} min using {model_name.capitalize()} model. Check `./output/{basename}/` for results."
            )

        except Exception as e:
            print(f"❌ Error during transcription of '{basename}': {e}")

    for msg in done_messages:
        print(msg)

def split_into_chunks(text, tokenizer, max_tokens=512):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for sentence in sentences:
        test = current + sentence + " "
        if len(tokenizer(test).input_ids) < max_tokens:
            current = test
        else:
            chunks.append(current.strip())
            current = sentence + " "
    if current:
        chunks.append(current.strip())
    return chunks

def translate_text(text, target_lang):
    lang_map = {
        "no": "Neurora/opus-tatoeba-eng-nor-bt", #Norwegian Bokmål
        "sv": "Helsinki-NLP/opus-mt-en-sv" #Swedish
    }
    if target_lang not in lang_map:
        raise ValueError(f"Unsupported target language: {target_lang}")

    model_name = lang_map[target_lang]
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    chunks = split_into_chunks(text, tokenizer)
    translated_chunks = []
    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt", padding=True, truncation=True)
        translated = model.generate(**inputs)
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        translated_chunks.append(translated_text)

    return " ".join(translated_chunks)

def ask_language():
    options = {"no", "sv", "en", "auto"}

    print("\n👋 Welcome to **TBone's Transcriber App**")
    print("This app will convert sound or video files into MP3, and transcribe them into various formats and languages.\n")

    print("🌐 Choose input-language for transcription:")
    print("   no   = Norwegian")
    print("   sv   = Swedish")
    print("   en   = English")
    print("   auto = Automatic detection\n")
    
    while True:
        lang = input("👉 Define input language [no/sv/en/auto]: ").strip().lower()
        if lang in options:
            return None if lang == "auto" else lang
        print("❌ Invalid choice, please try again...")

def ask_model():
    options = {"base", "small", "medium", "large"}
    print("\n🧠 Choose Whisper model:")
    print("   base   = Fastest, lowest accuracy (default)")
    print("   small  = Good balance (recommended)")
    print("   medium = Higher accuracy, slower")
    print("   large  = Best accuracy, very slow (CPU only)\n")

    while True:
        model = input("👉 Enter model name [base/small/medium/large] (default: base): ").strip().lower()
        if model == "":
            return "base"
        if model in options:
            return model
        print("❌ Invalid choice, try again...")

if __name__ == "__main__":
    args = parse_args()

    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CONVERTED_DIR, exist_ok=True)

    if args.clean:
        clean_directories(args.clean)
        if len(vars(args)) == 1:  # no other args provided
            exit(0)

    language = ask_language()
    model_name = ask_model()
    files = prepare_files()
    transcribe_files(files, language=language, model_name=model_name)

    print("\n✅ Done! 🎉")
    print("💡 Tip: If you want to clear all files, run:\n   `python transcribe.py --clean all`")
    print("👋 See you next time!")