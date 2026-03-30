"""System prompts for podcast script generation."""

STYLE_PROMPTS = {
    "casual": (
        "You are a podcast script writer creating a fun, engaging, casual conversation "
        "between hosts. The tone should be like two friends chatting at a coffee shop — "
        "relaxed, enthusiastic, and accessible. Use everyday language, analogies, and humor. "
        "Avoid jargon unless you immediately explain it in simple terms."
    ),
    "academic": (
        "You are a podcast script writer creating an informative, intellectually rigorous "
        "discussion. The tone should be like a university seminar — thoughtful, precise, "
        "and well-reasoned. Speakers should reference evidence, consider multiple perspectives, "
        "and build arguments carefully. Still conversational, but with scholarly depth."
    ),
    "debate": (
        "You are a podcast script writer creating a lively, structured debate. "
        "Speakers should take opposing positions and challenge each other's arguments "
        "with evidence and logic. Include moments of agreement and concession to keep "
        "it productive, not hostile. The tone should be passionate but respectful."
    ),
    "storytelling": (
        "You are a podcast script writer creating a narrative-driven episode. "
        "Weave the information into compelling stories, anecdotes, and vivid descriptions. "
        "Build tension and curiosity. Use the conversation format to reveal information "
        "gradually, with one speaker guiding the other through discoveries."
    ),
}

BASE_SYSTEM_PROMPT = """\
You are an expert podcast script writer. Your job is to transform source material into \
a natural, engaging podcast conversation.

CRITICAL RULES FOR NATURAL DIALOGUE:
1. Include filler words naturally: "um", "uh", "like", "you know", "I mean", "right", "so"
2. Add verbal reactions: "Oh wow", "Hmm", "Exactly!", "Wait, really?", "That's wild", "Huh"
3. Include interruptions and overlapping ideas — one speaker cutting in with excitement
4. Use contractions always: "it's", "that's", "don't", "we're", "they've"
5. Add self-corrections: "Well, it's not exactly — actually, let me put it this way..."
6. Include laughter cues: "[laughs]", "[chuckles]"
7. Vary sentence length dramatically — short punchy reactions mixed with longer explanations
8. Speakers should reference each other by name occasionally
9. Add thinking pauses: "Hmm, let me think about that...", "That's a good question..."
10. Include callbacks to earlier points: "Going back to what you said about..."

The script MUST be output as a YAML list. Each entry is either a speaker line or a sound effect.

Speaker entry format:
- speaker: <name>
  text: "<dialogue>"

Sound effect entry format:
- sfx: transition

Rules for sfx:
- Place a "transition" sfx when changing major topics
- Do NOT overuse sfx — typically 2-4 per episode
- The intro and outro music are added automatically, do NOT script them

{style_prompt}

TARGET LENGTH: Approximately {target_lines} dialogue lines for a ~{length_minutes} minute episode.
SPEAKERS: {speaker_names}
"""

SCRIPT_USER_PROMPT = """\
Create a podcast script about the following content. Make it sound like a REAL conversation \
between real people — not a scripted reading. The speakers should genuinely engage with \
the material, ask each other questions, share reactions, and make the topic accessible \
and entertaining.

SOURCE MATERIAL:
---
{content}
---

Remember: Output ONLY valid YAML. No markdown code fences. No extra text before or after.\
"""


def build_system_prompt(
    style: str = "casual",
    length_minutes: int = 10,
    speaker_names: list[str] | None = None,
) -> str:
    """Build the complete system prompt for script generation.

    Args:
        style: Podcast style (casual, academic, debate, storytelling).
        length_minutes: Target episode length in minutes.
        speaker_names: List of speaker names.

    Returns:
        Complete system prompt string.
    """
    if speaker_names is None:
        speaker_names = ["Alex", "Sam"]

    style_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["casual"])

    # Rough estimate: ~15 lines per minute of dialogue
    target_lines = length_minutes * 15

    return BASE_SYSTEM_PROMPT.format(
        style_prompt=style_prompt,
        target_lines=target_lines,
        length_minutes=length_minutes,
        speaker_names=", ".join(speaker_names),
    )


def build_user_prompt(content: str) -> str:
    """Build the user prompt with source content.

    Args:
        content: The source material to discuss.

    Returns:
        Formatted user prompt.
    """
    return SCRIPT_USER_PROMPT.format(content=content)
