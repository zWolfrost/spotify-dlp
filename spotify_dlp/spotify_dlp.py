import os, argparse, requests, yt_dlp
from spotify_dlp.spotify_api import SpotifyAPI, Item
from spotify_dlp.utils import HandledError, tag_print, Colors, Config


def init_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(prog="spotify-dlp", description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.")
	parser.set_defaults(**Config.read())

	parser.add_argument("query", type=str, nargs=argparse.ZERO_OR_MORE, help="The words to search up or a link to a spotify album, artist, playlist or track.")

	parser.add_argument("-a", "--auth", action="store_true", help="Authenticate using the client credentials flow and save the Client ID and Client Secret to a file.")
	parser.add_argument("-i", "--client-id", type=str, help="The Spotify Client ID.")
	parser.add_argument("-s", "--client-secret", type=str, help="The Spotify Client Secret.")

	parser.add_argument("-f", "--format", type=str, help="The format of the downloaded tracks' names. Set to \"help\" for a list of available fields.")
	parser.add_argument("-t", "--type", type=str, choices=["album", "artist", "playlist", "track"], help="When searching up a query, the specified type of content.")
	parser.add_argument("-l", "--slice", type=str, help="The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Either one of those indexes can be omitted.")

	parser.add_argument("-o", "--output", type=str, help="The output path of the downloaded tracks.")
	parser.add_argument("-c", "--codec", type=str, choices=["m4a", "mp3", "flac", "wav", "aac", "ogg", "opus"], help="The audio codec of the downloaded tracks. By default, it is unchanged from the one \"yt-dlp\" downloads. Requires \"ffmpeg\" to be installed.")
	parser.add_argument("-m", "--metadata", action="store_true", help="Whether to download metadata (such as covers).")

	parser.add_argument("-y", "--yes", action="store_true", help="Whether to skip the confirmation prompt.")

	parser.add_argument("-v", "--verbose", action="store_true", help="Whether to display verbose information and full errors.")
	parser.add_argument("--version", action="version", version="%(prog)s 2.4.0")

	return parser.parse_args()

def parse_args(args: argparse.Namespace) -> argparse.Namespace:
	args.query = " ".join(args.query)

	try:
		begindex, endindex = args.slice.split(":")
	except ValueError:
		begindex, endindex = args.slice, args.slice

	try:
		begindex = 0    if (begindex == "" or begindex == "0") else int(begindex)-1
		endindex = None if (endindex == "" or endindex == "0") else int(endindex)

		args.slice = (begindex, endindex)
	except ValueError as e:
		raise HandledError("Invalid slice argument.") from e

	try:
		Item().format_with_index(args.format)
	except KeyError as e:
		raise HandledError(f"Invalid field \"{{{e.args[0]}}}\" in format argument. Use \"--format help\" to see available fields.") from e

	return args


def main():
	try:
		# Add color support for Windows terminals
		if os.name == "nt":
			os.system("")

		args = init_args()
		args = parse_args(args)


		### AUTHENTICATION ###
		if args.auth:
			print(
				"To authenticate, please follow these steps:\n"
				"1. Go to https://developer.spotify.com/dashboard/applications\n"
				"2. Press \"Create app\" and fill in details for name and description.\n"
				"3. Set \"Redirect URIs\" to a random URL, such as \"http://127.0.0.1:3000/\".\n"
				"4. Press \"Save\" and paste your Client ID and Client Secret below.\n"
			)
			client_id = input("Client ID: ").strip()
			client_secret = input("Client Secret: ").strip()

			if len(client_id) != 32 or not client_id.isalnum():
				raise HandledError("Invalid Client ID. Please try again.")

			if len(client_secret) != 32 or not client_secret.isalnum():
				raise HandledError("Invalid Client Secret. Please try again.")

			Config.write("client_id", client_id)
			Config.write("client_secret", client_secret)
			tag_print(f"Tokens saved to ~/.config/spotify-dlp/config.json", color=Colors.BOLD)

			return
		elif not args.query:
			raise HandledError("No query was provided. Please provide a query or a link to a Spotify album, artist, playlist or track.")

		if args.client_id and args.client_secret:
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
				tracklist = spotify.items_by_search(args.query, args.type)
			else:
				tag_print("Fetching the query URL...")
				tracklist = spotify.items_by_url(args.query)
		except Exception as e:
			raise HandledError(e) from e

		if len(tracklist) == 0:
			raise HandledError("No tracks were found.")

		tracklist = tracklist[args.slice[0]:args.slice[1]]

		if len(tracklist) == 0:
			raise HandledError(f"The specified slice is out of range.")


		### DISPLAY TRACKLIST ###

		if args.format == "help":
			tag_print("Available fields for the format argument:", color=Colors.BOLD)
			for keys, value in tracklist[0].get_format_dict().items():
				print("{:>12} {}".format(f"{{{keys}}}:", value))
			return

		print()
		tag_print(f"The query you requested contained {len(tracklist)} track(s):", color=Colors.BOLD)
		for track in tracklist:
			print(track.format_with_index(args.format))

		if not args.yes:
			print()
			choice = tag_print("Are you sure you want to download these tracks? [Y/n]\n", color=Colors.BOLD, prompt=True)

			if "n" in choice.lower():
				return

			if choice:
				print()
		else:
			print()


		### DOWNLOAD TRACKS ###

		if not os.path.exists(args.output):
			os.makedirs(args.output)

		DEFAULT_YTDLP_OPTIONS = {
			"quiet": not args.verbose,
			"no_warnings": not args.verbose,
			"format": "bestaudio",
			"noplaylist": True,
			"extract_flat": True,
			"extractor_args": { "youtube": { "player_client": ["tv", "web"] } },
		} | ({
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": args.codec
				}
			]
		} if args.codec else {})

		for index, track in enumerate(tracklist, start=1):
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
				tag_print(f"File \"{filename}\" already exists; Skipping track #{track.index}...", color=Colors.WARN)
				continue

			TRACK_DURATION_DELTA = 5
			SEARCH_TRACKS_COUNT = 10

			ytdlp_options = DEFAULT_YTDLP_OPTIONS | {
				"outtmpl": filepath + ".%(ext)s",
				"match_filter": yt_dlp.utils.match_filter_func(
					f"duration>={track.duration-TRACK_DURATION_DELTA} & duration<={track.duration+TRACK_DURATION_DELTA}"
				),
				"playlistend": SEARCH_TRACKS_COUNT
			}

			def search_entries(url: str) -> str:
				return yt_dlp.YoutubeDL(ytdlp_options).extract_info(url, download=False)["entries"]

			tag_print(f"Searching for track \"{track.format(args.format)}\"...\r", end="")

			try:
				entries = search_entries(f"https://www.youtube.com/results?search_query={track.quoted_keywords}&sp=CAMSAhAB")

				if len(entries) == 0:
					entries = search_entries(f"ytsearch{SEARCH_TRACKS_COUNT}:{track.keywords}")

				if len(entries) == 0:
					raise HandledError(f"No results found for track \"{track.format(args.format)}\".")

				yt_dlp.YoutubeDL(ytdlp_options).download([entries[0]["id"]])
			except Exception as e:
				tag_print(f"Error: {e}; Skipping track #{track.index}...", color=Colors.WARN)
			else:
				tag_print(f"Successfully downloaded \"{track.format(args.format)}\"! ({index}/{len(tracklist)})")

	except KeyboardInterrupt:
		tag_print("Interrupted by user.", color=Colors.FAIL)

	except HandledError as e:
		if args.verbose:
			raise e
		else:
			tag_print(f"Error: {e}", color=Colors.FAIL)

if __name__ == "__main__":
	main()
