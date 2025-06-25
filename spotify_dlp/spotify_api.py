import requests, re
from urllib.parse import urlencode, quote_plus
from spotify_dlp.utils import HandledError, tag_print


class SpotifyItem:
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
	def url(self) -> str:
		return f"https://open.spotify.com/{self.type}/{self.id}"

	@property
	def uri(self) -> str:
		return f"spotify:{self.type}:{self.id}"

	@property
	def keywords(self) -> str:
		return f"{self.title} {' '.join(self.authors)} {self.album}"

	@property
	def quoted_keywords(self) -> str:
		return quote_plus(self.keywords)

	@property
	def format_dict(self) -> dict:
		self_dict = self.__dict__.copy()
		self_dict["authors"] = ", ".join(self_dict["authors"]) if self_dict["authors"] else None
		return self_dict


	def format(self, format: str) -> str:
		return format.format(**self.format_dict)

	def safe_format(self, format: str) -> str:
		return re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "_", self.format(format).strip())


class SpotifyAPI:
	client_id: str
	access_token: str
	refresh_token: str

	def __init__(self, client_id: str = None, access_token: str = None, refresh_token: str = None):
		self.client_id = client_id
		self.access_token = access_token
		self.refresh_token = refresh_token

	@classmethod
	def from_client_credentials_flow(cls, client_id, client_secret):
		token = SpotifyAPI.token_post_request({
			"grant_type": "client_credentials",
			"client_id": client_id,
			"client_secret": client_secret,
		}).get("access_token")

		return cls(client_id, token)

	@staticmethod
	def raise_request_if_error(response: requests.Response):
		try:
			content = response.json()
		except Exception:
			raise HandledError(f"Request to {response.url} returned invalid/missing JSON with code {response.status_code}: {response.reason}")

		if "error" in content:
			if isinstance(content["error"], str):
				msg = content["error"]
			elif isinstance(content["error"], dict) and "message" in content["error"]:
				msg = content["error"]["message"]
			else:
				msg = "An unknown error occurred while processing the request."

			raise HandledError(msg)

		if response.status_code != 200:
			raise HandledError(f"Request to {response.url} failed with code {response.status_code}: {response.reason}")

	@staticmethod
	def token_post_request(data: dict = None) -> dict:
		response = requests.post(
			"https://accounts.spotify.com/api/token",
			headers={"Content-Type": "application/x-www-form-urlencoded"},
			data=urlencode(data)
		)

		SpotifyAPI.raise_request_if_error(response)

		return response.json()

	def api_get_request(self, endpoint: str) -> dict:
		response = requests.get(
			"https://api.spotify.com/v1" + endpoint,
			headers={"Authorization": "Bearer " + self.access_token}
		)

		self.raise_request_if_error(response)

		return response.json()


	def items_by_url(self, url: str) -> list[SpotifyItem]:
		item_type, item_id = self.parse_url(url)
		info: list[SpotifyItem] = []

		match item_type:
			case "album":
				album = self.api_get_request(f"/albums/{item_id}")
				while len(info) < album["total_tracks"]:
					result = self.api_get_request(f"/albums/{item_id}/tracks?limit=50&offset={len(info)}")
					for item in result["items"]:
						item["album"] = album
						info.append(SpotifyItem(item))

			case "artist":
				result = self.api_get_request(f"/artists/{item_id}/top-tracks?market=US")
				for item in result["tracks"]:
					info.append(SpotifyItem(item))

			case "playlist":
				total = None
				while total is None or len(info) < total:
					result = self.api_get_request(f"/playlists/{item_id}/tracks?limit=50&offset={len(info)}")
					if total is None:
						total = result["total"]
					for item in result["items"]:
						if item["track"]["type"] == "track":
							info.append(SpotifyItem(item["track"]))
						else:
							total -= 1
					tag_print(f"Fetching items ({len(info)}/{total})...", start="\r", end="")
				print()

			case "track":
				result = self.api_get_request(f"/tracks/{item_id}")
				info.append(SpotifyItem(result))

			case _:
				raise HandledError(f"\"{item_type}\" type is not currently supported.")

		for index, item in enumerate(info, start=1):
			item.index = index

		return info


	def items_by_search(self, query: str) -> list[SpotifyItem]:
		query = query.lower()
		search_type = "track"

		for t in ("track", "album", "artist", "playlist"):
			if t in query:
				query = query.replace(t, "").strip()
				search_type = t
				break

		result = self.api_get_request(f"/search?q={query}&type={search_type}&limit=1")
		result = list(result.values())[0]["items"]

		if len(result) == 0:
			return []

		return self.items_by_url(f"spotify:{search_type}:{result[0]['id']}")


	@staticmethod
	def parse_url(url: str) -> tuple[str, str]:
		try:
			return re.search(r"(?:open\.spotify\.com/|spotify:)([a-z]+)(?:/|:)(\w+)", url).groups()
		except AttributeError as e:
			raise ValueError("Invalid URL.") from e
