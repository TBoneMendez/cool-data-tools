
# TBone's Transcriber App 🎙️🎞️

This app converts audio and video files to .mp3, transcribes the speech using OpenAI Whisper, and outputs the results in multiple formats including .txt, .json, .srt, and .vtt.
It supports Norwegian, Swedish and English, with optional automatic language detection.
Every transcription is automatically translated into all three supported languages. All processing is done entirely locally, with no internet connection required after the initial setup.

## 🧠 Models used

This app combines two powerful open-source model families:

- 🎙 **OpenAI Whisper** – used to transcribe `.mp3` audio into text  
  - You can choose between `base`, `small`, `medium`, and `large`  
  - Whisper supports multilingual transcription and automatic language detection

- 🌍 **Hugging Face translation models** – used to translate the English transcript into Norwegian and Swedish  
  - Norwegian: [Neurora/opus-tatoeba-eng-nor-bt](https://huggingface.co/Neurora/opus-tatoeba-eng-nor-bt)  
  - Swedish: [Helsinki-NLP/opus-mt-en-sv](https://huggingface.co/Helsinki-NLP/opus-mt-en-sv)  
  - Translations are performed locally using the `transformers` library  
  - No API keys or internet connectivity are required after first-time model download

## 📁 Folder structure

```
project-root/
├── input/              # Place your .wav, .m4a, .mp3, or video files here
├── converted/          # All converted .mp3 files used for transcription
├── output/             # One folder per file, with subfolders per detected or specified language
│   └── <filename>/
│       ├── no/         # Norwegian transcription outputs
│       ├── en/         # English translation (if applicable)
│       └── ...         # Other language codes (e.g., sv, etc.)
├── transcribe.py       # Main script
├── requirements.txt    # Python dependencies
└── README.md
```

## 🧱 System requirements

This app depends on `ffmpeg` being available on your system for converting and extracting audio.

### Install `ffmpeg`:

- **macOS**:  
  ```bash
  brew install ffmpeg
  ```

- **Ubuntu/Debian**:  
  ```bash
  sudo apt install ffmpeg
  ```

- **Windows**:
  1. Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
  2. Add `ffmpeg.exe` to your system `PATH` or place it in the project root

## 🛠️ Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ▶️ Usage

1. Place your audio or video files in the `input/` folder (`.wav`, `.m4a`, `.mp3`, `.mp4`, `.mov`, `.mkv`, `.webm`).
2. Run the script:
   ```bash
   python transcribe.py
   ```

3. You will be prompted for two choices:

### 🌐 Choose input language

Select the language of the audio manually for best accuracy:

- `no` = Norwegian
- `sv` = Swedish
- `en` = English
- `auto` = Let Whisper detect the language automatically (less accurate on short files)

### 🧠 Choose model size

Select a Whisper model based on your needs:

- `base` = Fastest, but lowest accuracy (default)
- `small` = Balanced for most uses (recommended for scandinavian languages)
- `medium` = More accurate, slower
- `large` = Highest quality, very slow on CPU

If you just press Enter, the `base` model will be selected by default.

## 📝 Output

For each input file, a folder will be created in `output/` containing subfolders for each language:

```
output/<filename>/
├── en/
│ ├── transcript.txt
│ ├── transcript.json
│ ├── transcript.srt
│ └── transcript.vtt
├── sv/
│ └── ...
├── no/
│ └── ...

- Each folder corresponds to a language: the original transcript, and two automatic translations.
- Translations are generated based on the transcribed **text**, not the original audio.
- All output folders include:
  - `transcript.txt`: plain text
  - `transcript.json`: Whisper segments
  - `transcript.srt`: subtitle format
  - `transcript.vtt`: WebVTT format
```

## ✅ Ready to go!

Place a file in the input folder, and start transcribing!

```
python transcribe.py
```

## 🧹 Clean folders (standalone operation)

You can use the `--clean` flag to delete contents of specific folders. This is a **standalone command** — the script will exit immediately after cleaning, without running transcription.

### 🗂 Supported targets

- `input` – original uploaded files
- `converted` – internally converted `.mp3` files
- `output` – final transcript outputs
- `all` – cleans all the above folders

### 🧪 Examples

```bash
# Clean everything and exit
python transcribe.py --clean all

# Only clean converted and output files
python transcribe.py --clean converted output

# Only clean converted files
python transcribe.py --clean converted

# Reset input folder (e.g. before new import)
python transcribe.py --clean input
```

## 🔒 ...by the way: Offline capability

Once you have setup, and run the app once with each model, everything works 100% offline.

- When you first run transcription using OpenAI Whisper (e.g. `base`), the model is downloaded locally to your machine.
- The same goes for the Hugging Face translation models (`en→no`, `en→sv`), which are stored under `~/.cache/huggingface/`.

After this one-time setup, **no internet connection is required** to run the app.  
All transcription and translation is performed **entirely locally**, ensuring:
- Full data privacy
- Fast repeat usage
- No API keys or third-party services

This makes the app ideal for field use, travel, air-gapped environments, or when processing sensitive content.
