"""PodForge CLI - Turn any content into a podcast."""
import logging
import sys

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel

from . import __version__

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich handler.

    Args:
        verbose: Enable debug logging.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, show_path=False, rich_tracebacks=True)],
    )
    # Quiet noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("trafilatura").setLevel(logging.WARNING)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("topic", required=False)
@click.option("--url", "-u", help="URL to extract content from")
@click.option("--file", "-f", "file_path", help="File path (PDF, TXT, MD) to extract content from")
@click.option("--from-script", "from_script", help="Resume from an existing YAML script file")
@click.option("--script-only", is_flag=True, help="Only generate the YAML script, skip audio")
@click.option("--output", "-o", default="episode.mp3", help="Output file path (default: episode.mp3)")
@click.option("--speakers", "-s", default=2, type=click.IntRange(2, 5), help="Number of speakers (2-5)")
@click.option(
    "--style",
    type=click.Choice(["casual", "academic", "debate", "storytelling"], case_sensitive=False),
    default="casual",
    help="Podcast conversation style",
)
@click.option("--length", "-l", default=10, type=click.IntRange(1, 60), help="Target length in minutes")
@click.option(
    "--tts",
    "tts_backend",
    type=click.Choice(["elevenlabs", "edge", "openai"], case_sensitive=False),
    default="edge",
    help="TTS backend (default: edge - free)",
)
@click.option("--voice-host", help="Voice for the host speaker")
@click.option("--voice-guest", help="Voice for the guest speaker")
@click.option("--model", default="claude-sonnet-4-20250514", help="Claude model for script generation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose/debug logging")
@click.version_option(version=__version__, prog_name="podforge")
def cli(
    topic,
    url,
    file_path,
    from_script,
    script_only,
    output,
    speakers,
    style,
    length,
    tts_backend,
    voice_host,
    voice_guest,
    model,
    verbose,
):
    """🎙️  PodForge - Turn any content into a podcast.

    Generate a fully-produced podcast episode from a topic, URL, PDF, or text file.
    Uses AI to create natural conversations and professional audio production.

    \b
    Examples:
      podforge "Explain quantum computing"
      podforge --url https://example.com/article
      podforge --file paper.pdf --style academic
      podforge "AI safety" --script-only > script.yaml
      podforge --from-script script.yaml -o episode.mp3
    """
    setup_logging(verbose)

    # Show banner
    console.print(
        Panel(
            f"[bold cyan]PodForge[/bold cyan] v{__version__}\n"
            "[dim]AI-powered podcast generator[/dim]",
            border_style="cyan",
        )
    )

    # Validate inputs
    inputs_provided = sum([
        topic is not None,
        url is not None,
        file_path is not None,
        from_script is not None,
        not sys.stdin.isatty(),
    ])

    if inputs_provided == 0:
        console.print("[red]Error:[/red] No input provided. Specify a topic, --url, --file, or pipe text.")
        console.print("Run [bold]podforge --help[/bold] for usage information.")
        raise SystemExit(1)

    if inputs_provided > 1 and not (topic and not url and not file_path and not from_script):
        console.print("[yellow]Warning:[/yellow] Multiple inputs provided. Using the first one found.")

    # Build voice map
    voice_map = {}
    if voice_host:
        voice_map["host"] = voice_host
        voice_map["Alex"] = voice_host
    if voice_guest:
        voice_map["guest"] = voice_guest
        voice_map["Sam"] = voice_guest

    # Detect stdin
    from_stdin = not sys.stdin.isatty() and not any([topic, url, file_path, from_script])

    try:
        from .pipeline import run_pipeline

        result = run_pipeline(
            topic=topic,
            url=url,
            file_path=file_path,
            from_stdin=from_stdin,
            from_script=from_script,
            script_only=script_only,
            output=output,
            speakers=speakers,
            style=style,
            length=length,
            tts_backend=tts_backend,
            voice_map=voice_map,
            model=model,
        )

    except ValueError as e:
        console.print(f"[red]Configuration error:[/red] {e}")
        raise SystemExit(1)
    except FileNotFoundError as e:
        console.print(f"[red]File not found:[/red] {e}")
        raise SystemExit(1)
    except RuntimeError as e:
        console.print(f"[red]Runtime error:[/red] {e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise SystemExit(130)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error")
        console.print(f"[red]Unexpected error:[/red] {e}")
        console.print("[dim]Run with --verbose for more details[/dim]")
        raise SystemExit(1)
