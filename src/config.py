import os

APPDATA_PATH = os.path.expandvars('%APPDATA%')
MINECRAFT_DIR = os.path.join(APPDATA_PATH, ".wacorp")
AUTHLIB_DIR = os.path.join(MINECRAFT_DIR, "libraries", "com", "mojang", "authlib")

MINECRAFT_VERSION_FILE = os.path.join(MINECRAFT_DIR, "minecraft_version.json")

SERVER_IP = "127.0.0.1"
MINECRAFT_VERSION = "1.20.1"
FORGE_VERSION = "47.3.27"

HTML_URL = "https://wacolauncher-web-production.up.railway.app"
AUTHAPI_URL = "https://wacoapi-production.up.railway.app"