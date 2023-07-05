# spotify-dlp
Useful downloader for spotify tracks, playlists, albums and top artists tracks.
It works by taking the metadata out of these items using the Spotify API and searching them up on youtube.
Then, it downloads the result by using yt-dlp.


&nbsp;
## Requirements
The ".exe" pyinstaller version in the releases tab has the libraries already included

The only real requirements are the spotify client ID and client Secret, which you can get by [creating a spotify app](https://developer.spotify.com/documentation/web-api/concepts/apps) in the spotify dashboard.


&nbsp;
## Arguments
| Command         | Shorthand | Required           | Default  | Description
|:-:              |:-:        |:-:                 |:-:       |:-
|                 |           | :heavy_check_mark: |          | The words to search up or a link to a spotify album, artist, playlist or track.
| --client-id     | -i        | :heavy_check_mark: | *        | The Spotify Client ID.
| --client-secret | -s        | :heavy_check_mark: | *        | The Spotify Client Secret.
| --output        | -o        | :x:                | "."      | The output path of the downloaded tracks.
| --search-type   | -t        | :x:                | "tracks" | When searching up a query, the specified type of content.

*Looks the value up in a ".env" file which **should be in the same filepath as the script**

Note: The .env file in question is [present in the repository](.env) as a reference, in case you were wondering about its structure.


&nbsp;
## Use Examples
```
spotify-dlp change deftones -o "%userprofile%\Downloads"
```
```
spotify-dlp https://open.spotify.com/album/7o4UsmV37Sg5It2Eb7vHzu -i <Client ID> -s <Client Secret>
```


&nbsp;
## Screenshots
![Downloading album](https://i.imgur.com/5A51fah.png)