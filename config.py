import yaml

with open("config.yml") as fl:
    config = yaml.load(fl, Loader=yaml.FullLoader)


GUILD_ID = config["GUILD_ID"]
STAFF_ROLE = config["STAFF_ROLE"]
DRIVE_FOLDER = config["DRIVE_FOLDER"]
MOD_CHANNEL = config["MOD_CHANNEL"]

PREFIXES = config["PREFIXES"]

COMMAND_NAME = config["COMMAND_NAME"]

ROLEBAN_ROLE_NAMES = config["ROLEBAN_ROLE_NAMES"]

ROLEBAN_ROLE_IGNORE = config["ROLEBAN_ROLE_IGNORE"]

UNROLEBAN_EXPIRY = config["UNROLEBAN_EXPIRY"]

TOKEN = config["TOKEN"]
