from setuptools import setup, find_packages

setup(
	name="spotify-dlp",
	author="zWolfrost",
	version="2.6.0",
	description="Command line downloader for spotify tracks, playlists, albums and top artists songs.",
	long_description=open("README.md").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/zWolfrost/spotify-dlp",
	packages=find_packages(),
	install_requires=[
		"requests>=2.31.0",
		"yt_dlp>=2024.4.9"
	],
	entry_points={
		"console_scripts": [
			"spotify-dlp = spotify_dlp.spotify_dlp:main"
		]
	}
)
