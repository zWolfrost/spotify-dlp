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

2. Then, you can authenticate your Spotify account by running this command and following the instructions:
	```bash
	spotify-dlp --auth
	```
	The authentication tokens should get saved automatically and used for future commands.

&nbsp;
## Arguments
| Command                | Example            | Short Description
|:-:                     |:-:                 |:-
|                        | "kid a album"      | The words to search up<br>or a link to a spotify album, artist, playlist or track.<br>Include keywords like `album` or `playlist`<br>to specify the type of item to search for.
| `-a` `--auth`          |                    | Authenticate using the client credentials flow and exit.
| `-i` `--client-id`     | "qwertyuiop"       | The Spotify Client ID.
| `-s` `--client-secret` | "asdfghjkl"        | The Spotify Client Secret.
| `-f` `--format`        | "{index}. {title}" | The format of the downloaded tracks' names.<br>Set to `help` for a list of available fields.
| `-r` `--range`         | "2:6,10"           | The beginning and ending index of the list items<br>to download, separated by a colon "`:`" (1-based). <br>Multiple ranges can be specified with a comma "`,`".
| `-o` `--output`        | "./album/"         | The output path of the downloaded tracks.
| `-c` `--codec`         | "mp3"              | The audio codec of the downloaded tracks.<br>Requires `ffmpeg` to be installed.
| `-m` `--metadata`      |                    | Whether to download metadata (such as covers).
| `-b` `--browser`       | "chrome"           | The name of the browser from which cookies<br>should be extracted, to bypass the age restriction.
| `-y` `--yes`           |                    | Whether to skip the confirmation prompt.
| `-v` `--verbose`       |                    | Whether to display verbose information and full errors.
| `-h` `--help`          |                    | Show the help message and exit.

&nbsp;
## Usage Examples
```sh
spotify-dlp jigsaw falling into place
```
```sh
spotify-dlp spirit phone album -o "./Desktop/spotify" -c mp3 -y
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
	- **2.3.2**:
	<br>- Fixed port conflicts with `--auth` argument.
	<br>- Faster searching.
- **2.4.0**:
<br>- Removed authentication via PKCE flow, as [spotify only supports up to 25 users for apps not made by companies.](https://docs.google.com/forms/d/1O87xdPP1zWUDyHnduwbEFpcjA57JOaefCgBShKjAqlo/viewform?edit_requested=true)
- **2.5.0**:
<br>- Added config file support.
<br>- Renamed `--slice` argument to `--range`.
<br>- Added comma (",") support for `--range` argument.
<br>- The item type can be now specified in the search query; removed `--type` argument.
	- **2.5.1**:
	<br>- Fixed wrong config path message on Windows.
	<br>- Fixed "Requested format is not available" error.
	<br>- Other small bug fixes.
	- **2.5.2**:
	<br>- Fixed "Requested format is not available." error.
- **2.6.0**:
<br>- Added `--browser` argument which allows importing cookies from a browser.
