import os, argparse, re, requests
from yt_dlp import YoutubeDL
from spotify_dlp.spotify_api import SpotifyAPI, Item


class HandledError(Exception):
   pass

class Colors():
	ENDC = "\033[0m"
	FAIL = "\033[91m"
	WARN = "\033[93m"
	BOLD = "\033[1m"

def tag_print(string: str, color: str = None, prompt: bool = False):
	TAG = "[spotify-dlp] "
	string = TAG + string

	if color:
		string = color + string + Colors.ENDC

	return input(string) if prompt else print(string)

class TokenFile():
	token_filepath: str = os.path.expanduser("~/.config/spotify-dlp/TOKEN")

	@staticmethod
	def read_token() -> str:
		if not os.path.exists(TokenFile.token_filepath):
			return None

		with open(TokenFile.token_filepath, "r") as f:
			return f.read().strip()

	@staticmethod
	def write_token(token: str):
		if not os.path.exists(os.path.dirname(TokenFile.token_filepath)):
			os.makedirs(os.path.dirname(TokenFile.token_filepath))

		with open(TokenFile.token_filepath, "w") as f:
			f.write(token)

		tag_print("Token saved to ~/.config/spotify-dlp/TOKEN", color=Colors.BOLD)

def parse_args() -> dict:
	parser = argparse.ArgumentParser(prog="spotify-dlp", description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.")

	parser.add_argument("query", type=str, nargs=argparse.ZERO_OR_MORE, help="The words to search up or a link to a spotify album, artist, playlist or track. If \"saved\", download the user's saved tracks (requires browser authentication).")

	# ENV IS DEPRECATED!
	parser.add_argument("-a", "--auth", action="store_true", help="Whether to authenticate using the PKCE flow and exit.")
	parser.add_argument("-i", "--client-id", type=str, default=os.getenv("SPOTIFY_DLP_CLIENT_ID"), help="The Spotify Client ID.")
	parser.add_argument("-s", "--client-secret", type=str, default=os.getenv("SPOTIFY_DLP_CLIENT_SECRET"), help="The Spotify Client Secret.")

	parser.add_argument("-f", "--format", type=str, default="{title} - {authors} ({album})", help="The format of the downloaded tracks' names. Set to \"help\" for a list of available fields.")
	parser.add_argument("-t", "--type", type=str, default="track", choices=["album", "artist", "playlist", "track"], help="When searching up a query, the specified type of content.")
	parser.add_argument("-l", "--slice", type=str, default=":", help="The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Either one of those indexes can be omitted.")

	parser.add_argument("-o", "--output", type=str, default=".", help="The output path of the downloaded tracks.")
	parser.add_argument("-c", "--codec", type=str, default="m4a", choices=["m4a", "mp3", "flac", "wav", "aac", "ogg", "opus"], help="The audio codec of the downloaded tracks.")
	parser.add_argument("-m", "--metadata", action="store_true", help="Whether to download metadata (such as covers).")

	parser.add_argument("-y", "--yes", action="store_true", help="Whether to skip the confirmation prompt.")

	parser.add_argument("-v", "--verbose", action="store_true", help="Whether to display verbose information.")
	parser.add_argument("--version", action="version", version="%(prog)s 2.2.0")

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
		raise HandledError("Invalid slice argument.")

	try:
		Item().format_with_index(args.format)
	except KeyError as e:
		raise HandledError(f"Invalid field \"{{{e.args[0]}}}\" in format argument. Use \"--format help\" to see available fields.")

	if not args.auth:
		if not args.query:
			raise HandledError("No query was provided. Please provide a query or a link to a Spotify album, artist, playlist or track.")

		if (not args.client_id or not args.client_secret) and not TokenFile.read_token():
			raise HandledError(
				"Not authenticated.\n"
				"You can authenticate using the browser by running \"spotify-dlp --auth\".\n"
				"Alternatively, you can provide your Client ID and Client Secret, both trough command line arguments or environment variables (see README)."
			)

	return args


def main():
	try:
		### FETCH TRACKLIST ###

		ARGS = parse_args()

		if ARGS.auth:
			tag_print(f"Please open the following URL in your browser to authenticate:", color=Colors.BOLD)
			try:
				token = SpotifyAPI.from_pkce_flow().token
			except Exception as e:
				raise HandledError(f"An error occurred while trying to authenticate: {e}")
			TokenFile.write_token(token)
			return

		if token := TokenFile.read_token():
			spotify = SpotifyAPI(token=token)
			tag_print("Authenticated using saved token.", color=Colors.BOLD)
		else:
			try:
				spotify = SpotifyAPI.from_client_credentials_flow(ARGS.client_id, ARGS.client_secret)
			except Exception as e:
				raise HandledError("Couldn't fetch token. Client ID and/or Client Secret are probably invalid.")

		try:
			SpotifyAPI.parse_url(ARGS.query)
		except ValueError:
			tag_print("Searching up the query...")
			tracklist = spotify.items_by_search(ARGS.query, ARGS.type)
		else:
			tag_print("Fetching the query URL...")
			try:
				tracklist = spotify.items_by_url(ARGS.query)
			except Exception as e:
				raise HandledError(e)

		if len(tracklist) == 0:
			raise HandledError("No tracks were found.")

		tracklist = tracklist[ARGS.slice[0]:ARGS.slice[1]]

		if len(tracklist) == 0:
			raise HandledError(f"The specified slice is out of range.")


		### DISPLAY TRACKLIST ###

		if ARGS.format == "help":
			tag_print("Available fields for the format argument:", color=Colors.BOLD)
			for keys, value in tracklist[0].get_format_dict().items():
				print("{:>10} {}".format(f"{{{keys}}}:", value))
			return

		tag_print(f"The query you requested contained {len(tracklist)} track(s):", color=Colors.BOLD)
		for track in tracklist:
			print(track.format_with_index(ARGS.format))

		if not ARGS.yes:
			print()
			choice = tag_print("Are you sure you want to download these tracks? [y/n]\n", color=Colors.BOLD, prompt=True)

			if "y" not in choice.lower():
				return

		print()


		### DOWNLOAD TRACKS ###

		if not os.path.exists(ARGS.output):
			os.makedirs(ARGS.output)

		DEFAULT_YTDLP_OPTS = {
			"quiet": not ARGS.verbose,
			"no_warnings": not ARGS.verbose,
			"format": "bestaudio",
			"postprocessors": [
				{
					"key": "FFmpegExtractAudio",
					"preferredcodec": ARGS.codec
				}
			],
			"noplaylist": True
		}

		for index, track in enumerate(tracklist, start=1):
			filename = re.sub(r"[/<>:\"\\|?*]", "_", track.format(ARGS.format).strip())
			filepath = os.path.join(ARGS.output, filename)

			if ARGS.metadata:
				coverpath = os.path.join(ARGS.output, f"{track.album}.jpg")
				if not os.path.exists(coverpath):
					try:
						img_data = requests.get(track.cover).content
						open(coverpath, "wb").write(img_data)
					except Exception as e:
						tag_print(f"An error was encountered while trying to download the cover for \"{track.album}\": {e}", color=Colors.WARN)
					else:
						if ARGS.verbose:
							tag_print(f"Successfully downloaded the cover for \"{track.album}\"!")

			if os.path.exists(f"{filepath}.m4a") or os.path.exists(f"{filepath}.{ARGS.codec}"):
				tag_print(f"File \"{filename}\" already exists; Skipping track #{track.index}...", color=Colors.WARN)
				continue

			options = DEFAULT_YTDLP_OPTS | {
				"outtmpl": filepath + ".%(ext)s"
			}

			try:
				YoutubeDL(options).extract_info(f"ytsearch:{track.keywords}")
			except Exception as e:
				tag_print(f"Error: {e}; Skipping track #{track.index}...", color=Colors.WARN)
			else:
				tag_print(f"Successfully downloaded \"{track.format(ARGS.format)}\"! ({index}/{len(tracklist)})")

	except KeyboardInterrupt:
		tag_print("Interrupted by user.", color=Colors.FAIL)

	except HandledError as e:
		tag_print(f"Error: {e}", color=Colors.FAIL)

if __name__ == "__main__":
	main()
