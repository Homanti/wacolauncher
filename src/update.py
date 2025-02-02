import webview
from src.api import Api
from src.config import HTML_URL
from src.logger_setup import setup_logging
from src.utils import create_folder_if_needed

if __name__ == '__main__':
    setup_logging("update_logs.txt")

    create_folder_if_needed("data")

    api = Api()
    window = webview.create_window(title="WacoLauncher", width=400, url=f"{HTML_URL}/update", height=100, js_api=api, resizable=False, fullscreen=False, frameless=True, hidden=True)
    api.set_window(window)

    webview.start(api.update_launcher, debug=False)