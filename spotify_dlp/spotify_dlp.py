import os, argparse, requests, yt_dlp
from spotify_dlp.spotify_api import SpotifyAPI, SpotifyItem
from spotify_dlp.utils import HandledError, tag_print, Colors, Config, YTDLPLogger


def init_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(prog="spotify-dlp", description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.")
	parser.set_defaults(**Config.read())

	parser.add_argument("query", type=str, nargs=argparse.ZERO_OR_MORE, help="The words to search up or a link to a spotify album, artist, playlist or track.")

	parser.add_argument("-a", "--auth", action="store_true", help="Authenticate using the client credentials flow and save the Client ID and Client Secret to a file.")
	parser.add_argument("-i", "--client-id", type=str, help="The Spotify Client ID.")
	parser.add_argument("-s", "--client-secret", type=str, help="The Spotify Client Secret.")

	parser.add_argument("-f", "--format", type=str, help="The format of the downloaded tracks' names. Set to \"help\" for a list of available fields.")
	parser.add_argument("-r", "--range", type=str, help="The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Multiple ranges can be specified with a comma \",\".")

	parser.add_argument("-o", "--output", type=str, help="The output path of the downloaded tracks.")
	parser.add_argument("-c", "--codec", type=str, choices=["mp3", "aac", "m4a", "opus", "vorbis", "flac", "alac", "wav"], help="The audio codec of the downloaded tracks. Defaults to \"mp3\", and requires \"ffmpeg\" to be installed, otherwise it is unchanged from the one \"yt-dlp\" downloads.")
	parser.add_argument("-m", "--metadata", action="store_true", help="Whether to download metadata (such as covers).")
	parser.add_argument("-b", "--browser", type=str, choices=["brave", "chrome", "chromium", "edge", "firefox", "opera", "safari", "vivaldi", "whale"], help="The name of the browser from which cookies should be extracted.")

	parser.add_argument("-y", "--yes", action="store_true", help="Whether to skip the confirmation prompt.")

	parser.add_argument("-v", "--verbose", action="store_true", help="Whether to display verbose information and full errors.")
	parser.add_argument("--version", action="version", version="%(prog)s 2.6.0")

	return parser.parse_args()

def validate_args(args: argparse.Namespace) -> argparse.Namespace:
	args.query = " ".join(args.query)

	parse_range_str([], args.range)

	try:
		SpotifyItem().format(args.format)
	except KeyError as e:
		raise HandledError(f"Invalid field \"{{{e.args[0]}}}\" in format argument. Use \"--format help\" to see available fields.") from e

	if args.codec and not yt_dlp.utils.check_executable("ffmpeg"):
		raise HandledError("The \"--codec\" argument requires \"ffmpeg\" to be installed. Please install it and try again.")

	if not args.codec and yt_dlp.utils.check_executable("ffmpeg"):
		args.codec = "mp3"

	return args

def parse_range_str(lst: list, range_str: str) -> list:
	indexes = set()

	for range_segment in range_str.split(","):
		try:
			beg_index, part, end_index = range_segment.partition(":")
			if part:
				beg_index = 0        if beg_index == "" else int(beg_index) - 1
				end_index = len(lst) if end_index == "" else int(end_index)
				indexes.update(range(beg_index, end_index))
			else:
				indexes.add(int(beg_index) - 1)
		except ValueError:
			raise HandledError("Invalid range format.")

	return [lst[i] for i in sorted(indexes) if 0 <= i < len(lst)]

def main():
	try:
		# Add color support for Windows terminals
		if os.name == "nt":
			os.system("")

		args = init_args()
		args = validate_args(args)


		### AUTHENTICATION ###
		if args.auth:
			print(
				"To authenticate, please follow these steps:\n"
				"1. Go to https://developer.spotify.com/dashboard/applications\n"
				"2. Press \"Create app\" and fill in details for name and description;\n"
				"3. Set \"Redirect URIs\" to a random URL, such as \"http://127.0.0.1:3000/\";\n"
				"4. Press \"Save\" and paste your Client ID & Client Secret below.\n"
			)

			is_valid_code = lambda code: len(code) == 32 and code.isalnum()

			client_id = input("Client ID: ").strip()

			if not is_valid_code(client_id):
				raise HandledError("Invalid Client ID. Please try again.")

			client_secret = input("Client Secret: ").strip()

			if not is_valid_code(client_secret):
				raise HandledError("Invalid Client Secret. Please try again.")

			Config.write("client_id", client_id)
			Config.write("client_secret", client_secret)
			tag_print(f"Authorization codes saved to {Config.get_config_filepath()}", color=Colors.BOLD)

			return
		elif not args.query:
			raise HandledError("No query was provided. Please provide a query or a link to a Spotify album, artist, playlist or track.")

		if args.client_id and args.client_secret:
			tag_print("Fetching access token...")
			try:
				spotify = SpotifyAPI.from_client_credentials_flow(args.client_id, args.client_secret)
			except Exception as e:
				raise HandledError("Couldn't fetch token. Client ID and/or Client Secret are probably invalid.") from e
		else:
			raise HandledError(
				"Not authenticated.\n"
				"You can authenticate by running `spotify-dlp --auth` and following the instructions.\n"
				"Alternatively, you can provide your Client ID and Client Secret as command line arguments."
			)


		### FETCH TRACKLIST ###

		try:
			try:
				SpotifyAPI.parse_url(args.query)
			except ValueError:
				tag_print("Searching up the query...")
				tracklist = spotify.items_by_search(args.query)
			else:
				tag_print("Fetching the query URL...")
				tracklist = spotify.items_by_url(args.query)
		except Exception as e:
			raise HandledError(e) from e

		if len(tracklist) == 0:
			raise HandledError("No tracks were found.")

		tracklist: list[SpotifyItem] = parse_range_str(tracklist, args.range)

		if len(tracklist) == 0:
			raise HandledError(f"The specified range is out of bounds.")


		### DISPLAY TRACKLIST ###

		print()

		if args.format == "help":
			tag_print("Available fields for the format argument:", color=Colors.BOLD)
			for keys, value in tracklist[0].format_dict.items():
				print("{:>12} {}".format(f"{{{keys}}}:", value))
			return

		CUTOFF_LENGTH = 100
		tag_print(f"The query you requested contained {len(tracklist)} track(s):", color=Colors.BOLD)
		for track in tracklist[:CUTOFF_LENGTH]:
			print(track.format(args.format))
		if len(tracklist) > CUTOFF_LENGTH:
			print(f"... and {len(tracklist) - CUTOFF_LENGTH} more track(s).")

		print()

		if not args.yes:
			choice = tag_print("Are you sure you want to download these tracks? [Y/n]\n", color=Colors.BOLD, prompt=True)

			if "n" in choice.lower():
				return

			if choice:
				print()


		### DOWNLOAD TRACKS ###

		if not os.path.exists(args.output):
			os.makedirs(args.output)

		DEFAULT_YTDLP_OPTIONS = {
			"logger": YTDLPLogger(verbose=args.verbose),
			"format": "bestaudio/best",
			"noplaylist": True,
			"extract_flat": True,
			"cookiesfrombrowser": (args.browser,) if args.browser else None
		} | ({
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": args.codec
				}
			]
		} if args.codec else {})

		for index, track in enumerate(tracklist, start=1):
			try:
				filename = track.safe_format(args.format)
				filepath = os.path.join(args.output, filename)

				if args.metadata:
					coverpath = os.path.join(args.output, f"{track.album}.jpg")
					if not os.path.exists(coverpath):
						try:
							img_data = requests.get(track.cover).content
							open(coverpath, "wb").write(img_data)
						except Exception as e:
							tag_print(f"An error was encountered while trying to download the cover for \"{track.album}\": {e}", color=Colors.WARN)
						else:
							if args.verbose:
								tag_print(f"Successfully downloaded the cover for \"{track.album}\"!")

				if os.path.exists(f"{filepath}.{args.codec}"):
					raise HandledError(f"File \"{filename}\" already exists")

				TRACK_DURATION_DELTA = 5
				SEARCH_TRACKS_COUNT = 10
				SHORT_FORMAT = "{title}"

				ytdlp_options = DEFAULT_YTDLP_OPTIONS | {
					"outtmpl": filepath + ".%(ext)s",
					"match_filter": yt_dlp.utils.match_filter_func(
						f"duration>={track.duration-TRACK_DURATION_DELTA} & duration<={track.duration+TRACK_DURATION_DELTA}"
					),
					"playlistend": SEARCH_TRACKS_COUNT
				}

				def search_entries(url: str) -> str:
					return yt_dlp.YoutubeDL(ytdlp_options).extract_info(url, download=False)["entries"]

				tag_print(f"Searching for track \"{track.format(SHORT_FORMAT)}\"... ({index}/{len(tracklist)})\r", end="")

				entries = search_entries(f"ytsearch{SEARCH_TRACKS_COUNT}:{track.keywords}")

				if len(entries) == 0:
					entries = search_entries(f"https://www.youtube.com/results?search_query={track.quoted_keywords}&sp=CAMSAhAB")

				if len(entries) == 0:
					raise HandledError(f"No results found for track \"{track.format(SHORT_FORMAT)}\".")

				yt_dlp.YoutubeDL(ytdlp_options).download([entries[0]["id"]])
			except Exception as e:
				msg = str(e)
				if "Sign in to confirm your age" in msg:
					msg = "Video is age-restricted and cannot be downloaded"
				tag_print(f"Error: {msg}; Skipping track #{track.index}...", color=Colors.WARN)
			else:
				tag_print(f"Successfully downloaded \"{track.format(SHORT_FORMAT)}\"! ({index}/{len(tracklist)})")

	except KeyboardInterrupt:
		tag_print("Interrupted by user.", color=Colors.FAIL)

	except HandledError as e:
		if args.verbose:
			raise e
		else:
			tag_print(f"Error: {e}", color=Colors.FAIL)

if __name__ == "__main__":
	main()
