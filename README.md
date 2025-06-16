# spotify-dlp
[![PyPI version](https://img.shields.io/pypi/v/spotify-dlp)](https://pypi.org/project/spotify-dlp/)
[![PyPI downloads](https://img.shields.io/pypi/dm/spotify-dlp)](https://pypi.org/project/spotify-dlp/)
[![GitHub license](https://img.shields.io/github/license/zWolfrost/spotify-dlp)](LICENSE)

Command line downloader for spotify tracks, playlists, albums and top artists songs.
It works by taking the metadata out of these items using the Spotify API and searching them up on YouTube.
Then, it downloads the result by using `yt-dlp`.
**This technically means that the tracks have a *really* small chance to be incorrect.**

&nbsp;
## Installation
1. After having installed [Python 3](https://www.python.org/downloads/) with pip, you can install spotify-dlp using the following command:
	```bash
	pip install spotify-dlp
	```

2. Then, you can authenticate your Spotify account by running the following command:
	```bash
	spotify-dlp --auth
	```
	This command will cause the program to print out an URL. Open it in a browser, log in to your Spotify account and allow the app to access your data. The authentication token should be saved automatically and should get used for future commands.

&nbsp;

*If you do not want to authenticate using the browser, you can manually pass your Client ID and Client Secret as arguments every command. You can get these values by logging to [Spotify developer console](https://developer.spotify.com/dashboard) and clicking on "Create an App", and you can pass them using the `-i` and `-s` arguments, respectively.*

&nbsp;
## Arguments
| Command                | Example              | Description
|:-:                     |:-:                   |:-
|                        | "earfquake"          | The words to search up<br>or a link to a spotify album, artist, playlist or track.<br>If \"saved\", download the user's saved tracks.
| `-a` `--auth`          |                      | Authenticate using the PKCE flow and exit.
| `-i` `--client-id`     | "qwertyuiop"         | The Spotify Client ID*.
| `-s` `--client-secret` | "asdfghjkl"          | The Spotify Client Secret*.
| `-f` `--format`        | "{name} - {authors}" | The format of the downloaded tracks' names.<br>Set to `help` for a list of available fields.
| `-t` `--type`          | "track"              | When searching up a query,<br>the specified type of content.
| `-l` `--slice`         | "2:6"                | The beginning and ending index of the list items<br>to download, separated by a colon ":" (1-based).<br>Either one of those indexes can be omitted.
| `-o` `--output`        | "./album/"           | The output path of the downloaded tracks.
| `-c` `--codec`         | "mp3"                | The audio codec of the downloaded tracks.<br>By default, it is unchanged from the one `yt-dlp` downloads.<br>Requires `ffmpeg` to be installed.
| `-m` `--metadata`      |                      | Whether to download metadata (such as covers).
| `-y` `--yes`           |                      | Whether to skip the confirmation prompt.
| `-v` `--verbose`       |                      | Whether to display verbose information and full errors.
| `-h` `--help`          |                      | Show the help message and exit.

*Required if not authenticated via the `spotify-dlp --auth` command.


&nbsp;
## Use Examples
```sh
spotify-dlp jigsaw falliing into place radiohead
```
```sh
spotify-dlp spirit phone -t album -o "%userprofile%\Desktop" -c mp3 -y
```
```sh
spotify-dlp https://open.spotify.com/album/2Vq0Y8wgiZRYtZ1mQ7zOMG -i "your_client_id" -s "your_client_secret"
```


&nbsp;
## Screenshots
![Downloading album](https://i.imgur.com/DorBju2.png)


&nbsp;
## Changelog
*This changelog only includes changes that are worth mentioning.*

- **2.0.0**:
<br>- Basically, everything changed. Also added package to PyPI.
	- **2.0.1**:
	<br>- Fixed `--verbose` argument not working.
	<br>- Made youtube search more accurate.
	<br>- Better error handling.
- **2.1.0**:
<br>- Added some QOL features.
<br>- Fixed bug where a playlist with more than 100 tracks would be cut off.
<br>- Better error handling.
	- **2.1.1**:
	<br>- Fixed bug where track indexes would not show.
	<br>- Fixed bug where an album with more than 50 tracks would be cut off.
	- **2.1.2**:
	<br>- Fixed bug where an error with a track would stop the whole process.
	- **2.1.3**:
	<br>- Fixed bug where an already downloaded track would be downloaded again.
	<br>- Added colors to the output.
	<br>- Minor tweaks.
- **2.2.0**:
<br>- Added `--metadata` argument, which allows cover downloading.
<br>- Fixed bug where a playlist with an episode in it would error out.
<br>- Fixed bug where the -c argument would give files double extensions.
- **2.3.0**:
<br>- Removed client credentials authentication trough environment variables!
<br>- Added `--auth` argument, which allows for easy PKCE/browser authentication.
<br>- Way more accurate youtube search (but a little slower)
<br>- Better error handling.
	- **2.3.1**:
	<br>- Fix windows path issues and terminal colors.
