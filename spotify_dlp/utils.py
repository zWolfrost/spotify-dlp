import os, json

class HandledError(Exception):
   pass

def tag_print(string: str, color: str = None, prompt: bool = False, start: str = "", end: str = "\n"):
	TAG = "[spotify-dlp]"
	string = start + TAG + " " + string

	if color:
		string = color + string + Colors.ENDC

	return input(string) if prompt else print(string, end=end, flush=True)

class Colors():
	ENDC = "\033[0m"
	FAIL = "\033[91m"
	WARN = "\033[93m"
	BOLD = "\033[1m"

class Config():
	DEFAULT_CONFIG = {
		"client_id": None,
		"client_secret": None,
		"format": "{index}. {title} - {authors} ({album})",
		"range": ":",
		"output": ".",
		"codec": None,
		"metadata": False,
		"browser": None,
		"yes": False,
		"verbose": False,
	}

	@staticmethod
	def get_config_filepath() -> str:
		if os.name == "nt":
			return os.path.join(os.getenv("APPDATA"), "spotify-dlp", "config.json")
		else:
			return os.path.join(os.path.expanduser("~"), ".config", "spotify-dlp", "config.json")

	@staticmethod
	def raw_read() -> dict:
		if os.path.isfile(Config.get_config_filepath()):
			with open(Config.get_config_filepath(), "r") as f:
				return json.load(f)
		return {}

	@staticmethod
	def read(name: str = None):
		settings = Config.DEFAULT_CONFIG | Config.raw_read()

		return settings.get(name) if name else settings

	@staticmethod
	def write(name: str, value: str):
		settings = Config.raw_read()

		settings[name] = value

		os.makedirs(os.path.dirname(Config.get_config_filepath()), exist_ok=True)

		with open(Config.get_config_filepath(), "w") as f:
			json.dump(settings, f, indent=4)

class YTDLPLogger:
	def __init__(self, verbose: bool = False):
		self.verbose = verbose

	def debug(self, msg: str):
		if self.verbose:
			print(msg)

	def info(self, msg: str):
		if self.verbose:
			print(msg)

	def warning(self, msg: str):
		if self.verbose:
			print(msg)

	def error(self, msg: str):
		pass
