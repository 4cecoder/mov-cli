from __future__ import annotations
from typing import TYPE_CHECKING

import os
import shutil
import subprocess
import unicodedata

__all__ = ("Download",)

if TYPE_CHECKING:
    from .config import Config
    from .media import Multi, Single

from .logger import mov_cli_logger
from devgoldyutils import LoggerAdapter

logger = LoggerAdapter(mov_cli_logger, "Downloader")

class Download():
    def __init__(self, config: Config) -> None:
        self.config = config

    def download(self, media: Multi | Single, subtitles: str = None) -> subprocess.Popen:
        title = unicodedata.normalize('NFKD', media.display_name).encode('ascii', 'ignore').decode('ascii') # normalize title

        file_path = os.path.join(self.config.download_location, title + ".mp4")

        use_yt_dlp = self.config.use_yt_dlp

        if shutil.which("yt-dlp") is None:
            logger.warning("yt-dlp was not found, defaulting to ffmpeg!")
            use_yt_dlp = False

        elif media.audio_url is not None:
            logger.warning("Can't use yt-dlp as this media contains an audio url, defaulting to ffmpeg!")
            use_yt_dlp = False

        if use_yt_dlp:
            logger.info("Downloading via yt-dlp...")

            args = [
                "yt-dlp", 
                media.url, 
                "-o", 
                file_path,
                "--downloader", 
                "ffmpeg",
                "--hls-use-mpegts",
            ]

            if self.config.debug is False:
                args.append("--no-warnings")
    
            if media.referrer is not None:
                args.extend(["--add-header", f"Referer:{media.referrer}"])

        else:
            logger.info("Downloading via ffmpeg...")

            args = [
                "ffmpeg",
                "-n",
                "-headers",
                f"Referer: {media.referrer}",
                "-i",
                media.url,
            ]

            if media.audio_url:
                args.extend(["-i", media.audio_url])

            if subtitles:
                args.extend(["-vf", f"subtitle={subtitles}"])

            args.extend(["-c", "copy", file_path])

        return subprocess.Popen(args)

