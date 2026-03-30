"""Generate podcast scripts using Claude."""
import logging
import os

import anthropic
import yaml

from .prompts import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)


def generate_script(
    content: str,
    style: str = "casual",
    length_minutes: int = 10,
    speakers: int = 2,
    speaker_names: list[str] | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> list[dict]:
    """Generate a podcast script from source content using Claude.

    Args:
        content: Source material text.
        style: Podcast style (casual, academic, debate, storytelling).
        length_minutes: Target episode length in minutes.
        speakers: Number of speakers.
        speaker_names: Custom speaker names. Defaults to Alex, Sam, etc.
        model: Claude model to use.

    Returns:
        List of script entries (dicts with speaker/text or sfx keys).

    Raises:
        ValueError: If the API key is not set or response is invalid.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Get your API key at https://console.anthropic.com/"
        )

    if speaker_names is None:
        default_names = ["Alex", "Sam", "Jordan", "Riley", "Casey"]
        speaker_names = default_names[:speakers]

    system_prompt = build_system_prompt(
        style=style,
        length_minutes=length_minutes,
        speaker_names=speaker_names,
    )
    user_prompt = build_user_prompt(content)

    logger.info(f"Generating script with Claude ({model}), style={style}, length={length_minutes}min")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        # Remove first line (```yaml or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines)

    try:
        script = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse script YAML: {e}")
        raise ValueError(f"LLM returned invalid YAML script: {e}") from e

    if not isinstance(script, list):
        raise ValueError("LLM returned a script that is not a list of entries")

    # Validate script entries
    validated = []
    for entry in script:
        if not isinstance(entry, dict):
            logger.warning(f"Skipping non-dict script entry: {entry}")
            continue
        if "speaker" in entry and "text" in entry:
            validated.append({"speaker": str(entry["speaker"]), "text": str(entry["text"])})
        elif "sfx" in entry:
            validated.append({"sfx": str(entry["sfx"])})
        else:
            logger.warning(f"Skipping invalid script entry: {entry}")

    if not validated:
        raise ValueError("No valid entries in generated script")

    logger.info(f"Generated script with {len(validated)} entries")
    return validated


def save_script(script: list[dict], output_path: str) -> None:
    """Save a script to a YAML file.

    Args:
        script: List of script entries.
        output_path: Path to save the YAML file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(script, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    logger.info(f"Script saved to {output_path}")


def load_script(input_path: str) -> list[dict]:
    """Load a script from a YAML file.

    Args:
        input_path: Path to the YAML script file.

    Returns:
        List of script entries.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the file is not valid YAML or has invalid structure.
    """
    from pathlib import Path

    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Script file not found: {input_path}")

    with open(path, "r", encoding="utf-8") as f:
        script = yaml.safe_load(f.read())

    if not isinstance(script, list):
        raise ValueError(f"Script file must contain a YAML list, got {type(script).__name__}")

    # Validate entries
    for i, entry in enumerate(script):
        if not isinstance(entry, dict):
            raise ValueError(f"Script entry {i} is not a dict: {entry}")
        if "speaker" not in entry and "sfx" not in entry:
            raise ValueError(f"Script entry {i} must have 'speaker' or 'sfx' key: {entry}")
        if "speaker" in entry and "text" not in entry:
            raise ValueError(f"Script entry {i} has 'speaker' but no 'text': {entry}")

    logger.info(f"Loaded script with {len(script)} entries from {input_path}")
    return script
