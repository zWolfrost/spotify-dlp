import os, argparse, re
from yt_dlp import YoutubeDL
from spotify_dlp.spotify_api import SpotifyAPI


def parse_args() -> dict:
	parser = argparse.ArgumentParser(prog="spotify-dlp", description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.")

	parser.add_argument("query", type=str, nargs=argparse.ONE_OR_MORE, help="The words to search up or a link to a spotify album, artist, playlist or track.")

	client_id = os.getenv("SPOTIFY_DLP_CLIENT_ID")
	client_secret = os.getenv("SPOTIFY_DLP_CLIENT_SECRET")
	parser.add_argument("-i", "--client-id", type=str, default=client_id, required=(client_id == None), help="The Spotify Client ID.")
	parser.add_argument("-s", "--client-secret", type=str, default=client_secret, required=(client_secret == None), help="The Spotify Client Secret.")

	parser.add_argument("-f", "--format", type=str, default="{title} - {authors} ({album})", help="The format of the downloaded tracks' names. Set to \"help\" for a list of available fields.")
	parser.add_argument("-t", "--type", type=str, default="track", choices=["album", "artist", "playlist", "track"], help="When searching up a query, the specified type of content.")

	parser.add_argument("-o", "--output", type=str, default=".", help="The output path of the downloaded tracks.")
	parser.add_argument("-c", "--codec", type=str, default="m4a", help="The audio codec of the downloaded tracks.")
	parser.add_argument("-l", "--slice", type=str, default=":", help="The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Either one of those indexes can be omitted.")
	parser.add_argument("-y", "--yes", action="store_true", help="Whether to skip the confirmation prompt.")

	parser.add_argument("-v", "--verbose", action="store_true", help="Whether to display verbose information.")
	parser.add_argument("--version", action="version", version="%(prog)s 2.1.1")

	args = parser.parse_args()

	args.query = " ".join(args.query)

	try:
		begindex, endindex = args.slice.split(":")
	except ValueError:
		begindex, endindex = args.slice, args.slice

	try:
		begindex = 0    if (begindex == "" or begindex == "0") else int(begindex)-1
		endindex = None if (endindex == "" or endindex == "0") else int(endindex)

		args.slice = (begindex, endindex)
	except ValueError:
		raise Exception("Invalid slice argument.")

	return args

def tag_print(message: str):
	print(f"[spotify-dlp] {message}")


def main():
	try:
		### PARSE ARGUMENTS & GET QUERY TRACKS INFO ###

		ARGS = parse_args()

		try:
			spotify = SpotifyAPI(ARGS.client_id, ARGS.client_secret)
		except Exception as e:
			raise Exception("Couldn't fetch token. Client ID and/or Client Secret are probably invalid.")

		if SpotifyAPI.parse_url(ARGS.query):
			tracklist = spotify.items_by_url(ARGS.query)
		else:
			tracklist = spotify.items_by_search(ARGS.query, ARGS.type)


		### SLICE TRACKLIST ###

		try:
			tracklist = tracklist[ARGS.slice[0]:ARGS.slice[1]]
		except ValueError:
			raise Exception("Invalid slice argument.")


		### DISPLAY TRACKS & ASK CONFIRMATION ###

		if len(tracklist) == 0:
			raise Exception("No tracks were found.")

		if ARGS.format == "help":
			tag_print("Available fields for the format argument:")
			for keys, value in tracklist[0].get_format_dict().items():
				print("{:>10} {}".format(f"{{{keys}}}:", value))
			return

		tag_print(f"The query you requested contained {len(tracklist)} track(s):")
		for track in tracklist:
			try:
				print(track.format_with_index(ARGS.format))
			except KeyError as e:
				raise Exception(f"Invalid field \"{e.args[0]}\" in format argument. Use \"--format help\" to see available fields.")

		if not ARGS.yes:
			choice = input("\nAre you sure you want to download these tracks? (Y/n)\n")

			if choice.lower() not in ["y", "yes"]:
				return

		print()


		### DOWNLOAD TRACKS ###

		DEFAULT_YTDLP_OPTS = {
			"quiet": not ARGS.verbose,
			"no_warnings": not ARGS.verbose,
			"format": "m4a/bestaudio/best",
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": ARGS.codec
				}
			],
			"noplaylist": True,
			"playlist_items": "1"
		}

		for track in tracklist:
			filename = re.sub(r'[<>:"/\\|?*]', "_", track.format(ARGS.format))

			if ARGS.verbose:
				tag_print(f"Fetching first track found in search \"{track.keywords}\"...")

			options = DEFAULT_YTDLP_OPTS | {
				"outtmpl": os.path.join(ARGS.output, filename + ".%(ext)s")
			}

			YoutubeDL(options).extract_info(f"https://music.youtube.com/search?q={track.keywords}#songs")

			tag_print(f"Successfully downloaded \"{track.format(ARGS.format)}\"! ({track.index}/{len(tracklist)})")

	except KeyboardInterrupt:
		print()
		tag_print("Interrupted by user.")

	except Exception as e:
		tag_print(f"Error: {e}")

if __name__ == "__main__":
	main()