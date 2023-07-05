import base64, json, requests

SPOTIFY_ENDPOINT = "https://api.spotify.com/v1"

class SpotifyApi:
   def __init__(self, client_id, client_secret):
      auth_string = client_id + ":" + client_secret
      auth_base64 = str(base64.b64encode(auth_string.encode("utf-8")), "utf-8")

      url = "https://accounts.spotify.com/api/token"
      headers = {
         "Authorization": "Basic " + auth_base64,
         "Content-Type": "application/x-www-form-urlencoded"
      }
      data = {"grant_type": "client_credentials"}
      result = requests.post(url, headers=headers, data=data)

      self.token = json.loads(result.content)["access_token"]


   def get_request(self, uri):
      headers = {"Authorization": "Bearer " + self.token}
      result = requests.get(SPOTIFY_ENDPOINT + uri, headers=headers)
      content = json.loads(result.content)

      if ("error" in content): raise Exception(content["error"]["message"])

      return content


   def get_tracks_info(self, track, searchtype="tracks"):

      def item_info(item, album_name=None):
         if (album_name == None): album_name = item["album"]["name"]
         info = {
            "name": item["name"],
            "authors": [artist["name"] for artist in item["artists"]],
            "album": album_name,
         }
         info["query"] = " ".join(flatten(list(info.values())))

         info["explicit"] = item["explicit"]
         info["url"] = item["external_urls"]["spotify"]
         return info

      def flatten(input_list):
         result = []
         for item in input_list:
            if isinstance(item, list): result.extend(flatten(item))
            else: result.append(item)
         return result

      try:
         type, id = self.clean_url(track)
      except:
         result = self.get_request(f"/search?q={track}&type=album,artist,playlist,track&limit=1")[searchtype]["items"]

         if (len(result) == 0): raise Exception("No tracks were found!")

         type, id = self.clean_url(result[0]["external_urls"]["spotify"])


      match(type):
         case "album":
            album_name = self.get_request(f"/albums/{id}")["name"]
            result = self.get_request(f"/albums/{id}/tracks")

            info = [item_info(item, album_name) for item in result["items"]]

         case "artist":
            result = self.get_request(f"/artists/{id}/top-tracks?market=US")

            info = [item_info(item) for item in result["tracks"]]

         case "playlist":
            result = self.get_request(f"/playlists/{id}/tracks")

            info = [item_info(item["track"]) for item in result["items"]]

         case "track":
            result = self.get_request(f"/tracks?ids={id}")

            info = [item_info(item) for item in result["tracks"]]


      return info


   @staticmethod
   def clean_url(url, begstr="spotify.com/", endstr="?"):

      beg = url.find(begstr)
      if (beg == -1): beg = 0
      else: beg += len(begstr)

      end = url.find(endstr, beg)
      if (end == -1): end = len(url)

      return url[ beg : end ].split("/")




############### TESTING ###############


#import os, json
#from dotenv import load_dotenv
#load_dotenv()
#spotifyapi = SpotifyApi(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))
#
#
#query = "hybrid theory"
#searchtype = "tracks"
#"""
#https://open.spotify.com/album/09wqWIOKWuS6RwjBrXe08B?si=3266fb2161824070
#https://open.spotify.com/artist/7jy3rLJdDQY21OgRLCZ9sD?si=4a55232349a94d48
#https://open.spotify.com/playlist/7mBgbujFe7cAZ5rrK0HTxp?si=82b3e3f2549641b5
#https://open.spotify.com/show/6TXzjtMTEopiGjIsCfvv6W?si=8f7012b4b6d340be
#https://open.spotify.com/track/6rDaCGqcQB1urhpCrrD599?si=05987dc8f4ae4d31
#"""
#
#
#print(json.dumps(spotifyapi.get_tracks_info(query, searchtype), indent=3))