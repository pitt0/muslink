from __future__ import annotations

import json
from typing import TYPE_CHECKING

from clients import sp, ytm
from utils import loop, read

if TYPE_CHECKING:
    from ._types import SpTrackObj, YtTrackObj


def _fetch_tracks(playlist_id: str) -> list[YtTrackObj]:
    return ytm.get_playlist(playlist_id, limit=None)["tracks"]


def _query_track(track: YtTrackObj) -> str:
    return f"track:{track['title']}&{'&'.join(f'artist:{a["name"]}' for a in track['artists'])}"


def _search_spotify(track: YtTrackObj) -> SpTrackObj | None:
    tracks: list[SpTrackObj] = sp.search(q=_query_track(track), limit=1)  # pyright: ignore[reportAssignmentType]
    if len(tracks) == 0:
        return None

    return tracks[0]


def _upload_tracks(all_tracks: list[YtTrackObj], matches: dict[str, str], sp_id: str) -> dict[str, str]:
    # upload new tracks to spotify
    uploads = []
    _ids = set(matches.values())

    for track in all_tracks:
        if track["videoId"] in _ids:
            continue

        found = _search_spotify(track)
        if found is None:
            continue

        matches[found["id"]] = track["videoId"]

        uploads.append(found)

    sp.playlist_add_items(sp_id, uploads)

    return matches


def _update_deletions(tracks_id: set[str], matches: dict[str, str], sp_id: str) -> dict[str, str]:
    removed = []

    for s_id, yt_id in matches.items():
        if yt_id in tracks_id:
            continue
        matches.pop(s_id)
        removed.append(sp.track(s_id))

    sp.playlist_remove_all_occurrences_of_items(sp_id, removed)

    return matches


@loop(1800)
def listen_youtube(playlist_id: str, sp_id: str) -> None:
    matches = read("matches.json")
    all_tracks = _fetch_tracks(playlist_id)

    matches = _upload_tracks(all_tracks, matches, sp_id)
    matches = _update_deletions({t["videoId"] for t in all_tracks}, matches, sp_id)

    with open("matches.json", "w") as f:
        json.dump(matches, f, inline=2)
