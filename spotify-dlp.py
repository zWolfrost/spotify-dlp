import os, sys, argparse
from dotenv import load_dotenv
from SpotifyApi import SpotifyApi



### PARSE ARGUMENTS ###

load_dotenv(os.path.dirname(sys.executable) + "\.env")

parser = argparse.ArgumentParser()

parser.add_argument(
   "query", type=str, nargs=argparse.ONE_OR_MORE,
   help="The words to search up or a link to a spotify album, artist, playlist or track."
)
parser.add_argument(
   "-i", "--client-id", type=str, default=os.getenv("CLIENT_ID"), required=os.getenv("CLIENT_ID") == None,
   help="The Spotify Client ID."
)
parser.add_argument(
   "-s", "--client-secret", type=str, default=os.getenv("CLIENT_SECRET"), required=os.getenv("CLIENT_SECRET") == None,
   help="The Spotify Client Secret."
)
parser.add_argument(
   "-o", "--output", type=str, default=".",
   help="The output path of the downloaded tracks."
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


def track_query_beautify(track):
   return f"{track['name']} - {', '.join([author for author in track['authors']])} ({track['album']})"


print(f"\n[spotify-dlp] The query you requested contained {len(info)} tracks:")
for index, track in enumerate(info, start=1): print(f"{index}. {track_query_beautify(track)}")
print()



### DOWNLOAD TRACKS ###

from yt_dlp import YoutubeDL

def download_queries(queries, ytdlp_opts=None, callback=None):
   with YoutubeDL(ytdlp_opts) as ytdlp:
      for index, query in enumerate(queries):
         ytdlp.extract_info(f"ytsearch:{query}")["entries"][0]
         callback(index)

download_queries(
   [track["query"] for track in info],
   {
      "quiet": True,
      "outtmpl": args["output"] + "/%(title)s.%(ext)s",
      "format": "m4a/bestaudio/best", "postprocessors": [
         {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a"
         }
      ]
   },
   callback = lambda index : print(f"[spotify-dlp] Successfully downloaded \"{track_query_beautify(info[index])}\"! ({index+1}/{len(info)})")
)