import requests, json, re
from string import Formatter
from spotify_dlp.utils import HandledError, tag_print, Colors

# PKCE Flow Imports
import string, base64, random, hashlib, http.server
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


PKCE_APP_CLIENT_ID = "8e70634824f842519e666d1fefa91fd0"


class Item:
	id: str
	type: str
	title: str
	authors: list[str]
	album: str
	date: str
	duration: int
	cover: str
	entry: int
	index: int

	def __init__(self, item={}):
		self.id = item.get("id")
		self.type = item.get("type")
		self.title = item.get("name")

		match self.type:
			case "track":
				self.authors = [author["name"] for author in item["artists"]]
				self.album = item["album"]["name"]
				self.date = item["album"]["release_date"]
				self.duration = item["duration_ms"] // 1000
				self.cover = item["album"]["images"][0]["url"]
				self.entry = item["track_number"]
			case "episode":
				self.authors = [item["show"]["publisher"]]
				self.album = item["show"]["name"]
				self.date = item["release_date"]
				self.duration = item["duration_ms"] // 1000
				self.cover = item["images"][0]["url"]
				self.entry = None
			case _:
				self.authors = []
				self.album = None
				self.date = None
				self.duration = None
				self.cover = None
				self.entry = None

		self.index = None


	@property
	def url(self):
		return f"https://open.spotify.com/{self.type}/{self.id}"

	@property
	def uri(self):
		return f"spotify:{self.type}:{self.id}"

	@property
	def keywords(self):
		return f"{self.title} {' '.join(self.authors)} {self.album}"


	def get_format_dict(self) -> dict:
		self_dict = self.__dict__.copy()
		self_dict["authors"] = ", ".join(self_dict["authors"])
		return self_dict


	def format(self, format: str) -> str:
		return format.format(**self.get_format_dict())

	def format_with_index(self, format: str) -> str:
		has_placeholder = lambda f, p: any(n == p for _, n, _, _ in Formatter().parse(f))
		return self.format(("" if has_placeholder(format, "index") else "{index}. ") + format)


