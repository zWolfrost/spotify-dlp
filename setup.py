from setuptools import setup, find_packages

setup(
	name="spotify-dlp",
	author="zWolfrost",
	version="2.0.0",
	description="Command line downloader for spotify tracks, playlists, albums and top artists tracks.",
	long_description=open("README.md").read(),
	long_description_content_type="text/markdown",
	url="https://github.com/zWolfrost/spotify-dlp",
	packages=find_packages(),
	install_requires=[
		"requests>=2.28.0",
		"yt_dlp>=2023.6.22"
	],
	entry_points={
		"console_scripts": [
			"spotify-dlp = spotify_dlp:main"
		]
	}
)
