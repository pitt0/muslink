import asyncio
import json
import sys

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
        try:
            artists = ", ".join(artist["name"] for artist in track["artists"])
        except KeyError:
            with open("data/songs/spotify1.json", "w") as f:
                json.dump(track, f, indent=4)
            continue
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
        sp_tracks = get_spotify_playlist_songs(sp_p_id)
        yt_tracks = get_ytm_playlist_songs(yt_p_id)

        if len(sp_tracks) == len(yt_tracks):
            # there are the same number of tracks, so we can safely assume (or partially so)
            # that there has been no change since the last minute
            continue

        if len(sp_tracks) > len(yt_tracks):
            # track goes from last element of sp_tracks to the first element that is not also contained in yt_tracks
            for track in sp_tracks[-1 : len(yt_tracks) - 1 : -1]:
                track = ytm.search(query=track, filter="songs", limit=1, ignore_spelling=True)[0]
                ytm.add_playlist_items(yt_p_id, [track["videoId"]])

        else:
            # track goes from last element of yt_tracks to the first element that is not also contained in sp_tracks
            for track in yt_tracks[-1 : len(sp_tracks) - 1 : -1]:
                track = sp.search(track, limit=1)
                assert track is not None  # mi dava fastidio che pyright mi dava errore
                sp.playlist_add_items(sp_p_id, items=[track["track"]["id"]])

        # sleep for a minute then repeat the process indefinitely
        await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # interrupting with Ctrl-C causes the program to exit immediately without crashing
        exit(0)
