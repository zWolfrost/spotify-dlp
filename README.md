# spotify-dlp
Useful downloader for spotify tracks, playlists, albums and top artists tracks.
It works by taking the metadata out of these items using the Spotify API and searching them up on youtube.
Then, it downloads the result by using yt-dlp.


&nbsp;
## Requirements
The ".exe" pyinstaller version in the releases tab has the libraries already included

The only real requirement is getting the spotify client ID and client Secret, which you can get by [creating a spotify app](https://developer.spotify.com/documentation/web-api/concepts/apps) in the spotify dashboard.


&nbsp;
## How to set up
- Download the latest release along with the `.env` file and move them into a new folder

- Fill the `.env` file with your spotify app id and secret (also remove all the text before the `.env` extension).

You're done! Now to use it just open a command prompt in the folder you've just created (shift+right click the folder > "Open command window here") and digit `.\spotify-dlp` along with the query and arguments you want




&nbsp;
## Arguments
| Command         | Shorthand | Default  | Description
|:-:              |:-:        |:-:       |:-
| --client-id     | -i        | *        | Required. The Spotify Client ID.
| --client-secret | -s        | *        | Required. The Spotify Client Secret.
| --output-path   | -o        | "."      | The output path of the downloaded tracks.
| --audio-codec   | -a        | "m4a"    | The audio codec of the downloaded tracks.
| --ask-confirm   | -c        | False    | Whether to ask for confirmation before downloading.
| --list-items    | -l        | ":"      | The beginning and ending index of the list items to download separated by a colon \":\" (1-based). Either one of those indexes can be omitted.
| --search-type   | -t        | "track"  | When searching up a query, the specified type of content.
| --verbose       | -v        | False    | Whether to include verbose text.

*Looks the value up in a ".env" file which should be in the same filepath as the script

Note: The .env file in question is [present in the repository](.env) as a reference, in case you were wondering about its structure.


&nbsp;
## Use Examples
```
spotify-dlp change deftones
```
```
spotify-dlp white pony -t album -o "%userprofile%\Desktop" -a mp3 -c
```
```
spotify-dlp https://open.spotify.com/album/5LEXck3kfixFaA3CqVE7bC -i <Client ID> -s <Client Secret>
```


&nbsp;
## Screenshots
![Downloading album](https://i.imgur.com/5A51fah.png)