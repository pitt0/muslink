import asyncio
import json
import sys
from typing import Generator

from dotenv import load_dotenv
from spotipy import Spotify, SpotifyOAuth
from ytmusicapi import YTMusic

load_dotenv()
sp = Spotify(auth_manager=SpotifyOAuth())

ytm = YTMusic("oauth.json")


def get_spotify_playlist_songs(playlist_id: str) -> list[str]:
    """Get the songs inside the chosen spotify playlist"""
    playlist = sp.playlist(playlist_id)
    assert playlist is not None  # mi dava fastidio che pyright mi dava errore
    tracks = playlist["tracks"]["items"]

    out = []
    for track in tracks:
        track = track["track"]
        artists = ", ".join(artist["name"] for artist in track["artists"])
        # since python 3.12 you can include double quotes inside f-strings
        # if you are to use an older version of python just use
        # f"{track['name']} {artists}"
        out.append(f"{track["name"]} {artists}")
    return out


def get_ytm_playlist_songs(playlist_id: str) -> list[str]:
    """Get the songs inside the chosen youtube music playlist"""
    playlist = ytm.get_playlist(playlist_id)
    tracks = playlist["tracks"]

    out = []
    for track in tracks:
        artists = ", ".join(artist["name"] for artist in track["artists"])
        out.append(f"{track["title"]} {artists}")
    return out


def get_del_songs(latest: list[str], cache: list[str]) -> Generator[str, None, None]:
    for song in cache:
        if song not in latest:
            yield song


def get_new_songs(latest: list[str], cache: list[str]) -> Generator[str, None, None]:
    for song in latest:
        if song not in cache:
            yield song


def get_spotify_new(playlist_id: str) -> Generator[str, None, None]:
    sp_tracks = get_spotify_playlist_songs(playlist_id)
    with open("cache/spotify.json", "r") as f:
        sp_cache = json.load(f)

    return get_new_songs(sp_tracks, sp_cache)


def get_spotify_del(playlist_id: str) -> Generator[str, None, None]:
    sp_tracks = get_spotify_playlist_songs(playlist_id)
    with open("cache/spotify.json", "r") as f:
        sp_cache = json.load(f)

    return get_del_songs(sp_tracks, sp_cache)


def get_youtube_new(playlist_id: str) -> Generator[str, None, None]:
    yt_tracks = get_ytm_playlist_songs(playlist_id)
    with open("cache/youtube.json", "r") as f:
        yt_cache = json.load(f)

    return get_new_songs(yt_tracks, yt_cache)


def get_youtube_del(playlist_id: str) -> Generator[str, None, None]:
    yt_tracks = get_ytm_playlist_songs(playlist_id)
    with open("cache/youtube.json", "r") as f:
        yt_cache = json.load(f)

    return get_del_songs(yt_tracks, yt_cache)


def remove_from_cache(cache: str, song: str) -> None:
    with open(f"cache/{cache}.json", "r") as f:
        old = json.load(f)
    old.remove(song)
    with open(f"cache/{cache}.json", "w") as f:
        old = json.dump(old, f)


async def main() -> None:

    sp_p_id = None
    yt_p_id = None
    # get playlists_ids from args when running the program as
    # `python main.py spotify_playlist_id=xxxxx youtube_playlist_id=yyyyyyy`
    for p_id in sys.argv:
        if p_id.startswith("spotify_playlist_id"):
            sp_p_id = p_id.split("=")[1]
        elif p_id.startswith("youtube_playlist_id"):
            yt_p_id = p_id.split("=")[1]

    if not sp_p_id or not yt_p_id:
        print("Too few argumets")
        return

    while True:
        for song in get_spotify_new(sp_p_id):
            track = ytm.search(query=song, filter="songs", limit=1, ignore_spelling=True)[0]
            ytm.add_playlist_items(yt_p_id, [track["videoId"]])

        for song in get_spotify_del(sp_p_id):
            track = ytm.search(query=song, filter="songs", limit=1, ignore_spelling=True)[0]
            ytm.remove_playlist_items(yt_p_id, [track["videoId"]])
            remove_from_cache("spotify", song)

        for song in get_youtube_new(yt_p_id):
            track = sp.search(song, limit=1)
            assert track is not None  # mi dava fastidio che pyright mi dava errore
            sp.playlist_add_items(sp_p_id, items=[track["track"]["id"]])

        for song in get_youtube_del(yt_p_id):
            track = sp.search(song, limit=1)
            assert track is not None  # mi dava fastidio che pyright mi dava errore
            sp.playlist_remove_all_occurrences_of_items(sp_p_id, items=[track["track"]["id"]])
            remove_from_cache("youtube", song)

        # sleep for a minute then repeat the process indefinitely
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # interrupting with Ctrl-C causes the program to exit immediately without crashing
        exit(0)
