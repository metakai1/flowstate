"""CLI entry points."""

import click

from .analyze import analyze
from .corpus import corpus
from .download_videos import download_videos
from .run import run
from .write_metadata import write_metadata


@click.group()
@click.version_option()
def main():
    """FLOWSTATE - DJ Decision Support System.

    Analyze your music library and get real-time track recommendations
    based on energy, key, vibe, and danceability.
    """
    pass


main.add_command(analyze)
main.add_command(corpus)
main.add_command(download_videos)
main.add_command(run)
main.add_command(write_metadata)


if __name__ == "__main__":
    main()
