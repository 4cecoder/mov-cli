from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Type, Optional, Tuple, List, Dict

    from .plugins import PluginsDataT

    from ..media import Metadata, Media
    from ..http_client import HTTPClient
    from ..config import Config, ScrapersConfigT
    from ..utils.episode_selector import EpisodeSelector
    from ..scraper import Scraper, ScraperOptionsT

from thefuzz import fuzz
from devgoldyutils import Colours

from .ui import prompt
from .plugins import get_plugins_data, handle_internal_plugin_error

from ..utils import what_platform
from ..logger import mov_cli_logger

def scrape(choice: Metadata, episode: EpisodeSelector, scraper: Scraper) -> Optional[Media]:
    mov_cli_logger.info(f"Scraping '{Colours.CLAY.apply(choice.title)}'...")

    try:
        media = scraper.scrape(choice, episode)
    except Exception as e:
        handle_internal_plugin_error(e)

    return media

def use_scraper(
    selected_scraper: Tuple[str, Type[Scraper], ScraperOptionsT], 
    config: Config, 
    http_client: HTTPClient
) -> Scraper:
    scraper_name, scraper_class, scraper_options = selected_scraper

    mov_cli_logger.info(f"Using '{Colours.BLUE.apply(scraper_name)}' scraper...")

    try:
        chosen_scraper = scraper_class(config, http_client, scraper_options)
    except Exception as e:
        handle_internal_plugin_error(e)

    return chosen_scraper

def select_scraper(plugins: Dict[str, str], scrapers: ScrapersConfigT, fzf_enabled: bool, default_scraper: Optional[str] = None) -> Optional[Tuple[str, Type[Scraper], ScraperOptionsT]]:
    plugins_data = get_plugins_data(plugins)

    if default_scraper is not None:
        scraper_name, scraper_or_available_scrapers, scraper_options = get_scraper(default_scraper, plugins_data, scrapers)

        if scraper_name is None:
            mov_cli_logger.error(
                f"Could not find a scraper by the id '{default_scraper}'! Are you sure the plugin is installed and in your config? " \
                    "Read the wiki for more on that: 'https://github.com/mov-cli/mov-cli/wiki#plugins'."
            )

            scrapers_beautifully_formatted = Colours.ORANGE.apply(f"{f'{Colours.RESET} | {Colours.ORANGE}'.join(scraper_or_available_scrapers)}")

            print(f"\nAvailable Scrapers -> {scrapers_beautifully_formatted}")

            did_you_mean_these = [(x, fuzz.ratio(default_scraper, x)) for x in scraper_or_available_scrapers]
            did_you_mean_these.sort(key = lambda x: x[1], reverse = True)

            if len(did_you_mean_these) > 0:
                print(Colours.PURPLE.apply(f"\n* Did you mean: {Colours.GREEN}{did_you_mean_these[0][0]}\n"))

            return None

        return scraper_name, scraper_or_available_scrapers, scraper_options

    chosen_plugin = prompt(
        "Select a plugin", 
        choices = plugins_data, 
        display = lambda x: f"{Colours.ORANGE.apply(x[0])} [{Colours.PINK_GREY.apply(x[1])}]", 
        fzf_enabled = fzf_enabled
    )

    plaform = what_platform()

    if chosen_plugin is not None:
        plugin_namespace, _, plugin = chosen_plugin

        plugin_default_scraper = plugin.default_scraper(plaform)

        chosen_scraper = prompt(
            "Select a scraper", 
            choices = [scraper for scraper in plugin.scrapers], 
            display = (
                lambda x: Colours.BLUE.apply(x[0].lower()) + Colours.CLAY.apply(" [DEFAULT]") if x[1] == plugin_default_scraper else Colours.BLUE.apply(x[0].lower())
            ), 
            fzf_enabled = fzf_enabled
        )

        if chosen_scraper is None:
            return None

        scraper_name, scraper = chosen_scraper

        return f"{plugin_namespace}.{scraper_name}".lower(), scraper, {}

    return None

def steal_scraper_args(query: List[str]) -> Tuple[ScraperOptionsT, List[str]]:
    args_to_kidnap: List[str] = []
    arg_values_to_kidnap: List[str] = []

    scraper_options_args: List[Tuple[str, str | bool]] = []

    for index, arg in enumerate(query):

        if arg.startswith("--"):
            arg_value = True

            try:
                arg_value_maybe = query[index + 1]

                if not arg_value_maybe.startswith("--"):
                    arg_value = arg_value_maybe

                    arg_values_to_kidnap.append(arg_value)

            except IndexError as e:
                mov_cli_logger.debug(
                    f"No scraper option argument value was found after '{arg}' so we'll assume this argument is a flag. \nError: {e}"
                )

            args_to_kidnap.append(arg)
            scraper_options_args.append((arg.replace("--", "").replace("-", "_"), arg_value))

    # KIDNAP THEM ARGS!!!!!
    for arg_or_arg_value in args_to_kidnap + arg_values_to_kidnap:
        query.remove(arg_or_arg_value)

    mov_cli_logger.debug(f"Scraper args picked up on --> {scraper_options_args}")

    valid_scraper_args = [arg.replace("--", "").replace("-", "_") for arg in args_to_kidnap]

    return dict(scraper_options_args), valid_scraper_args

def get_scraper(scraper_id: str, plugins_data: PluginsDataT, user_defined_scrapers: ScrapersConfigT) -> Tuple[str, Type[Scraper] | Tuple[None, List[str]], ScraperOptionsT]:
    scraper_options = {}
    available_scrapers = []

    # scraper namespace override.
    for scraper_namespace, scraper_data in user_defined_scrapers.items():

        if scraper_id.lower() == scraper_namespace.lower():
            mov_cli_logger.debug(f"Using the scraper overridden namespace '{scraper_namespace}'...")
            scraper_id = scraper_data["namespace"]
            scraper_options = scraper_data["options"]

    platform = what_platform().upper()

    for plugin_namespace, _, plugin in plugins_data:
        plugin_scrapers = plugin.hook_data["scrapers"]

        if scraper_id.lower() == plugin_namespace.lower() and f"{platform}.DEFAULT" in plugin_scrapers:
            return f"{plugin_namespace}.{platform}.DEFAULT", plugin_scrapers[f"{platform}.DEFAULT"], scraper_options

        elif scraper_id.lower() == plugin_namespace.lower() and "DEFAULT" in plugin_scrapers:
            return f"{plugin_namespace}.DEFAULT", plugin_scrapers["DEFAULT"], scraper_options

        for scraper_name, scraper in plugin_scrapers.items():
            id = f"{plugin_namespace}.{scraper_name}".lower()

            available_scrapers.append(id)

            if scraper_id.lower() == id:
                return id, scraper, scraper_options

    return None, available_scrapers, scraper_options

def validate_scraper_args(scrape_options: ScraperOptionsT, valid_scraper_args: List[str]) -> List[str]:
    invalid_args = [arg for arg in scrape_options if arg not in valid_scraper_args]
    return invalid_args
