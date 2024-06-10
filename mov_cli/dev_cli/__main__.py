from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    ...

import os
import typer
import shutil
from subprocess import call

from ..cache import Cache
from ..utils import what_platform

__all__ = ()

app = typer.Typer(
    pretty_exceptions_enable = False, 
    help = "Developer only commands to be executed from scripts and assist with testing and development of mov-cli plugins."
)

test_app = typer.Typer(name = "test", help = "Run tests on plugins varies mov-cli functionalities.")
preview_app = typer.Typer(name = "preview", help = "Dev command used by stuff like fzf to display images from mov-cli in the terminal.")

app.add_typer(test_app)
app.add_typer(preview_app)

@preview_app.command(help = "Preview image from mov-cli cache to terminal.")
def image(id: str):
    cache = Cache(
        platform = what_platform(), 
        section = "image_urls"
    )

    image_url = cache.get_cache(id)

    if image_url is None:
        print("No Image :(")
        return False

    fzf_preview_lines = os.environ["FZF_PREVIEW_LINES"]
    fzf_preview_columns = os.environ["FZF_PREVIEW_COLUMNS"]

    if "KITTY_WINDOW_ID" in os.environ:
        call([
            "kitty", 
            "icat", 
            "--clear", 
            "--transfer-mode=memory", 
            "--unicode-placeholder", 
            "--stdin=no", 
            f"--place={fzf_preview_columns}x{fzf_preview_lines}@0x0", 
            image_url
        ])

    elif shutil.which("imgcat") is not None: # NOTE: imgcat doesn't work for some reason.
        call([
            "imgcat", f"{image_url}'"
        ])

    # else:
    #    call(["fzf-preview.sh", image_url])

@test_app.command(help = "Automatically tests the **entire** plugin for faults.")
def plugin(
    plugin_name: str = typer.Argument(help = "The name of the plugin to test."), 
    query: str = typer.Argument("*", help = "The query to use if searching is being tested.")
):
    # NOTE: I'll be using a series of pytest tests here.
    ...