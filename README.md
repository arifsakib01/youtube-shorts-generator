# Automated YouTube Shorts Generator

This project creates a vertical 9:16 YouTube Short from a topic:

1. Gemini writes a validated scene script.
2. Edge TTS creates free narration audio.
3. Pexels supplies portrait stock-video clips.
4. FFmpeg crops, joins, captions, and muxes the final MP4.

The software is free to run, but Gemini and Pexels still require free-tier API
keys. Internet access is required for Gemini, Edge TTS, and Pexels.

## Prerequisites

- Python 3.10 or newer
- FFmpeg, including `ffprobe`, available on `PATH`
- A Gemini API key from <https://aistudio.google.com/apikey>
- A Pexels API key from <https://www.pexels.com/api/>

On Windows, install FFmpeg with one of these options:

```powershell
winget install Gyan.FFmpeg.Shared
```

Or download a build from <https://ffmpeg.org/download.html>, add its `bin`
directory to `PATH`, and restart the terminal.

Verify the installation:

```powershell
ffmpeg -version
ffprobe -version
```

## Installation

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Edit `.env` and set `GEMINI_API_KEY` and `PEXELS_API_KEY`. Do not commit
`.env`; it contains secrets.

## Generate a short

```powershell
python main.py "5 surprising facts about the deep ocean"
```

Rendered videos are written to `output\`. Temporary downloads, audio, and
subtitle files are written to `.tmp\`.

## Run online with GitHub Actions

The repository includes a manual workflow at
`.github/workflows/generate-short.yml`. It runs Python, Edge TTS, Gemini,
Pexels, and FFmpeg on a GitHub-hosted Ubuntu runner and publishes the MP4 as a
 downloadable workflow artifact. No local Python or FFmpeg installation is
needed for this mode.

1. Push this project to a GitHub repository. A public repository is generally
   the safest choice for avoiding GitHub Actions billing, subject to GitHub's
   current usage policy.
2. Open **Settings → Secrets and variables → Actions**.
3. Add repository secrets named `GEMINI_API_KEY` and `PEXELS_API_KEY`.
   Never put keys in workflow YAML, source files, or normal repository
   variables.
4. Open **Actions → Generate YouTube Short → Run workflow**.
5. Enter a topic and optionally change the Gemini model.
6. When the run finishes, open the run summary and download the
   `youtube-short` artifact.

GitHub-hosted runners are ephemeral: downloaded stock clips, narration, and
temporary files are discarded after the run. The final MP4 remains available
for the artifact retention period configured in the workflow.

## Configuration

The defaults in `.env.example` produce 1080x1920 video at 30 FPS. Useful
settings include:

- `GEMINI_MODEL`: Gemini model name
- `VOICE`: an Edge TTS voice such as `en-US-AriaNeural`
- `MAX_SCENES`: between 3 and 8 scenes
- `FFMPEG_BINARY`: custom FFmpeg executable path or name
- `OUTPUT_DIR` and `TEMP_DIR`: output locations

## Notes

- Captions use scene narration timings estimated from word counts. They are
  synchronized to the generated narration track without requiring a paid
  captioning API.
- Pexels results are filtered for portrait-oriented files and the highest
  available resolution.
- API quotas, rate limits, and stock availability are controlled by the
  respective free-tier providers.
