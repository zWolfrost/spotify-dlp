# spotify-dlp
[![PyPI version](https://img.shields.io/pypi/v/spotify-dlp)](https://pypi.org/project/spotify-dlp/)
[![PyPI downloads](https://img.shields.io/pypi/dm/spotify-dlp)](https://pypi.org/project/spotify-dlp/)
[![GitHub license](https://img.shields.io/github/license/zWolfrost/spotify-dlp)](LICENSE)

Command line downloader for spotify tracks, playlists, albums and top artists songs.
It works by taking the metadata out of these items using the Spotify API and searching them up on YouTube Music.
Then, it downloads the result by using yt-dlp.


&nbsp;
## Installation
1. After having installed [Python 3](https://www.python.org/downloads/) with pip, you can install spotify-dlp using the following command:
	```bash
	pip install spotify-dlp
	```

2. Then, login to [Spotify developer console](https://developer.spotify.com/dashboard) and click on "Create an App". Fill in details for name and description.

3. Make a note of Client ID and Client Secret. These values need to be then set to the `SPOTIFY_DLP_CLIENT_ID` and `SPOTIFY_DLP_CLIENT_SECRET` environment variables respectively

	Alternatively, you can also include them in a `.env` file in the working directory, or even directly pass them as arguments.

	You can set environment variables by doing the following:

	Windows (run in cmd as administrator):
	```sh
	setx SPOTIFY_DLP_CLIENT_ID "your_client_id"
	```
	```sh
	setx SPOTIFY_DLP_CLIENT_SECRET "your_client_secret"
	```

	Linux (add to `~/.bashrc`):
	```sh
	export SPOTIFY_DLP_CLIENT_ID="your_client_id"
	export SPOTIFY_DLP_CLIENT_SECRET="your_client_secret"
	```

4. You can now use the script by running `spotify-dlp` in the command line.
	Also, ffmpeg is required if you wish to convert the m4a codec to another one using the `-c` argument.


&nbsp;
## Arguments
| Command                | Example                        | Description
|:-:                     |:-:                             |:-
|                        | "kon queso"                    | The words to search up<br>or a link to a spotify album, artist, playlist or track.
| `-i` `--client-id`     | "qwertyuiop"                   | The Spotify Client ID*.
| `-s` `--client-secret` | "asdfghjkl"                    | The Spotify Client Secret*.
| `-f` `--format`        | "{name} - {authors} ({album})" | The format of the downloaded tracks' names.<br>Set to `help` for a list of available fields.
| `-t` `--type`          | "track"                        | When searching up a query,<br>the specified type of content.
| `-o` `--output`        | "./album/"                     | The output path of the downloaded tracks.
| `-c` `--codec`         | "m4a"                          | The audio codec of the downloaded tracks.
| `-l` `--slice`         | "2:6"                          | The beginning and ending index of the list items<br>to download, separated by a colon ":" (1-based).<br>Either one of those indexes can be omitted.
| `-y` `--yes`           |                                | Whether to skip the confirmation prompt.
| `-v` `--verbose`       |                                | Whether to display verbose information.
| `-h` `--help`          |                                | Show the help message and exit.

*Required if not already found in the environment variables or in the working directory `.env` file.


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
![Downloading album](https://i.imgur.com/t5N1Og3.png)


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