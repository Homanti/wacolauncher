import subprocess
import time
import webbrowser
import zipfile
from urllib.parse import urlsplit
import keyring
import minecraft_launcher_lib
import io
import psutil
from mcstatus import JavaServer
from src.config import SERVER_IP, MINECRAFT_DIR, AUTHLIB_DIR, MINECRAFT_VERSION_FILE, AUTHAPI_URL, MINECRAFT_VERSION, FORGE_VERSION
from src.utils import *

class Api:
    def __init__(self):
        self._window = None
        self.downloading = False
        self.launched = False
        self.tab_name = None
        self.server_status = None

    def set_window(self, window):
        self._window = window

    def load_tab(self, tab_name, info_message_title = None, info_message_text = None):
        self.tab_name = tab_name
        self._window.load_url(f"https://wacolauncher-web-production.up.railway.app/{tab_name}")

        if tab_name == "index" or tab_name == "settings":
            if self.server_status:
                self._window.evaluate_js(f"""
                const players_online = document.getElementById('players_online').textContent = "Игроков онлайн: {self.server_status.players.online}"
                """)
            else:
                self._window.evaluate_js(f"""
                const players_online = document.getElementById('players_online').textContent = "Сервер выключен"
                """)

        if tab_name == "index" and self.downloading:
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)

        elif tab_name == "index" and self.launched:
            self.disable_button("btn_play", True)
            self.change_innerHTML("btn_play", "Запуск...")

        if info_message_title and info_message_text:
            self.show_info_message(info_message_title, info_message_text)

    def read_json(self, filename):
        return read_json(filename)

    def write_json(self, filename, data):
        return write_json(filename, data)

    def file_download(self, url, folder_path, download_name = None):
        os.makedirs(folder_path, exist_ok=True)

        try:
            response = requests.get(url, stream=True)
            total_length = response.headers.get('content-length')

            if 'Content-Disposition' in response.headers:
                filename = response.headers.get('Content-Disposition').split('filename=')[-1].strip('"')
            else:
                filename = os.path.basename(urlsplit(url).path)

            file_path = os.path.join(folder_path, filename)
            self.downloading = True

            if total_length is None:
                if download_name:
                    self.progress_bar_set(0, download_name)
            else:
                dl = 0
                total_length = int(total_length)
                with open(file_path, 'wb') as file:
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        file.write(data)
                        progress = round(dl / total_length * 100, 2)

                        if download_name:
                            self.progress_bar_set(progress, download_name)

                logging.info(f"Файл успешно загружен и сохранен в {file_path}.")

        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка загрузки файла: {e}")
            return False

        self.downloading = False
        return True

    def set_password(self, nickname, password):
        keyring.set_password("WacoLauncher", nickname, password)

    def get_password(self, nickname):
        return keyring.get_password("WacoLauncher", nickname)

    def save_account(self, nickname, password):
        self.set_password(nickname, password)
        new_account_data = {
            "nickname": nickname,
            "active": True,
        }
        try:
            try:
                with open("data/credentials.json", "r") as json_file:
                    data = json.load(json_file)
            except (FileNotFoundError, json.JSONDecodeError):
                data = []

            if not isinstance(data, list):
                data = [new_account_data]
            else:
                updated = False
                for account in data:
                    if account["nickname"] == nickname:
                        account["active"] = True
                        updated = True
                    else:
                        account["active"] = False

                if not updated:
                    for account in data:
                        account["active"] = False
                    data.append(new_account_data)

            self.write_json("data/credentials.json", data)
        except Exception as e:
            logging.error(f"Ошибка при обработке файла data/credentials.json: {e}")

    def account_login(self, nickname, password):
        response = requests.post(
            f"{AUTHAPI_URL}/database/login",
            json={"nickname": nickname, "password": password},
        )

        if response.status_code == 200:
            self.save_account(response.json()["result"][1], response.json()["result"][2])
            return {"status_code": 200, "result": response.json()["result"]}

        elif response.status_code == 401:
            data = self.read_json("data/credentials.json")

            if data:
                data = [item for item in data if item['nickname'] != nickname]
                self.write_json("data/credentials.json", data)

            logging.error(f"Login failed: {response.json()['detail']}")
            return {"status_code": 401}

        return {"status_code": response.status_code}

    def account_register(self, nickname, password, rp_history, how_did_you_find, skin_bytes):
        skin_file = io.BytesIO(bytes(skin_bytes))
        skin_file.name = f'{nickname}_skin.png'

        response = requests.post(
            f"{AUTHAPI_URL}/database/register",
            data={
                "nickname": nickname,
                "password": password,
                "rp_history": rp_history,
                "how_did_you_find": how_did_you_find
            },
            files={'skin_png': (skin_file.name, skin_file, 'image/png')}
        )
        if response.status_code == 200:
            return self.account_login(nickname, password)
        elif response.status_code == 409:
            return {"status_code": 409}
        else:
            logging.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            return {"status_code": 401}

    def update_skin(self, nickname, password, skin_bytes):
        skin_file = io.BytesIO(bytes(skin_bytes))
        skin_file.name = f'{nickname}_skin.png'

        response = requests.post(
            f"{AUTHAPI_URL}/database/update_skin",
            params={
                "nickname": nickname,
                "password": password,
            },
            files={'skin_png': (skin_file.name, skin_file, 'image/png')}
        )
        if response.status_code == 200:
            return True
        else:
            logging.error(f"Update skin failed: {response.json().get('detail', 'Unknown error')}")
            return False

    def open_link(self, url):
        webbrowser.open(url)

    def get_active_account(self):
        data = read_json("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    nickname = item['nickname']
                    password = self.get_password(nickname)
                    if password:
                        return self.account_login(nickname, password)
        return None

    def check_login(self):
        data = read_json("data/credentials.json")
        try:
            if data:
                for item in data:
                    if item['active']:
                        nickname = item['nickname']
                        password = self.get_password(nickname)
                        if password:
                            result = self.account_login(nickname, password)
                            if result["status_code"] == 200:
                                if result["result"][3] is None:
                                    self.tab_name = "link_discord_register"
                                    return self.tab_name
                                else:
                                    self.tab_name = "index"
                                    return "index"
                            else:
                                self.tab_name = "login"
                                return self.tab_name
            else:
                self.tab_name = "login"
                return self.tab_name
        except:
            self.tab_name = "login"
            return self.tab_name

    def update_password(self, nickname, password, new_password):
        response = requests.post(
            f"{AUTHAPI_URL}/database/update_password",
            params={"action": "update_password", "nickname": nickname, "password": password, "new_password": new_password}
        )

        if response.status_code == 200:
            self.save_account(nickname, new_password)
            return 200

        elif response.status_code == 401:
            logging.error(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    def delete_account(self, nickname, password):
        response = requests.post(
            f"{AUTHAPI_URL}/database/",
            params={"action": "delete", "nickname": nickname, "password": password}
        )

        if response.status_code == 200:
            data = self.read_json("data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == nickname and item['password'] == password)]
                self.write_json("data/credentials.json", data)
            return 200

        elif response.status_code == 401:
            logging.error(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    def progress_bar_set(self, percent, download_name):
        self._window.evaluate_js(f"""
        document.getElementById('progress_bar').style.width = '{percent}%';
        document.getElementById('progress_text').textContent = 'Установка ' + {json.dumps(download_name)} + '... {round(percent, 2)}%';
        """)

    def open_progress_bar(self, status):
        if status:
            self._window.evaluate_js(f"""
            const progressBarContainer = document.querySelector('.progress-bar-container');
            progressBarContainer.style.marginTop = '-30px';
            """)
        else:
            self._window.evaluate_js(f"""
            const progressBarContainer = document.querySelector('.progress-bar-container');
            progressBarContainer.style.marginTop = '0';
            """)

    def disable_button(self, button_id, status):
        if status:
            status = "true"
            if button_id == "profile_button":
                self._window.evaluate_js(f"""
                document.getElementById('profile_button').onclick = null;
                """)
        else:
            status = "false"
            if button_id == "profile_button":
                self._window.evaluate_js(f"""
                document.getElementById('profile_button').onclick = toggleDropdown;
                """)

        self._window.evaluate_js(f"""
        document.getElementById('{button_id}').disabled = {status};
        """)

    def change_innerHTML(self, element_id, innerHTML):
        self._window.evaluate_js(f"""
        document.getElementById('{element_id}').innerHTML = '{innerHTML}';
        """)

    def show_info_message(self, title, text):
        self._window.evaluate_js(f"""
        show_info_modal('{title}', '{text}');
        """)

    def show_minecraft_install_progress(self, progress, total, status):
        percent = float((progress / total) * 100)

        if "Download" in status:
            status = status.replace("Download", "")

        self.open_progress_bar(True)
        self.progress_bar_set(percent, "Minecraft: " + status)

    def disable_launch_button(self):
        self.downloading = True
        self.open_progress_bar(True)
        self.disable_button("btn_play", True)
        self.disable_button("profile_button", True)
        self.disable_button("btn_settings", True)
        self.change_innerHTML("btn_play", 'Установка...')

    def enable_launch_button(self):
        self.downloading = False
        self.open_progress_bar(False)
        self.disable_button("btn_play", False)
        self.disable_button("profile_button", False)
        self.disable_button("btn_settings", False)
        self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

    def install_minecraft(self):
        try:
            max_value = [0]
            status = [0]
            self.disable_launch_button()

            callback = {
                "setStatus": lambda value: status.__setitem__(0, value),
                "setProgress": lambda value: self.show_minecraft_install_progress(value, max_value[0], status[0]),
                "setMax": lambda value: max_value.__setitem__(0, value)
            }

            minecraft_launcher_lib.forge.install_forge_version(f"{MINECRAFT_VERSION}-{FORGE_VERSION}", MINECRAFT_DIR, callback=callback)

            self.write_json(MINECRAFT_VERSION_FILE, {"mods": [], "rp_version": None, "pointblank": None})

            with open(MINECRAFT_DIR + "/options.txt", "w", encoding="utf-8") as file:
                options = (
                    'resourcePacks:["vanilla","pointblank_resources","pfm-asset-resources","mod_resources","file/WacoRP.zip"]\n'
                    'lang:ru_ru\n'
                )
                file.write(options)

            self.file_download("https://github.com/Homanti/wacominecraft/raw/refs/heads/main/servers.dat", MINECRAFT_DIR, "Minecraft")
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            self.enable_launch_button()

    def install_mods(self):
        try:
            minecraft_version = self.read_json(MINECRAFT_VERSION_FILE)
            latest_minecraft_version = self.read_json("https://raw.githubusercontent.com/Homanti/wacominecraft/main/mods.json")

            list_mods = minecraft_version["mods"]
            latest_list_mods = latest_minecraft_version["mods"]

            self.disable_launch_button()

            mods_dir = os.path.join(MINECRAFT_DIR, "mods")

            if not os.path.exists(mods_dir):
                os.makedirs(mods_dir)

            mods_to_remove = list(set(list_mods) - set(latest_list_mods))
            mods_to_install = list(set(latest_list_mods) - set(list_mods))

            for mod in mods_to_remove:
                mod_path = os.path.join(mods_dir, mod)
                if os.path.exists(mod_path):
                    os.remove(mod_path)
                    logging.info(f"Удален мод: {mod}")

            for mod in mods_to_install:
                mod_path = os.path.join(mods_dir, mod)
                if not os.path.exists(mod_path):
                    logging.info(f"Скачивание мода: {mod}")
                    self.file_download(f"https://github.com/Homanti/wacominecraft/raw/main/mods/{mod}", mods_dir, f"модов: {mod}")

            for mod in latest_list_mods:
                if mod not in os.listdir(mods_dir):
                    logging.info(f"Скачивание мода: {mod}")
                    self.file_download(f"https://github.com/Homanti/wacominecraft/raw/main/mods/{mod}", mods_dir, f"модов: {mod}")

            remove_file(AUTHLIB_DIR + "/authlib-injector-1.2.5.jar")
            self.install_authlib_injector()

            minecraft_version["mods"] = latest_list_mods
            self.write_json(MINECRAFT_VERSION_FILE, minecraft_version)
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            self.enable_launch_button()

    def install_authlib_injector(self):
        try:
            self.disable_launch_button()

            self.file_download(f"https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.5/authlib-injector-1.2.5.jar", AUTHLIB_DIR, f"модов: authlib-injector-1.2.5.jar")
        except Exception as e:
            self.show_info_message("Ошибка", f"Ошибка при установке authlib-injector: {e}")
        finally:
            self.enable_launch_button()

    def install_rp(self):
        try:
            minecraft_version = self.read_json(MINECRAFT_VERSION_FILE)
            latest_minecraft_version = self.read_json("https://pastebin.com/raw/70N3V9Nj")
            latest_rp_version = latest_minecraft_version["rp_version"]

            self.disable_launch_button()

            remove_file(MINECRAFT_DIR + "/resourcepacks/WacoRP.zip")
            self.file_download(url="https://github.com/Homanti/wacominecraft/raw/main/WacoRP.zip", folder_path=MINECRAFT_DIR + "/resourcepacks", download_name="ресурс пака")

            minecraft_version["rp_version"] = latest_rp_version
            self.write_json(MINECRAFT_VERSION_FILE, minecraft_version)
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            self.enable_launch_button()

    def install_pointblank(self):
        try:
            minecraft_version = self.read_json(MINECRAFT_VERSION_FILE)
            latest_minecraft_version = self.read_json("https://pastebin.com/raw/70N3V9Nj")
            latest_pointblank_version = latest_minecraft_version["pointblank"]

            self.disable_launch_button()

            remove_directory(MINECRAFT_DIR + "/pointblank")
            self.file_download(url="https://github.com/Homanti/wacominecraft/raw/main/pointblank.zip", folder_path=MINECRAFT_DIR + "/pointblank", download_name="ресурс пака")

            with zipfile.ZipFile(MINECRAFT_DIR + "/pointblank/pointblank.zip", 'r') as zip_ref:
                zip_ref.extractall(MINECRAFT_DIR)

            remove_file(MINECRAFT_DIR + "/pointblank/pointblank.zip")

            minecraft_version["pointblank"] = latest_pointblank_version
            self.write_json(MINECRAFT_VERSION_FILE, minecraft_version)
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            self.enable_launch_button()

    def check_minecraft_installation(self):
        return os.path.exists(MINECRAFT_DIR + f"/versions/{MINECRAFT_VERSION}-forge-{FORGE_VERSION}/{MINECRAFT_VERSION}-forge-{FORGE_VERSION}.jar")

    def check_authlib_injector_installation(self):
        return os.path.exists(AUTHLIB_DIR + "/authlib-injector-1.2.5.jar")

    def check_mods_installation(self):
        list_mods = self.read_json(MINECRAFT_VERSION_FILE)["mods"]
        latest_list_mods = self.read_json("https://github.com/Homanti/wacominecraft/raw/main/mods.json")["mods"]

        if list_mods == latest_list_mods:
            for mod in latest_list_mods:
                mod_path = os.path.join(MINECRAFT_DIR, "mods", mod)
                if not os.path.exists(mod_path):
                    return False

            return True

        return False

    def check_rp_installation(self):
        rp_version = self.read_json(MINECRAFT_VERSION_FILE)["rp_version"]
        latest_minecraft_version = self.read_json("https://pastebin.com/raw/70N3V9Nj")["rp_version"]

        return rp_version == latest_minecraft_version and os.path.exists(MINECRAFT_DIR + "/resourcepacks/WacoRP.zip")

    def check_pointblank_installation(self):
        pointblank_version = self.read_json(MINECRAFT_VERSION_FILE)["rp_version"]
        latest_pointblank_version = self.read_json("https://pastebin.com/raw/70N3V9Nj")["rp_version"]

        if pointblank_version and latest_pointblank_version:
            return pointblank_version == latest_pointblank_version and os.path.exists(MINECRAFT_DIR + "/pointblank")
        return False

    def start_minecraft(self):
        if self.check_minecraft_installation() and self.check_mods_installation() and self.check_rp_installation() and self.check_pointblank_installation() and self.check_authlib_injector_installation():
            settings = self.read_json("data/settings.json")
            account = self.get_active_account()

            if account["status_code"] == 200:
                if account["result"][7]:
                    options = {
                        "username": account["result"][1],
                        "jvmArguments": [
                            f"-Xmx{settings['ram']}m",
                            f"-Xms{settings['ram']}m",
                            f"-javaagent:{AUTHLIB_DIR}/authlib-injector-1.2.5.jar={AUTHAPI_URL}"
                        ],
                        "uuid": account["result"][8],
                        "token": account["result"][9]
                    }

                    self.launched = True
                    self.disable_button("btn_play", True)
                    self.change_innerHTML("btn_play", "Запуск...")
                    try:
                        start_minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(f"{MINECRAFT_VERSION}-forge-{FORGE_VERSION}", MINECRAFT_DIR, options=options)
                        logging.info(f"Запуск Minecraft: {start_minecraft_command}")

                        with open("minecraft_logs.txt", "w") as file:
                            subprocess.run(start_minecraft_command, stdout=file, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

                    except Exception as e:
                        self.show_info_message("Ошибка", f"Ошибка запуска Minecraft: {e}")

                    self.launched = False
                    self.disable_button("btn_play", False)
                    self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')
                else:
                    self.show_info_message("Ошибка", "Ваша заявка еще не одобрена. Ожидайте сообщение в Discord.")

            elif account["status_code"] == 401:
                self.show_info_message("Ошибка", "Неверный логин или пароль")

            elif account["status_code"] == 502:
                self.show_info_message("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.")

        else:
            if not self.check_minecraft_installation():
                self.install_minecraft()

            if not self.check_authlib_injector_installation():
                self.install_authlib_injector()

            if not self.check_mods_installation():
                self.install_mods()

            if not self.check_rp_installation():
                self.install_rp()

            if not self.check_pointblank_installation():
                self.install_pointblank()

    def get_max_ram(self):
        memory_info = psutil.virtual_memory()
        return round(memory_info.total / (1024 ** 2))\

    def reinstall(self, download_name):
        if download_name == "minecraft":
            remove_directory(MINECRAFT_DIR)
            self.load_tab("index")
            self.change_innerHTML("btn_play", "Установить")

        elif download_name == "mods":
            remove_directory(MINECRAFT_DIR + "/mods")
            self.load_tab("index")
            self.change_innerHTML("btn_play", "Установить")

        elif download_name == "rp":
            remove_file(MINECRAFT_DIR + "/resourcepacks/WacoRP.zip")
            remove_file(MINECRAFT_DIR + "/pointblank")
            self.load_tab("index")
            self.change_innerHTML("btn_play", "Установить")

    def set_server_online(self):
        while True:
            if self.tab_name == "index" or self.tab_name == "settings":
                try:
                    server = JavaServer.lookup(SERVER_IP)
                    self.server_status = server.status()

                    self._window.evaluate_js(f"""
                    const players_online = document.getElementById('players_online').textContent = "Игроков онлайн: {self.server_status.players.online}"
                    """)
                except:
                    self.server_status = False
                    self._window.evaluate_js(f"""
                    const players_online = document.getElementById('players_online').textContent = "Сервер выключен"
                    """)

            time.sleep(5)

    def update_launcher(self):
        launcher_version_hash = self.read_json("data/launcher_version_hash.json")
        latest_launcher_version_hash = get_latest_commit_sha("Homanti/wacolauncher", "build_launcher/wacolauncher.zip")

        if launcher_version_hash is None:
            self.write_json("data/launcher_version_hash.json", {"launcher_version_hash": None})
            launcher_version_hash = self.read_json("data/launcher_version_hash.json")

        if not os.path.exists("wacolauncher/wacolauncher.exe") or latest_launcher_version_hash != launcher_version_hash["launcher_version_hash"]:
            self._window.show()
            remove_directory("wacolauncher")

            self.file_download(f"https://github.com/Homanti/wacolauncher/raw/main/build_launcher/wacolauncher.zip", "wacolauncher", "лаунчера")

            with zipfile.ZipFile("wacolauncher/wacolauncher.zip") as zip_ref:
                zip_ref.extractall("wacolauncher")

            remove_file("wacolauncher/wacolauncher.zip")
            launcher_version_hash["launcher_version_hash"] = latest_launcher_version_hash

        self._window.hide()
        self.write_json("data/launcher_version_hash.json", launcher_version_hash)

        exe_path = os.path.abspath("wacolauncher/wacolauncher.exe")

        subprocess.Popen([exe_path], shell=True)
        self._window.destroy()
