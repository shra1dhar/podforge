# PodForge

**Turn any topic, URL, PDF, or text into a fully-produced podcast episode.**

PodForge generates natural multi-voice AI conversations with intro/outro music, sound effects, transitions, and professional loudness normalization -- all from a single command. Feed it a topic, a web article, a research paper, or raw text, and get back a polished MP3 ready to publish.

---

## Features

- **Multi-voice AI conversation** -- 2 to 5 distinct speakers with natural dialogue, filler words, reactions, interruptions, and self-corrections
- **Multiple input sources** -- topic string, URL, PDF, text file, Markdown, or stdin
- **Four podcast styles** -- `casual`, `academic`, `debate`, `storytelling`
- **Three TTS backends** -- ElevenLabs (premium), Edge TTS (free, default), OpenAI TTS
- **Professional audio production** -- FFmpeg-powered mixing with intro/outro music, transition sound effects, and loudness normalization (EBU R128, -16 LUFS)
- **Editable YAML scripts** -- generate a script, review or edit it by hand, then render to audio (human-in-the-loop workflow)
- **Rich output** -- MP3 with ID3 tags, SRT subtitles, plain-text transcript, and JSON metadata

---

## Installation

### Prerequisites

FFmpeg must be installed on your system:

```bash
# Debian / Ubuntu
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (via Chocolatey)
choco install ffmpeg
```

### Install PodForge

```bash
# From the project root
pip install .

# Or in editable/development mode
pip install -e .
```

PodForge requires Python 3.10 or later.

---

## Quick Start

1. **Set your API key** (required for script generation):

   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

2. **Generate a podcast**:

   ```bash
   podforge "Explain quantum computing in simple terms"
   ```

   This produces `episode.mp3`, `episode.srt`, and `episode_transcript.txt` in the current directory using the free Edge TTS backend.

3. **(Optional) Enable premium voices**:

   ```bash
   export ELEVENLABS_API_KEY="..."
   podforge "The history of jazz" --tts elevenlabs
   ```

---

## Usage Examples

### From a topic

```bash
podforge "The rise and fall of the Roman Empire"
```

### From a URL

```bash
podforge --url https://example.com/article
```

### From a PDF

```bash
podforge --file research-paper.pdf --style academic
```

### From a text file

```bash
podforge --file notes.txt
```

### From stdin

```bash
cat meeting-notes.txt | podforge
```

### Script-only mode (generate YAML, skip audio)

```bash
podforge "AI safety" --script-only > script.yaml
```

### Resume from an edited script

```bash
podforge --from-script script.yaml -o episode.mp3
```

### Full options example

```bash
podforge "Dark matter and dark energy" \
  --speakers 3 \
  --style debate \
  --length 20 \
  --tts elevenlabs \
  --voice-host rachel \
  --voice-guest adam \
  --output dark-matter-ep.mp3
```

---

## CLI Reference

```
Usage: podforge [OPTIONS] [TOPIC]

Options:
  -u, --url TEXT              URL to extract content from
  -f, --file TEXT             File path (PDF, TXT, MD) to extract content from
      --from-script TEXT      Resume from an existing YAML script file
      --script-only           Only generate the YAML script, skip audio
  -o, --output TEXT           Output file path (default: episode.mp3)
  -s, --speakers INTEGER      Number of speakers, 2-5 (default: 2)
      --style TEXT            Podcast style: casual | academic | debate | storytelling
  -l, --length INTEGER        Target length in minutes, 1-60 (default: 10)
      --tts TEXT              TTS backend: elevenlabs | edge | openai (default: edge)
      --voice-host TEXT       Voice for the host speaker
      --voice-guest TEXT      Voice for the guest speaker
      --model TEXT            Claude model for script generation
  -v, --verbose               Enable debug logging
  -h, --help                  Show help message and exit
      --version               Show version and exit
```

---

## Script Format

PodForge uses a simple YAML list as its intermediate script format. Each entry is either a **speech line** or a **sound effect cue**:

```yaml
- speaker: Alex
  text: "Welcome back to the show! Today we're diving into something wild -- quantum computing."

- speaker: Sam
  text: "Oh man, I've been looking forward to this one. So, like, where do we even start?"

- sfx: transition

- speaker: Alex
  text: "Okay so -- and this is the mind-bending part -- a qubit can be zero AND one at the same time."

- speaker: Sam
  text: "Wait, really? That's... huh. How does that even work?"
```

### Editing scripts

The `--script-only` flag outputs the YAML script without producing audio. You can then:

1. Review the conversation for accuracy and flow
2. Rewrite lines, add or remove speakers, insert `sfx: transition` markers
3. Render the final audio with `--from-script`

This human-in-the-loop workflow lets you keep full editorial control over the content.

---

## Configuration

### Environment Variables

| Variable             | Required | Description                                      |
|----------------------|----------|--------------------------------------------------|
| `ANTHROPIC_API_KEY`  | Yes      | Claude API key for script generation ([get one](https://console.anthropic.com/)) |
| `ELEVENLABS_API_KEY` | No       | Required only when using `--tts elevenlabs`      |
| `OPENAI_API_KEY`     | No       | Required only when using `--tts openai`          |

### TTS Backend Comparison

| Backend      | Cost | Quality   | Speed  | Voices                         | Flag                 |
|--------------|------|-----------|--------|--------------------------------|----------------------|
| **Edge TTS** | Free | Good      | Fast   | Guy, Jenny, Aria, Davis, +more | `--tts edge` (default) |
| **ElevenLabs** | Paid | Excellent | Medium | Rachel, Adam, Bella, Josh, +more | `--tts elevenlabs` |
| **OpenAI**   | Paid | Very Good | Fast   | alloy, echo, fable, onyx, nova, shimmer | `--tts openai` |

---

## Architecture

PodForge follows a linear six-stage pipeline:

```
INPUT  -->  EXTRACT  -->  SCRIPT  -->  TTS  -->  MIX  -->  OUTPUT
```

| Stage       | Description                                                       |
|-------------|-------------------------------------------------------------------|
| **Input**   | Accept topic string, URL, PDF, text file, or stdin                |
| **Extract** | Pull and clean text content (Trafilatura for URLs, pdfplumber for PDFs) |
| **Script**  | Generate a multi-speaker YAML conversation via Claude             |
| **TTS**     | Synthesize each speech line to audio using the selected backend   |
| **Mix**     | Concatenate segments with intro/outro music, transitions, pauses, and apply loudness normalization via FFmpeg |
| **Output**  | Write MP3 (with ID3 tags), SRT subtitles, text transcript, and JSON metadata |

### Project Layout

```
podforge/
  cli.py              # Click CLI entry point
  pipeline.py         # Pipeline orchestrator
  extract/            # Content extraction (URL, PDF, text, stdin)
  script/             # Script generation and prompt engineering
  tts/                # TTS backends (ElevenLabs, Edge, OpenAI)
  audio/              # FFmpeg mixing, music, sound effects
  output/             # ID3 tagging, transcripts, metadata
```

---

## License

MIT
