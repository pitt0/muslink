from typing import TypedDict


class SpArtistObj(TypedDict):
    name: str


class SpTrackObj(TypedDict):
    id: str
    name: str
    artists: list[SpArtistObj]


class SpPlaylistTracks(TypedDict):
    total: int
    items: list[SpTrackObj]


class YtArtistObj(TypedDict):
    name: str
    id: str


class YtTrackObj(TypedDict):
    videoId: str
    title: str
    artists: list[YtArtistObj]
    album: dict
    duration: str
    duration_seconds: int
    setVideoId: str
    likeStatus: str
    thumbnails: list
    isAvailable: bool
    isExplicit: bool
    videoType: str
    feedbackTokens: dict
