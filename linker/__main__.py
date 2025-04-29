import argparse
import asyncio

from spotify import listen_spotify
from youtube import listen_youtube


async def main() -> None:
    parser = argparse.ArgumentParser(description="Link Spotify and YouTube playlists.")
    parser.add_argument("--spotify", help="Spotify Playlist ID", required=True)
    parser.add_argument("--youtube", help="YouTube Playlist ID", required=True)

    args = parser.parse_args()

    listen_spotify(args.spotify, args.youtube)
    listen_youtube(args.youtube, args.spotify)
    await asyncio.Event().wait()


asyncio.run(main())
