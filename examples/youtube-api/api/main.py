from typing import List

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from mov_cli import Config
from mov_cli.utils import EpisodeSelector
from mov_cli.http_client import HTTPClient
from mov_cli_youtube import YTDlpScraper, PyTubeScraper

from . import __version__, errors, models

__all__ = ("app",)

app = FastAPI(
    version = __version__
)

mov_cli_conf = Config()
mov_cli_http = HTTPClient(mov_cli_conf)

@app.post(
    "/search",
    openapi_extra = {
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": models.SearchModel.model_json_schema()
                }
            },
            "required": True,
        },
    },
    response_class = JSONResponse,
    responses = {
        200: {
            "content": {    
                "application/json": {}
            },
            "description": "Returns YouTube Metadata",
        },
        404: {
            "model": errors.NoMetadata, 
            "description": "No Metadata was returned by mov-cli"
        }
    },
)
async def search(data: models.SearchModel) -> List[models.MetadataModel]:
    scraper = YTDlpScraper(
        mov_cli_conf, mov_cli_http
    )

    search_results = list(
        scraper.search(
            query = data.query, 
            limit = data.limit
        )
    )

    if len(search_results) == 0:
        return JSONResponse(
            status_code = 404, 
            content = {
                "error": "NoMetadata",
                "message": "mov-cli-youtube didn't return any metadata"
            }
        )

    return [
        {
            "watch_url": result.id, 
            "title": result.title, 
            "type": result.type.value,
            "image_url": result.image_url
        } for result in search_results
    ]

@app.post(
    "/get_stream",
        openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": models.StreamModel.model_json_schema()
                }
            },
            "required": True,
        },
    },
    response_class = JSONResponse,
    responses = {
        200: {
            "content": {},
            "description": "Returns Scraped Data from YouTube",
        },
        404: {
            "model": errors.NoVideoToScrape, 
            "description": "No video was found to scrape"
        }
    },
)
async def get_stream(data: models.StreamModel) -> models.StreamResultModel:
    if data.scraper == "yt-dlp":
        scraper = YTDlpScraper(
            mov_cli_conf, mov_cli_http
        )
    else:
        scraper = PyTubeScraper(
            mov_cli_conf, mov_cli_http
        )

    video_metadata = next(scraper.search(data.watch_url), None)

    if video_metadata is None:
        return JSONResponse(
            status_code = 404, 
            content = {
                "error": "NoVideoToScrape",
                "message": "mov-cli-youtube didn't find any video with that ID to scrape."
            }
        )

    media = scraper.scrape(
        metadata = video_metadata, 
        _ = EpisodeSelector()
    )

    return {
        "url":  media.url, 
        "audio_url": media.audio_url, 
        "title": media.title, 
        "subtitles_url": media.subtitles
    }