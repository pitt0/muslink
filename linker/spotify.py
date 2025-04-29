from __future__ import annotations

import json
from typing import TYPE_CHECKING

from clients import sp, ytm
from utils import loop, read

if TYPE_CHECKING:
    from ._types import SpPlaylistTracks, SpTrackObj


def _fetch_tracks(playlist_id: str) -> list[SpTrackObj]:
    """Retrieve all the tracks inside of a playlist."""
    tracks: list[SpTrackObj] = []
    total = 1  # arbitrary value, any in >0 is good

    while len(tracks) < total:
        playlist: SpPlaylistTracks = sp.playlist_tracks(
            playlist_id,
            offset=len(tracks),
            fields="total,items(track(id,name,artists(name)))",
        )  # pyright: ignore[reportAssignmentType]

        total = playlist["total"]
        tracks += playlist["items"]

    return tracks


def _format_track(track: SpTrackObj) -> str:
    return f"{track['name']} {' '.join(a['name'] for a in track['artists'])}"


def _search_ytm(track: SpTrackObj):
    return ytm.search(query=_format_track(track), filter="songs", limit=1, ignore_spelling=True)[0]["videoId"]


def _upload_tracks(all_tracks: list[SpTrackObj], matches: dict[str, str], playlist_id: str) -> dict[str, str]:
    # upload new tracks to youtube
    uploads = []

    for track in all_tracks:
        if track["id"] in matches:
            continue

        found = _search_ytm(track)
        if found is None:
            continue

        matches[track["id"]] = found["videoId"]

        uploads.append(found)

    ytm.add_playlist_items(playlist_id, uploads)

    return matches


def _update_deletions(tracks_id: set[str], matches: dict[str, str], playlist_id: str) -> dict[str, str]:
    removed = []

    for sp_id, yt_id in matches.items():
        if sp_id in tracks_id:
            continue

        matches.pop(sp_id)
        removed.append(ytm.get_song(yt_id))

    ytm.remove_playlist_items(playlist_id, removed)

    return matches


@loop(1800)
def listen_spotify(playlist_id: str, yt_id: str) -> None:
    matches = read("matches.json")
    all_tracks = _fetch_tracks(playlist_id)

    matches = _upload_tracks(all_tracks, matches, yt_id)
    matches = _update_deletions({t["id"] for t in all_tracks}, matches, yt_id)

    with open("matches.json", "w") as f:
        json.dump(matches, f, inline=2)
