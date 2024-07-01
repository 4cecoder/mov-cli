from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, List
    from ..media import Metadata
    from ..scraper import Scraper

from devgoldyutils import Colours

from .ui import prompt

from ..media import MetadataType
from ..utils import EpisodeSelector
from ..logger import mov_cli_logger

def handle_episode(
    episode_string: Optional[str], 
    _range: Optional[str], 
    scraper: Scraper, 
    choice: Metadata, 
    fzf_enabled: bool
    ) -> Optional[List[EpisodeSelector] | EpisodeSelector]:
    if choice.type == MetadataType.SINGLE:
        return EpisodeSelector()

    metadata_episodes = scraper.scrape_episodes(choice)

    if _range is not None:
        try:
            episode_selectors = []
            range_episodes = _range.split("-")

            start_episode = int(range_episodes[0])
            final_episode = int(range_episodes[1]) + 1

            season = prompt(
                "Select Season", 
                choices = [season for season in metadata_episodes], 
                display = lambda x: f"Season {x}", 
                fzf_enabled = fzf_enabled
            )

            if season is None:
                return None
            
            season_episode = metadata_episodes[season]
            
            for episode in range(start_episode, final_episode):
                if episode > season_episode:
                    raise Exception(
                        f"This season: {season} doesn't have that many episodes."
                    )

                episode_selectors.append(
                    EpisodeSelector(episode, season)
                )

        except ValueError as e:
            mov_cli_logger.error(
                "Incorrect episode format! This is how it's done --> '1-10' (1 being starting episode and 10 being final episode)\n" \
                    f"Error: {e}"
            )

            return None

        return episode_selectors

    elif episode_string is not None:
        try:
            episode_season = episode_string.split(":")

            episode = 1
            season = 1

            if len(episode_season) == 1 or episode_season[1] == "":
                episode = int(episode_season[0])

            elif len(episode_season) == 2:
                episode = int(episode_season[0])
                season = int(episode_season[1])

        except ValueError as e:
            mov_cli_logger.error(
                "Incorrect episode format! This is how it's done --> '5:1' (5 being episode and 1 being season)\n" \
                    f"Error: {e}"
            )

            return None

        return EpisodeSelector(episode, season)

    mov_cli_logger.info(f"Scraping episodes for '{Colours.CLAY.apply(choice.title)}'...")

    if metadata_episodes.get(None) == 1:
        return EpisodeSelector()

    season = prompt(
        "Select Season", 
        choices = [season for season in metadata_episodes], 
        display = lambda x: f"Season {x}", 
        fzf_enabled = fzf_enabled
    )

    if season is None:
        return None

    episode = prompt(
        "Select Episode", 
        choices = [episode for episode in range(1, metadata_episodes[season] + 1)], 
        display = lambda x: f"Episode {x}",
        fzf_enabled = fzf_enabled
    )

    if episode is None:
        return None

    return EpisodeSelector(episode, season)