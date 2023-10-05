from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

from enum import Enum
from dataclasses import dataclass

__all__ = ("MetadataType", "Metadata", "Media")

class MetadataType(Enum):
    SERIES = 0
    MOVIE = 1
    LIVE_TV = 2

@dataclass
class Metadata: # TODO: Fields that take None, set them to None by default.
    title: str
    id: str | None
    url: str | None
    type: MetadataType

    # Extras
    year: str | None
    image_url: str | None
    cast: List[str] | None
    description: str | None
    genre: List[str] | None

class Media():
    """Represents any piece of media in mov-cli that can be streamed or downloaded."""
    def __init__(self, url: str, title: str, referrer: str) -> None:
        self.url = url
        """The stream-able url."""
        self.title = title
        """A title to represent this stream-able media."""
        self.referrer = referrer # TODO: Add docstring for this.