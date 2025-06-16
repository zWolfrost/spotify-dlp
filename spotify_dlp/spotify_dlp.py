import os, argparse, re, urllib.parse, requests, yt_dlp
from spotify_dlp.spotify_api import SpotifyAPI, Item
from spotify_dlp.utils import HandledError, tag_print, Colors, TokenFile


def init_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(prog="spotify-dlp", description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.")

	parser.add_argument("query", type=str, nargs=argparse.ZERO_OR_MORE, help="The words to search up or a link to a spotify album, artist, playlist or track. If \"saved\", download the user's saved tracks (requires browser authentication).")

	parser.add_argument("-a", "--auth", action="store_true", help="Authenticate using the PKCE flow and exit.")
	parser.add_argument("-i", "--client-id", type=str, help="The Spotify Client ID.")
	parser.add_argument("-s", "--client-secret", type=str, help="The Spotify Client Secret.")

	parser.add_argument("-f", "--format", type=str, default="{title} - {authors} ({album})", help="The format of the downloaded tracks' names. Set to \"help\" for a list of available fields.")
	parser.add_argument("-t", "--type", type=str, default="track", choices=["album", "artist", "playlist", "track"], help="When searching up a query, the specified type of content.")
	parser.add_argument("-l", "--slice", type=str, default=":", help="The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Either one of those indexes can be omitted.")

	parser.add_argument("-o", "--output", type=str, default=".", help="The output path of the downloaded tracks.")
	parser.add_argument("-c", "--codec", type=str, default="", choices=["m4a", "mp3", "flac", "wav", "aac", "ogg", "opus"], help="The audio codec of the downloaded tracks. By default, it is unchanged from the one \"yt-dlp\" downloads. Requires \"ffmpeg\" to be installed.")
	parser.add_argument("-m", "--metadata", action="store_true", help="Whether to download metadata (such as covers).")

	parser.add_argument("-y", "--yes", action="store_true", help="Whether to skip the confirmation prompt.")

	parser.add_argument("-v", "--verbose", action="store_true", help="Whether to display verbose information and full errors.")
	parser.add_argument("--version", action="version", version="%(prog)s 2.3.1")

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

	if not args.auth:
		if not args.query:
			raise HandledError("No query was provided. Please provide a query or a link to a Spotify album, artist, playlist or track.")

		if not ((args.client_id and args.client_secret) or (TokenFile.read_token("ACCESS_TOKEN") and TokenFile.read_token("REFRESH_TOKEN"))):
			raise HandledError(
				"Not authenticated.\n"
				"You can authenticate using the browser by running \"spotify-dlp --auth\".\n"
				"Alternatively, you can provide your Client ID and Client Secret, "
				"both trough command line arguments or environment variables (see README)."
			)

	return args

def write_all_tokens(spotify: SpotifyAPI):
	TokenFile.write_token("ACCESS_TOKEN", spotify.access_token)
	TokenFile.write_token("REFRESH_TOKEN", spotify.refresh_token)


def main():
	try:
		# Add color support for Windows terminals
		if os.name == "nt":
			os.system("")

		args = init_args()
		args = parse_args(args)


		### AUTHENTICATION ###

		if args.auth:
			try:
				spotify = SpotifyAPI.from_pkce_flow()
			except Exception as e:
				raise HandledError(f"An error occurred while trying to authenticate: {e}") from e
			write_all_tokens(spotify)

			tag_print(f"Tokens saved to ~/.config/spotify-dlp/", color=Colors.BOLD)
			return

		if args.client_id and args.client_secret:
			try:
				spotify = SpotifyAPI.from_client_credentials_flow(args.client_id, args.client_secret)
			except Exception as e:
				raise HandledError("Couldn't fetch token. Client ID and/or Client Secret are probably invalid.") from e
		else:
			tag_print("Authenticating using refreshed saved token...", color=Colors.BOLD)
			spotify = SpotifyAPI(access_token=TokenFile.read_token("ACCESS_TOKEN"), refresh_token=TokenFile.read_token("REFRESH_TOKEN"))
			spotify.refresh_pkce_token()
			write_all_tokens(spotify)


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

		DEFAULT_YTDLP_OPTS = {
			"quiet": not args.verbose,
			"no_warnings": not args.verbose,
			"format": "bestaudio",
			"noplaylist": True,
		} | ({
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": args.codec
				}
			]
		} if args.codec else {})

		for index, track in enumerate(tracklist, start=1):
			filename = re.sub(r"[/<>:\"\\|?*]", "_", track.format(args.format).strip())
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

			options = DEFAULT_YTDLP_OPTS | {
				"outtmpl": filepath + ".%(ext)s",
				"match_filter": yt_dlp.utils.match_filter_func(f"duration>{track.duration-3} & duration<{track.duration+3}")
			}

			try:
				tag_print(f"Searching for track \"{track.format(args.format)}\"...\r", end="")

				search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(track.keywords)}&sp=CAMSAhAB"
				entries = yt_dlp.YoutubeDL(options | {"playlistend": 5}).extract_info(search_url, download=False)["entries"]

				if len(entries) == 0:
					entries = yt_dlp.YoutubeDL(options).extract_info(f"ytsearch5:{track.keywords}", download=False)["entries"]
					entries = sorted(entries, key=lambda s: s.get("view_count", 0), reverse=True)

				if len(entries) == 0:
					raise HandledError(f"No results found for track \"{track.format(args.format)}\".")

				yt_dlp.YoutubeDL(options).download([entries[0]["id"]])
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
