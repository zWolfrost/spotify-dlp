import os, sys, argparse, re
from .spotify_api import spotify_api



def get_args() -> dict:
	parser = argparse.ArgumentParser(prog="spotify-dlp", description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.")

	parser.add_argument("query", type=str, nargs=argparse.ONE_OR_MORE, help="The words to search up or a link to a spotify album, artist, playlist or track.")

	client_id = os.getenv("SPOTIFY_DLP_CLIENT_ID")
	client_secret = os.getenv("SPOTIFY_DLP_CLIENT_SECRET")
	parser.add_argument("-i", "--client-id", type=str, default=client_id, required=(client_id == None), help="The Spotify Client ID.")
	parser.add_argument("-s", "--client-secret", type=str, default=client_secret, required=(client_secret == None), help="The Spotify Client Secret.")

	parser.add_argument("-f", "--format", type=str, default="{name} - {authors} ({album})", help="The format of the downloaded tracks' names (available fields: {name}, {authors}, {album}, {index}).")
	parser.add_argument("-t", "--type", type=str, default="track", choices=["album", "artist", "playlist", "track"], help="When searching up a query, the specified type of content.")

	parser.add_argument("-o", "--output", type=str, default=".", help="The output path of the downloaded tracks.")
	parser.add_argument("-c", "--codec", type=str, default="m4a", help="The audio codec of the downloaded tracks.")

	parser.add_argument("-y", "--yes", action="store_true", help="Whether to skip the confirmation prompt.")
	parser.add_argument("-l", "--slice", type=str, default=":", help="The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Either one of those indexes can be omitted.")

	parser.add_argument("-v", "--version", action="version", version="%(prog)s 2.0.0")

	return vars(parser.parse_args())

def parse_tracklist(tracklist: list):
	for index, track in enumerate(tracklist, start=1):
		track["index"] = index
		track["authors"] = ", ".join(track["authors"])
	return tracklist

def format_track(track: dict, format: str, add_index: bool = False) -> str:
	add_index = add_index and not ("{index}" in format)
	string = (str(track["index"]) + ". ") if (add_index) else ""
	string += format.format(**track)
	return string


def main():
	### PARSE ARGUMENTS & GET QUERY TRACKS INFO ###

	ARGS = get_args()

	try:
		spotify = spotify_api(ARGS["client_id"], ARGS["client_secret"])

		query = " ".join(ARGS["query"])

		if len(spotify_api.clean_url(query)) == 1:
			tracklist = spotify.get_search_info(query, ARGS["type"])
		else:
			tracklist = spotify.get_tracks_info(query)

		tracklist = parse_tracklist(tracklist)
	except:
		print("ERROR: Couldn't get token. Client ID and/or Client Secret are probably invalid.")
		sys.exit()



	### SLICE TRACKLIST ###

	try:
		begindex, endindex = ARGS["slice"].split(":")
	except:
		print("ERROR: Slice argument must include one colon \":\".")
		sys.exit()

	try:
		begindex = 0    if (begindex == "" or begindex == "0") else int(begindex)-1
		endindex = None if (endindex == "" or endindex == "0") else int(endindex)

		tracklist = tracklist[begindex:endindex]
	except:
		print("ERROR: Invalid slice argument.")
		sys.exit()



	### DISPLAY TRACKS & ASK CONFIRMATION ###

	print()

	print(f"[spotify-dlp] The query you requested contained {len(tracklist)} track(s):")
	for track in tracklist:
		print(format_track(track, ARGS["format"], add_index=True))

	if (not ARGS["yes"]):
		CHOICE = input("\nAre you sure you want to download these tracks? (Y/n)\n").lower()

		CONFIRMED = ["y", "yes"]

		if (CHOICE not in CONFIRMED):
			sys.exit()

	print()



	### DOWNLOAD TRACKS ###

	from yt_dlp import YoutubeDL
	from yt_dlp.postprocessor import FFmpegPostProcessor
	try:
		FFmpegPostProcessor._ffmpeg_location.set(sys._MEIPASS)
	except:
		pass


	def download_query(query, ytdlp_opts):
		with YoutubeDL(ytdlp_opts) as ytdlp:
			ytdlp.extract_info(f"ytsearch:{query}")["entries"][0]

	DEFAULT_YTDL_OPTS = {
		"quiet": True,
		"format": "m4a/bestaudio/best",
		"postprocessors": [
			{
				"key": "FFmpegExtractAudio",
				"preferredcodec": ARGS["codec"]
			}
		],
		"extractor_args": {
			"youtube": {
				"player_client": ["ios", "web"]
			}
		}
	}

	for index, track in enumerate(tracklist, start=1):
		filename = re.sub(r'[<>:"/\\|?*]', "_", format_track(track, ARGS["format"]))
		download_query(
			track["query"],
			DEFAULT_YTDL_OPTS |
			{
				"outtmpl": f"{ARGS['output']}/{filename}.%(ext)s",
			}
		)
		print(f"[spotify-dlp] Successfully downloaded \"{format_track(track, ARGS['format'])}\"! ({index}/{len(tracklist)})")
