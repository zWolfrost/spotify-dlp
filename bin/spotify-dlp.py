import os, sys, argparse
from dotenv import dotenv_values
from SpotifyApi import SpotifyApi



### PARSE ARGUMENTS ###

spotify_client = dotenv_values() or dotenv_values(os.path.dirname(sys.executable) + "/.env")
parser = argparse.ArgumentParser()

parser.add_argument(
   "query", type=str, nargs=argparse.ONE_OR_MORE,
   help="The words to search up or a link to a spotify album, artist, playlist or track."
)
parser.add_argument(
   "-i", "--client-id", type=str, default=spotify_client["CLIENT_ID"], required=(spotify_client["CLIENT_ID"] == None),
   help="The Spotify Client ID."
)
parser.add_argument(
   "-s", "--client-secret", type=str, default=spotify_client["CLIENT_SECRET"], required=(spotify_client["CLIENT_SECRET"] == None),
   help="The Spotify Client Secret."
)
parser.add_argument(
   "-o", "--output", type=str, default=".",
   help="The output path of the downloaded tracks."
)
parser.add_argument(
   "-a", "--audio-codec", type=str, default="m4a",
   help="The audio codec of the downloaded tracks."
)
parser.add_argument(
   "-t", "--search-type", type=str, default="tracks", choices=["albums", "artists", "playlists", "tracks"],
   help="When searching up a query, the specified type of content."
)

args = vars(parser.parse_args())



### GET & PRINT TRACKS INFO ###

try:
   spotify_api = SpotifyApi(args["client_id"], args["client_secret"])
   info = spotify_api.get_tracks_info(" ".join(args["query"]))
except:
   raise Exception("Client ID and/or Client Secret were not specified or invalid.")


def track_beautify(track):
   return f"{track['name']} - {', '.join([author for author in track['authors']])} ({track['album']})"


print(f"\n[spotify-dlp] The query you requested contained {len(info)} tracks:")
for index, track in enumerate(info, start=1): print(f"{index}. {track_beautify(track)}")
print()



### DOWNLOAD TRACKS ###

from yt_dlp import YoutubeDL
from yt_dlp.postprocessor import FFmpegPostProcessor
try:
   FFmpegPostProcessor._ffmpeg_location.set(sys._MEIPASS)
except:
   pass


def download_query(query, ytdlp_opts=None):
   with YoutubeDL(ytdlp_opts) as ytdlp:
      ytdlp.extract_info(f"ytsearch:{query}")["entries"][0]


for index, track in enumerate(info, start=1):
   download_query(
      track["query"],
      {
         "quiet": True,
         "outtmpl": track_beautify(track) + ".%(ext)s",
         "format": "m4a/bestaudio/best",
         "postprocessors": [
            {
               "key": "FFmpegExtractAudio",
               "preferredcodec": args["audio_codec"]
            }
         ]
      }
   )
   print(f"[spotify-dlp] Successfully downloaded \"{track_beautify(track)}\"! ({index}/{len(info)})")