from typing import Literal, Optional

from pydantic import BaseModel

__all__ = (
    "SearchModel", 
    "StreamModel", 
    "MetadataModel", 
    "StreamResultModel"
)

class SearchModel(BaseModel):
    query: str
    limit: int

class StreamModel(BaseModel):
    watch_url: str
    scraper: Literal["yt-dlp", "pytube"]

class MetadataModel(BaseModel):
    watch_url: str
    title: str
    type: int
    image_url: str

class StreamResultModel(BaseModel):
    url: str
    audio_url: Optional[str]
    title: str
    subtitles_url: Optional[str]