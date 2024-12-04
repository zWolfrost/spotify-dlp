import requests, json, re
import urllib.parse
from string import Formatter


class Track:
   id: str
   type: str
   title: str
   authors: list[str]
   album: str
   date: str
   entry: int
   index: int

   def __init__(self, item):
      self.id = item["id"]
      self.type = item["type"]
      self.title = item["name"]
      self.index = None

      match self.type:
         case "track":
            self.authors = [author["name"] for author in item["artists"]]
            self.album = item["album"]["name"]
            self.date = item["album"]["release_date"]
            self.entry = item["track_number"]
         case "episode":
            self.authors = [item["show"]["publisher"]]
            self.album = item["show"]["name"]
            self.date = item["release_date"]
            self.entry = 0


   @property
   def url(self):
      return f"https://open.spotify.com/{self.type}/{self.id}"

   @property
   def uri(self):
      return f"spotify:{self.type}:{self.id}"

   @property
   def keywords(self):
      return urllib.parse.quote_plus(f"{self.title} {' '.join(self.authors)} {self.album}")


   def get_format_dict(self) -> dict:
      self_dict = self.__dict__
      return {
         **self_dict,
         "authors": ", ".join(self_dict["authors"]),
      }


   def format(self, format: str) -> str:
      return format.format(**self.get_format_dict())

   def format_with_index(self, format: str) -> str:
      has_placeholder = lambda f, p: any(n == p for _, n, _, _ in Formatter().parse(f))
      return self.format(("" if has_placeholder(format, "index") else "{index}. ") + format)


class SpotifyAPI:
   def __init__(self, client_id, client_secret):
      headers = {"Content-Type": "application/x-www-form-urlencoded"}
      data = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"

      result = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)

      content = json.loads(result.content)
      if "error" in content:
         raise Exception(content["error"])

      self.token = json.loads(result.content)["access_token"]


   def request_wrapper(self, endpoint: str) -> dict:
      headers = {"Authorization": "Bearer " + self.token}
      result = requests.get("https://api.spotify.com/v1" + endpoint, headers=headers)

      content = json.loads(result.content)
      if "error" in content:
         raise Exception(content["error"]["message"])

      return content


   def items_by_url(self, url: str) -> list[Track]:
      media_type, media_id = self.parse_url(url)
      info = []

      match media_type:
         case "album":
            album = self.request_wrapper(f"/albums/{media_id}")
            while len(info) < album["total_tracks"]:
               result = self.request_wrapper(f"/albums/{media_id}/tracks?limit=50&offset={len(info)}")
               for item in result["items"]:
                  item["album"] = album
               info += [Track(item) for item in result["items"]]

         case "artist":
            result = self.request_wrapper(f"/artists/{media_id}/top-tracks?market=US")
            info += [Track(item) for item in result["tracks"]]

         case "playlist":
            total = 1
            while len(info) < total:
               result = self.request_wrapper(f"/playlists/{media_id}/tracks?limit=100&offset={len(info)}")
               total = result["total"]
               info += [Track(item["track"]) for item in result["items"]]

         case "track":
            result = self.request_wrapper(f"/tracks?ids={media_id}")
            info += [Track(item) for item in result["tracks"]]

         case _:
            raise Exception(f"\"{media_type}\" type is not supported.")

      for index, item in enumerate(info):
         item.index = index + 1

      return info


   def items_by_search(self, query: str, search_type="track") -> list[Track]:
      result = self.request_wrapper(f"/search?q={query}&type={search_type}&limit=1")
      result = list(result.values())[0]["items"]

      if (len(result) == 0): raise Exception("No tracks were found.")

      info = self.items_by_url(f"https://open.spotify.com/{search_type}/{result[0]['id']}")

      return info


   @staticmethod
   def parse_url(url: str) -> tuple[str, str]:
      search = re.search(r"(?:.*?open\.spotify\.com/|spotify:)([a-z]+)(?:/|:)(\w+)", url)
      return search.groups() if search else None