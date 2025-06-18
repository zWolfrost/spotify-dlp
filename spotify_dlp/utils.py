import os, json

class HandledError(Exception):
   pass

def tag_print(string: str, color: str = None, prompt: bool = False, end: str = "\n"):
	TAG = "[spotify-dlp] "
	string = TAG + string

	if color:
		string = color + string + Colors.ENDC

	return input(string) if prompt else print(string, end=end)

class Colors():
	ENDC = "\033[0m"
	FAIL = "\033[91m"
	WARN = "\033[93m"
	BOLD = "\033[1m"

class Config():
	DEFAULT_CONFIG = {
		"client_id": None,
		"client_secret": None,
		"format": "{title} - {authors} ({album})",
		"type": "track",
		"slice": ":",
		"output": ".",
		"codec": None,
		"metadata": False,
		"yes": False,
		"verbose": False,
	}

	@staticmethod
	def get_config_filepath() -> str:
		if os.name == "nt":
			return os.path.join(os.getenv("APPDATA"), "spotify-dlp", "config.json")
		else:
			return os.path.expanduser("~/.config/spotify-dlp/config.json")

	@staticmethod
	def read(name: str = None):
		if not os.path.exists(os.path.dirname(Config.get_config_filepath())) or \
				not os.path.isfile(Config.get_config_filepath()):
			return Config.DEFAULT_CONFIG.get(name)

		with open(Config.get_config_filepath(), "r") as f:
			settings: dict = Config.DEFAULT_CONFIG | json.load(f)

		return settings.get(name) if name else settings

	@staticmethod
	def write(name: str, value: str):
		os.makedirs(os.path.dirname(Config.get_config_filepath()), exist_ok=True)

		settings = {}

		if os.path.isfile(Config.get_config_filepath()):
			with open(Config.get_config_filepath(), "r") as f:
				settings = json.load(f)

		settings[name] = value

		with open(Config.get_config_filepath(), "w") as f:
			json.dump(settings, f, indent=4)
