from dotenv import load_dotenv
from spotipy import Spotify, SpotifyOAuth
from ytmusicapi import YTMusic

load_dotenv()
sp = Spotify(auth_manager=SpotifyOAuth())

ytm = YTMusic()
