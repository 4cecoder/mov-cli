from __future__ import annotations
from typing import TYPE_CHECKING, Type, cast

if TYPE_CHECKING:
    from typing import Optional, Literal

    from ..config import Config
    from ..media import Media, Metadata
    from ..scraper import Scraper, ScrapeEpisodesT
    from ..players import Player

    from ..utils.platform import SUPPORTED_PLATFORMS
    from ..utils.episode_selector import EpisodeSelector

from devgoldyutils import Colours

from .scraper import scrape
from .episode import handle_episode
from .watch_options import watch_options

from ..media import MetadataType
from ..logger import mov_cli_logger
from ..cache import Cache
from ..utils import what_platform, hide_ip
from ..players import PLAYER_TABLE, CustomPlayer

import shutil
from pathlib import Path

def modify_input_conf() -> str:
    user_input_conf = Path.home() / ".config" / "mpv" / "input.conf"
    custom_input_conf = Path.home() / ".config" / "mpv" / "custom_input.conf"

    if not user_input_conf.exists():
        mov_cli_logger.error(f"User input.conf not found at {user_input_conf}")
        return str(user_input_conf)

    shutil.copy(user_input_conf, custom_input_conf)

    with custom_input_conf.open("a") as file:
        file.write("\n# Custom input configs\n")
        file.write("c script-message-to osc play\n")

    return str(custom_input_conf)

def play(media: Media, metadata: Metadata, scraper: Scraper, episode: EpisodeSelector, config: Config) -> Optional[Literal["search"]]:
    platform = what_platform()
    cache = Cache(platform)

    cache.set_cache(str(metadata.id), episode.__dict__)

    chosen_player = __get_player(config, platform)

    quality_string = ""
    episode_details_string = ""

    if metadata.type == MetadataType.MULTI:
        season_string = Colours.CLAY.apply(str(episode.season))
        episode_string = Colours.ORANGE.apply(str(episode.episode))

        episode_details_string = f"episode {episode_string} in season {season_string} of " if episode.season > 1 else f"episode {episode_string} of "

    if config.display_quality:
        quality = media.get_quality()

        if quality is not None:
            quality_string = f"in {Colours.GREEN.apply(quality.name)} "

    mov_cli_logger.info(
        f"Playing {episode_details_string}'{Colours.BLUE.apply(media.title)}' " \
            f"{quality_string}with {chosen_player.display_name}..."
    )

    try:
        if config.player == "mpv":
            input_conf_path = modify_input_conf()
            popen = chosen_player.play(media, f"--input-conf={input_conf_path}")
        else:
            popen = chosen_player.play(media)

        mov_cli_logger.debug(f"Called player with these args -> '{hide_ip(' '.join(popen.args), config.hide_ip)}'")
    except FileNotFoundError as e:
        mov_cli_logger.error(
            f"The player '{chosen_player.display_name}' was not found! " \
                f"Are you sure you have it installed? Are you sure it's in path? \nError: {e}"
        )
        return None

    if popen is None and platform != "iOS":
        mov_cli_logger.error(
            f"The player '{chosen_player.display_name}' is not supported on this platform ({platform}). " \
            "We recommend VLC for iOS, IINA for MacOS and MPV for every other platform."
        )

        return None

    if config.watch_options:
        option = watch_options(popen, chosen_player, platform, media, config.fzf_enabled)

        if option == "next" or option == "previous":
            popen.kill()

            media_episodes = scraper.scrape_episodes(metadata)

            if option == "next":
                episode.episode += 1
            else:
                episode.episode -= 1

            season_episode_count = media_episodes.get(episode.season)

            if season_episode_count is None:
                mov_cli_logger.info("No more episodes :(")
                return None

            result = __handle_next_season(episode, season_episode_count, media_episodes)

            if result is False:
                mov_cli_logger.info("No more episodes :(")
                return None

            media = scrape(metadata, episode, scraper)

            return play(media, metadata, scraper, episode, config)

        elif option == "select":
            popen.kill()

            episode = handle_episode(None, scraper, metadata, config.fzf_enabled)

            if episode is None:
                return None

            media = scrape(metadata, episode, scraper)

            return play(media, metadata, scraper, episode, config)

    popen.wait()

    return None

def __get_player(config: Config, platform: SUPPORTED_PLATFORMS) -> Player:
    player = PLAYER_TABLE.get(config.player, CustomPlayer)

    if player == CustomPlayer:
        player = cast(Type[CustomPlayer], player)

        return player(
            binary = config.player, 
            args = config.player_args
        )

    return player(
        platform = platform, 
        args = config.player_args, 
        debug = config.debug_player, 
        args_override = config.player_args_override
    )

def __handle_next_season(episode: EpisodeSelector, season_episode_count: int, media_episodes: ScrapeEpisodesT) -> bool:

    if episode.episode > season_episode_count:
        next_season = episode.season + 1

        if media_episodes.get(next_season) is None:
            return False

        episode._next_season()

    elif episode.episode <= 1:

        if episode.season <= 1:
            return False

        episode._previous_season(media_episodes)

    return True
