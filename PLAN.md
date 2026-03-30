# PodForge - Architecture Plan

## What It Does
Turn any topic, URL, PDF, or text into a fully-produced podcast episode with:
- Multi-voice AI conversation (2+ speakers)
- Intro/outro music
- Sound effects and transitions
- Professional audio mastering
- Ready-to-publish MP3 with metadata

## Pipeline

```
INPUT -> EXTRACT -> SCRIPT -> TTS -> MIX -> OUTPUT
```

### Stage 1: INPUT
- Topic string: "Explain quantum computing"
- URL: scrape and extract article text
- File: PDF, TXT, MD
- Stdin: pipe text in

### Stage 2: EXTRACT
- URL -> trafilatura/readability for clean text extraction
- PDF -> pdfplumber for text extraction
- Markdown -> strip formatting
- Truncate/summarize if too long for LLM context

### Stage 3: SCRIPT (LLM)
- Send extracted content to LLM (Claude/OpenAI/local)
- Generate a podcast script in structured format:
  ```yaml
  - speaker: host
    text: "Welcome to the show! Today we're diving into..."
  - speaker: guest
    text: "Thanks for having me. This is fascinating because..."
  - sfx: transition
  - speaker: host
    text: "Let's break that down..."
  ```
- Configurable: tone, length, num speakers, style (casual/academic/debate)
- Script is a YAML file - user can edit before TTS

### Stage 4: TTS
- ElevenLabs (primary, highest quality)
- OpenAI TTS (fallback)
- Edge TTS (free fallback)
- Each speaker gets a distinct voice
- Generate individual audio segments per line

### Stage 5: MIX (FFmpeg)
- Concatenate speech segments with natural pauses
- Layer intro music (fade in, duck under speech, fade out)
- Add transition sounds between segments
- Layer subtle background music (ducked)
- Add outro music
- Normalize audio levels (loudnorm)
- Apply light compression for podcast standards

### Stage 6: OUTPUT
- Final MP3 with ID3 tags (title, artist, description, artwork)
- SRT subtitle file
- Transcript (text)
- Episode metadata JSON

## CLI Interface

```bash
# Basic usage
podforge "Explain quantum computing in simple terms"

# From URL
podforge --url https://arxiv.org/abs/2301.00001

# From file
podforge --file paper.pdf

# Full options
podforge "Topic here" \
  --speakers 2 \
  --style casual \
  --length 10 \       # minutes target
  --tts elevenlabs \
  --voice-host "Rachel" \
  --voice-guest "Adam" \
  --music auto \
  --output episode.mp3

# Edit script before generating audio
podforge "Topic" --script-only > script.yaml
# ... edit script.yaml ...
podforge --from-script script.yaml --output episode.mp3
```

## Project Structure

```
podforge/
├── pyproject.toml
├── README.md
├── LICENSE
├── podforge/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── cli.py               # CLI argument parsing (click)
│   ├── pipeline.py          # Orchestrates the full pipeline
│   ├── extract/
│   │   ├── __init__.py
│   │   ├── url.py           # URL text extraction
│   │   ├── pdf.py           # PDF text extraction
│   │   └── text.py          # Plain text/markdown
│   ├── script/
│   │   ├── __init__.py
│   │   ├── generator.py     # LLM script generation
│   │   └── prompts.py       # System prompts for different styles
│   ├── tts/
│   │   ├── __init__.py
│   │   ├── base.py          # TTS interface
│   │   ├── elevenlabs.py    # ElevenLabs backend
│   │   ├── openai.py        # OpenAI TTS backend
│   │   └── edge.py          # Edge TTS (free) backend
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── mixer.py         # FFmpeg audio mixing
│   │   ├── music.py         # Intro/outro music handling
│   │   └── effects.py       # Sound effects
│   ├── output/
│   │   ├── __init__.py
│   │   ├── metadata.py      # ID3 tags, episode info
│   │   └── transcript.py    # SRT/text transcript
│   └── assets/
│       ├── music/            # Bundled royalty-free jingles
│       └── sfx/              # Bundled sound effects
└── tests/
```

## Dependencies
- click (CLI)
- anthropic / openai (LLM)
- elevenlabs (TTS)
- edge-tts (free TTS)
- trafilatura (URL extraction)
- pdfplumber (PDF extraction)
- pyyaml (script format)
- mutagen (ID3 tags)
- rich (terminal UI)

## MVP Scope (What We Build Now)
1. Topic/URL/text input
2. LLM script generation (Claude via anthropic SDK)
3. ElevenLabs + Edge TTS
4. FFmpeg mixing with intro music + transitions
5. MP3 output with metadata
6. Clean CLI with progress indicators