class SpotifyAPI:
	client_id: str
	access_token: str
	refresh_token: str

	def __init__(self, client_id: str = PKCE_APP_CLIENT_ID, access_token: str = None, refresh_token: str = None):
		self.client_id = client_id
		self.access_token = access_token
		self.refresh_token = refresh_token

	@classmethod
	def from_client_credentials_flow(cls, client_id, client_secret):
		token = cls.request_post(cls, "https://accounts.spotify.com/api/token", {
			"grant_type": "client_credentials",
			"client_id": client_id,
			"client_secret": client_secret,
		}).get("access_token")

		return cls(client_id, token)

	@classmethod
	def from_pkce_flow(cls, client_id: str = PKCE_APP_CLIENT_ID):
		def random_string(length: int = 16) -> str:
			CHARS = string.ascii_uppercase + string.ascii_lowercase + string.digits
			return ''.join(random.choice(CHARS) for _ in range(length))

		def generate_code_challenge(code_verifier: str) -> str:
			digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
			return base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')

		def add_url_params(url, params):
			url_parts = list(urlparse(url))
			query = dict(parse_qsl(url_parts[4]))
			query.update(params)
			url_parts[4] = urlencode(query)
			return urlunparse(url_parts)

		class HttpSpotifyAuthHandler(http.server.BaseHTTPRequestHandler):
			auth_code: str = None

			def do_GET(self):
				self.send_response(200)
				self.send_header("Content-type", "text/plain")
				self.end_headers()
				self.server.auth_code = dict(parse_qsl(urlparse(self.path).query)).get("code")

				if self.server.auth_code:
					self.wfile.write(b"Authentication successful! You can close this window now.")
				else:
					self.wfile.write(b"No authentication code received. Please try again.")

			def log_message(self, format, *args):
				return

		PORT = 3000
		REDIRECT_URI = f"http://127.0.0.1:{PORT}/"

		CODE_VERIFIER = random_string(64)
		AUTH_URL = add_url_params("https://accounts.spotify.com/authorize", {
			"client_id": client_id,
			"response_type": "code",
			"redirect_uri": REDIRECT_URI,
			"scope": "user-library-read",
			"code_challenge_method": "S256",
			"code_challenge": generate_code_challenge(CODE_VERIFIER),
		})

		tag_print(f"Please open the following URL in your browser to authenticate:", color=Colors.BOLD)
		print(AUTH_URL)

		httpd = http.server.HTTPServer(("127.0.0.1", PORT), HttpSpotifyAuthHandler)
		httpd.handle_request()
		AUTH_CODE = httpd.auth_code

		if not AUTH_CODE:
			raise HandledError("No authentication code received. Please try again.")

		content = cls.request_post(cls, "https://accounts.spotify.com/api/token", {
			"client_id": client_id,
			"grant_type": "authorization_code",
			"code": AUTH_CODE,
			"redirect_uri": REDIRECT_URI,
			"code_verifier": CODE_VERIFIER,
		})

		if not content.get("access_token"):
			raise HandledError("No access token received. Please try again.")

		return cls(client_id, content.get("access_token"), content.get("refresh_token"))

	def refresh_pkce_token(self):
		res = self.request_post("https://accounts.spotify.com/api/token", {
			"grant_type": "refresh_token",
			"refresh_token": self.refresh_token,
			"client_id": self.client_id
		})

		self.access_token = res.get("access_token")
		self.refresh_token = res.get("refresh_token")


	@staticmethod
	def request_raise_if_error(content):
		if "error" in content:
			if isinstance(content["error"], str):
				msg = content["error"]
			elif isinstance(content["error"], dict) and "message" in content["error"]:
				msg = content["error"]["message"]
			else:
				msg = "An unknown error occurred while processing the request."

			raise HandledError(msg)

	def request_get(self, endpoint: str) -> dict:
		headers = {"Authorization": "Bearer " + self.access_token}
		result = requests.get("https://api.spotify.com/v1" + endpoint, headers=headers)

		content = json.loads(result.content)
		self.request_raise_if_error(content)

		return content

	def request_post(self, endpoint: str, data: dict = None) -> dict:
		res = requests.post(
			endpoint,
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			data=urlencode(data)
		)

		content = json.loads(res.content)
		self.request_raise_if_error(content)

		return content


	def items_by_url(self, url: str) -> list[Item]:
		item_type, item_id = self.parse_url(url)
		info = []

		match item_type:
			case "album":
				album = self.request_get(f"/albums/{item_id}")
				while len(info) < album["total_tracks"]:
					result = self.request_get(f"/albums/{item_id}/tracks?limit=50&offset={len(info)}")
					for item in result["items"]:
						item["album"] = album
						info.append(Item(item))

			case "artist":
				result = self.request_get(f"/artists/{item_id}/top-tracks?market=US")
				for item in result["tracks"]:
					info.append(Item(item))

			case "playlist" | "saved":
				total = None
				while total is None or len(info) < total:
					result = self.request_get(
						f"/playlists/{item_id}/tracks?limit=100&offset={len(info)}" if item_type == "playlist" else
						f"/me/tracks?limit=50&offset={len(info)}" if item_type in ("liked", "saved") else ""
					)
					if total is None:
						total = result["total"]
					for item in result["items"]:
						if item["track"]["type"] == "track":
							info.append(Item(item["track"]))
						else:
							total -= 1
					print("\r", end="")
					tag_print(f"Fetching items... {len(info)}/{total}", end="")
				print()

			case "track":
				result = self.request_get(f"/tracks/{item_id}")
				info.append(Item(result))

			case _:
				raise HandledError(f"\"{item_type}\" type is not currently supported.")

		for index, item in enumerate(info, start=1):
			item.index = index

		return info


	def items_by_search(self, query: str, search_type="track") -> list[Item]:
		result = self.request_get(f"/search?q={query}&type={search_type}&limit=1")
		result = list(result.values())[0]["items"]

		if len(result) == 0:
			return []

		return self.items_by_url(f"spotify:{search_type}:{result[0]['id']}")


	@staticmethod
	def parse_url(url: str) -> tuple[str, str]:
		try:
			if url in ("saved", ):
				return url, None
			return re.search(r"(?:open\.spotify\.com/|spotify:)([a-z]+)(?:/|:)(\w+)", url).groups()
		except AttributeError as e:
			raise ValueError("Invalid URL.") from e
