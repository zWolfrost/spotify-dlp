import os

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

class TokenFile():
	@staticmethod
	def get_token_filepath() -> str:
		if os.name == "nt":
			return os.path.join(os.getenv("APPDATA"), "spotify-dlp")
		else:
			return os.path.expanduser("~/.config/spotify-dlp/")

	@staticmethod
	def read_token(name: str) -> str:
		filepath = os.path.join(TokenFile.get_token_filepath(), name)

		if not os.path.exists(filepath):
			return None

		with open(filepath, "r") as f:
			return f.read().strip()

	@staticmethod
	def write_token(name: str, token: str):
		if not os.path.exists(TokenFile.get_token_filepath()):
			os.mkdir(TokenFile.get_token_filepath())

		with open(os.path.join(TokenFile.get_token_filepath(), name), "w+") as f:
			f.write(token)
