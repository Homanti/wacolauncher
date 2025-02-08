import threading
import psutil
import webview
from src.logger_setup import setup_logging
from src.api import Api
from src.config import MINECRAFT_DIR, AUTHLIB_DIR, MINECRAFT_VERSION_FILE, HTML_URL
from src.utils import create_folder_if_needed, read_json, write_json

def main():
    setup_logging("launcher_logs.txt")

    create_folder_if_needed("./data")
    create_folder_if_needed(MINECRAFT_DIR)
    create_folder_if_needed(AUTHLIB_DIR)

    api = Api()

    window = webview.create_window(
        title="WacoLauncher",
        width=1296,
        height=809,
        url=f"{HTML_URL}/{api.check_login()}",
        js_api=api,
        resizable=False,
        fullscreen=False,
        hidden=True
    )

    api.set_window(window)

    # api.update_updater()

    settings = read_json("data/settings.json")
    minecraft_version = read_json(MINECRAFT_VERSION_FILE)

    if not settings or not settings["ram"]:
        memory_info = psutil.virtual_memory()
        write_json("data/settings.json", {"ram": (round(memory_info.total / (1024 ** 2) / 2))})

    if minecraft_version is None:
        write_json(MINECRAFT_VERSION_FILE, {"mods": [], "rp_version": None, "pointblank": None})

    threading.Thread(target=api.set_server_online, daemon=True).start()
    webview.start(debug=False)

if __name__ == '__main__':
    main()