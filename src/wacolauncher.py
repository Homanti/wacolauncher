import json
import shutil
import subprocess
import threading
import time
import webbrowser
import zipfile
import io
from urllib.parse import urlsplit
import keyring
import psutil
import webview
import os
import requests
import minecraft_launcher_lib
from mcstatus import JavaServer
import logging
import sys

def setup_logging(log_file="launcher_logs.txt"):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

setup_logging()
logging.getLogger("urllib3").setLevel(logging.WARNING)

appdata_path = os.path.expandvars('%APPDATA%')
minecraft_dir = appdata_path + "/.wacorp"
authlib_dir = minecraft_dir + "/libraries/com/mojang/authlib"
downloading = False
launched = False
tab = None
server_status = None

# skin_settings = {
#     "version": "14.20",
#     "buildNumber": 27,
#     "loadlist": [
#         {
#             "name": "Github",
#             "type": "Legacy",
#             "checkPNG": False,
#             "skin": "https://raw.githubusercontent.com/Homanti/wacoskins/main/{USERNAME}_skin.png",
#             "model": "auto"
#         }
#     ],
#     "enableDynamicSkull": True,
#     "enableTransparentSkin": False,
#     "forceLoadAllTextures": True,
#     "enableCape": True,
#     "threadPoolSize": 8,
#     "enableLogStdOut": False,
#     "cacheExpiry": 30,
#     "forceUpdateSkull": False,
#     "enableLocalProfileCache": False,
#     "enableCacheAutoClean": False,
#     "forceDisableCache": False
# }

def createFolderIfNeeded(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        logging.info(f"Папка {folder_name} создана")

createFolderIfNeeded("data")
createFolderIfNeeded(minecraft_dir)
createFolderIfNeeded(authlib_dir)

def save_account(nickname, password):
    api = Api()
    api.set_password(nickname, password)
    new_account_data = {
        "nickname": nickname,
        "active": True,
    }
    try:
        try:
            with open("../data/credentials.json", "r") as json_file:
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

        api.writeJson("data/credentials.json", data)
    except Exception as e:
        logging.error(f"Ошибка при обработке файла data/credentials.json: {e}")

def file_download(url, folder_path, what = None):
    global downloading
    os.makedirs(folder_path, exist_ok=True)

    api = Api()

    try:
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        if 'Content-Disposition' in response.headers:
            filename = response.headers.get('Content-Disposition').split('filename=')[-1].strip('"')
        else:
            filename = os.path.basename(urlsplit(url).path)

        file_path = os.path.join(folder_path, filename)
        downloading = True

        if total_length is None:
            if what:
                api.progress_bar_set(0, what)
        else:
            dl = 0
            total_length = int(total_length)
            with open(file_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    file.write(data)
                    progress = round(dl / total_length * 100, 2)

                    if what:
                        api.progress_bar_set(progress, what)

            logging.info(f"Файл успешно загружен и сохранен в {file_path}.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка загрузки файла: {e}")
        return False

    downloading = False
    return True

def show_minecraft_install_progress(progress, total, status):
    percent = float((progress / total) * 100)

    if "Download" in status:
        status = status.replace("Download", "")

    api = Api()
    api.open_progress_bar(True)
    api.progress_bar_set(percent, "Minecraft: " + status)

def remove_file(filepath):
    try:
        os.remove(filepath)
        logging.info(f"Файл {filepath} успешно удален.")
    except FileNotFoundError:
        logging.warning(f"Файл {filepath} не найден.")
    except Exception as e:
        logging.error(f"Ошибка при удалении файла {filepath}: {e}")

def remove_directory(dirpath):
    try:
        shutil.rmtree(dirpath)
        logging.info(f"Директория {dirpath} и все ее содержимое успешно удалены.")
    except FileNotFoundError:
        logging.warning(f"Директория {dirpath} не найдена.")
    except Exception as e:
        logging.error(f"Ошибка при удалении директории {dirpath}: {e}")

class Api:
    def load_tab(self, html_name, info_message_title = None, info_message_text = None):
        global tab
        tab = html_name
        window.load_url(f"https://wacolauncher-web-production.up.railway.app/{html_name}")

        if html_name == "index" or html_name == "settings":
            if server_status:
                window.evaluate_js(f"""
                const players_online = document.getElementById('players_online').textContent = "Игроков онлайн: {server_status.players.online}"
                """)
            else:
                window.evaluate_js(f"""
                const players_online = document.getElementById('players_online').textContent = "Сервер выключен"
                """)

        if html_name == "index" and downloading:
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)

        elif html_name == "index" and launched:
            self.disable_button("btn_play", True)
            self.change_innerHTML("btn_play", "Запущено")

        if info_message_title and info_message_text:
            self.show_info_message(info_message_title, info_message_text)

    def readJson(self, filename):  # чтение json файлов
        if filename.startswith('https://') or filename.startswith('http://'):
            try:
                response = requests.get(filename)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                logging.error(f"Ошибка при запросе к {filename}: {e}")
                return None
        else:
            try:
                with open(filename, "r") as json_file:
                    return json.load(json_file)
            except FileNotFoundError:
                logging.warning(f"Файл {filename} не найден")
                return None
            except json.JSONDecodeError:
                logging.error(f"Ошибка декодирования JSON в файле {filename}")
                return None

    def writeJson(self, filename, data):
        try:
            with open(filename, "w") as json_file:
                json.dump(data, json_file, indent=4)
            logging.info(f"Файл {filename} создан или изменен")
        except Exception as e:
            logging.error(f"Ошибка при обработке файла {filename}: {e}, информация которая записывалась в файл {data}")

    def set_password(self, nickname, password):
        keyring.set_password("WacoLauncher", nickname, password)

    def get_password(self, nickname):
        return keyring.get_password("WacoLauncher", nickname)

    def account_login(self, nickname, password):
        response = requests.post(
            "https://wacoapi-production.up.railway.app/database/login",
            params={"nickname": nickname, "password": password},
        )

        if response.status_code == 200:
            save_account(response.json()["result"][1], response.json()["result"][2])
            return {"status_code": 200, "result": response.json()["result"]}

        elif response.status_code == 401:
            data = self.readJson("../data/credentials.json")

            if data:
                data = [item for item in data if item['nickname'] != nickname]
                self.writeJson("../data/credentials.json", data)

            logging.error(f"Login failed: {response.json()['detail']}")
            return {"status_code": 401}

        return {"status_code": response.status_code}

    def account_register(self, nickname, password, rp_history, how_did_you_find, skin_bytes):
        skin_file = io.BytesIO(bytes(skin_bytes))
        skin_file.name = f'{nickname}_skin.png'

        response = requests.post(
            "https://wacoapi-production.up.railway.app/database/register",
            params={
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
            "https://wacoapi-production.up.railway.app/database/update_skin",
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
        data = self.readJson("../data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    nickname = item['nickname']
                    password = self.get_password(nickname)
                    if password:
                        return self.account_login(nickname, password)
        return None

    def check_login(self):
        global tab
        data = self.readJson("../data/credentials.json")
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
                                    tab = "link_discord_register"
                                    return tab
                                else:
                                    tab = "index"
                                    return "index"
                            else:
                                tab = "login"
                                return tab
            else:
                tab = "login"
                return tab
        except:
            tab = "login"
            return tab

    def update_password(self, nickname, password, new_password):
        response = requests.post(
            "https://wacoapi-production.up.railway.app/database/update_password",
            params={"action": "update_password", "nickname": nickname, "password": password, "new_password": new_password}
        )

        if response.status_code == 200:
            save_account(nickname, new_password)
            return 200

        elif response.status_code == 401:
            logging.error(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    def delete_account(self, nickname, password):
        response = requests.post(
            "https://wacoapi-production.up.railway.app/database/",
            params={"action": "delete", "nickname": nickname, "password": password}
        )

        if response.status_code == 200:
            data = self.readJson("../data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == nickname and item['password'] == password)]
                self.writeJson("../data/credentials.json", data)
            return 200

        elif response.status_code == 401:
            logging.error(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    def progress_bar_set(self, percent, what):
        window.evaluate_js(f"""
        document.getElementById('progress_bar').style.width = '{percent}%';
        document.getElementById('progress_text').textContent = 'Установка ' + {json.dumps(what)} + '... {round(percent, 2)}%';
        """)

    def open_progress_bar(self, status):
        if status:
            window.evaluate_js(f"""
            const progressBarContainer = document.querySelector('.progress-bar-container');
            progressBarContainer.style.marginTop = '-30px';
            """)
        else:
            window.evaluate_js(f"""
            const progressBarContainer = document.querySelector('.progress-bar-container');
            progressBarContainer.style.marginTop = '0';
            """)

    def disable_button(self, button_id, status):
        if status:
            status = "true"
            if button_id == "profile_button":
                window.evaluate_js(f"""
                document.getElementById('profile_button').onclick = null;
                """)
        else:
            status = "false"
            if button_id == "profile_button":
                window.evaluate_js(f"""
                document.getElementById('profile_button').onclick = toggleDropdown;
                """)

        window.evaluate_js(f"""
        document.getElementById('{button_id}').disabled = {status};
        """)

    def change_innerHTML(self, element_id, innerHTML):
        window.evaluate_js(f"""
        document.getElementById('{element_id}').innerHTML = '{innerHTML}';
        """)

    def show_info_message(self, title, text):
        window.evaluate_js(f"""
        show_info_modal('{title}', '{text}');
        """)

    def install_minecraft(self):
        global downloading
        try:
            max_value = [0]
            status = [0]
            downloading = True
            self.disable_button("btn_play", True)
            self.disable_button("profile_button", True)
            self.disable_button("btn_settings", True)
            self.change_innerHTML("btn_play", 'Установка...')

            callback = {
                "setStatus": lambda value: status.__setitem__(0, value),
                "setProgress": lambda value: show_minecraft_install_progress(value, max_value[0], status[0]),
                "setMax": lambda value: max_value.__setitem__(0, value)
            }

            minecraft_launcher_lib.forge.install_forge_version("1.20.1-47.3.12", minecraft_dir, callback=callback)

            api.writeJson(minecraft_dir + "/minecraft_version.json", {"mods": [], "rp_version": None, "pointblank": None})

            with open(minecraft_dir + "/options.txt", "w", encoding="utf-8") as file:
                options = (
                    'resourcePacks:["vanilla","pointblank_resources","pfm-asset-resources","mod_resources","file/WacoRP.zip"]\n'
                    'lastServer:\n'
                    'lang:ru_ru\n'
                )
                file.write(options)

            file_download("https://github.com/Homanti/wacominecraft/raw/refs/heads/main/servers.dat", minecraft_dir, "Minecraft")
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            downloading = False
            self.open_progress_bar(False)
            self.disable_button("btn_play", False)
            self.disable_button("profile_button", False)
            self.disable_button("btn_settings", False)
            self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

    def install_mods(self):
        global downloading

        try:
            minecraft_version = self.readJson(minecraft_dir + "/minecraft_version.json")
            latest_minecraft_version = self.readJson("https://raw.githubusercontent.com/Homanti/wacominecraft/main/mods.json")

            list_mods = minecraft_version["mods"]
            latest_list_mods = latest_minecraft_version["mods"]

            downloading = True
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)
            self.disable_button("profile_button", True)
            self.disable_button("btn_settings", True)
            self.change_innerHTML("btn_play", 'Установка...')

            mods_dir = os.path.join(minecraft_dir, "mods")

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
                    file_download(f"https://github.com/Homanti/wacominecraft/raw/main/mods/{mod}", mods_dir, f"модов: {mod}")

            for mod in latest_list_mods:
                if mod not in os.listdir(mods_dir):
                    logging.info(f"Скачивание мода: {mod}")
                    file_download(f"https://github.com/Homanti/wacominecraft/raw/main/mods/{mod}", mods_dir, f"модов: {mod}")

            remove_file(authlib_dir + "/authlib-injector-1.2.5.jar")
            self.install_authlib_injector()

            minecraft_version["mods"] = latest_list_mods
            self.writeJson(minecraft_dir + "/minecraft_version.json", minecraft_version)
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            downloading = False
            self.open_progress_bar(False)
            self.disable_button("btn_play", False)
            self.disable_button("profile_button", False)
            self.disable_button("btn_settings", False)
            self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

    def install_authlib_injector(self):
        global downloading
        try:
            downloading = True
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)
            self.disable_button("profile_button", True)
            self.disable_button("btn_settings", True)
            self.change_innerHTML("btn_play", 'Установка...')

            file_download(f"https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.5/authlib-injector-1.2.5.jar", authlib_dir, f"модов: authlib-injector-1.2.5.jar")
        except Exception as e:
            self.show_info_message("Ошибка", f"Ошибка при установке authlib-injector: {e}")
        finally:
            downloading = False
            self.open_progress_bar(False)
            self.disable_button("btn_play", False)
            self.disable_button("profile_button", False)
            self.disable_button("btn_settings", False)
            self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

    def install_rp(self):
        global downloading
        try:
            minecraft_version = self.readJson(minecraft_dir + "/minecraft_version.json")
            latest_minecraft_version = self.readJson("https://pastebin.com/raw/70N3V9Nj")
            latest_rp_version = latest_minecraft_version["rp_version"]

            downloading = True
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)
            self.disable_button("profile_button", True)
            self.disable_button("btn_settings", True)
            self.change_innerHTML("btn_play", 'Установка...')

            remove_file(minecraft_dir + "/resourcepacks/WacoRP.zip")
            file_download(url="https://github.com/Homanti/wacominecraft/raw/main/WacoRP.zip", folder_path=minecraft_dir + "/resourcepacks", what="ресурс пака")

            minecraft_version["rp_version"] = latest_rp_version
            self.writeJson(minecraft_dir + "/minecraft_version.json", minecraft_version)
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            downloading = False
            self.open_progress_bar(False)
            self.disable_button("btn_play", False)
            self.disable_button("profile_button", False)
            self.disable_button("btn_settings", False)
            self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

    def install_pointblank(self):
        global downloading
        try:
            minecraft_version = self.readJson(minecraft_dir + "/minecraft_version.json")
            latest_minecraft_version = self.readJson("https://pastebin.com/raw/70N3V9Nj")
            latest_pointblank_version = latest_minecraft_version["pointblank"]

            downloading = True
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)
            self.disable_button("profile_button", True)
            self.disable_button("btn_settings", True)
            self.change_innerHTML("btn_play", 'Установка...')

            remove_directory(minecraft_dir + "/pointblank")
            file_download(url="https://github.com/Homanti/wacominecraft/raw/main/pointblank.zip", folder_path=minecraft_dir + "/pointblank", what="ресурс пака")

            with zipfile.ZipFile(minecraft_dir + "/pointblank/pointblank.zip", 'r') as zip_ref:
                zip_ref.extractall(minecraft_dir)

            remove_file(minecraft_dir + "/pointblank/pointblank.zip")

            minecraft_version["pointblank"] = latest_pointblank_version
            self.writeJson(minecraft_dir + "/minecraft_version.json", minecraft_version)
        except Exception as e:
            self.show_info_message("Ошибка", f"Произошла непредвиденная ошибка {e}. Попробуйте еще раз.")
        finally:
            downloading = False
            self.open_progress_bar(False)
            self.disable_button("btn_play", False)
            self.disable_button("profile_button", False)
            self.disable_button("btn_settings", False)
            self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

    def check_minecraft_installation(self):
        return os.path.exists(minecraft_dir + "/versions/1.20.1-forge-47.3.12/1.20.1-forge-47.3.12.jar")

    def check_authlib_injector_installation(self):
        return os.path.exists(authlib_dir + "/authlib-injector-1.2.5.jar")

    def check_mods_installation(self):
        list_mods = self.readJson(minecraft_dir + "/minecraft_version.json")["mods"]
        latest_list_mods = self.readJson("https://github.com/Homanti/wacominecraft/raw/main/mods.json")["mods"]

        if list_mods == latest_list_mods:
            for mod in latest_list_mods:
                mod_path = os.path.join(minecraft_dir, "mods", mod)
                if not os.path.exists(mod_path):
                    return False

            return True

        return False

    def check_rp_installation(self):
        rp_version = self.readJson(minecraft_dir + "/minecraft_version.json")["rp_version"]
        latest_minecraft_version = self.readJson("https://pastebin.com/raw/70N3V9Nj")["rp_version"]

        return rp_version == latest_minecraft_version and os.path.exists(minecraft_dir + "/resourcepacks/WacoRP.zip")

    def check_pointblank_installation(self):
        pointblank_version = self.readJson(minecraft_dir + "/minecraft_version.json")["rp_version"]
        latest_pointblank_version = self.readJson("https://pastebin.com/raw/70N3V9Nj")["rp_version"]

        if pointblank_version and latest_pointblank_version:
            return pointblank_version == latest_pointblank_version and os.path.exists(minecraft_dir + "/pointblank")
        return False

    def start_minecraft(self):
        global launched
        if self.check_minecraft_installation() and self.check_mods_installation() and self.check_rp_installation() and self.check_pointblank_installation() and self.check_authlib_injector_installation():
            settings = self.readJson("../data/settings.json")
            account = self.get_active_account()

            # createFolderIfNeeded(minecraft_dir + "/CustomSkinLoader")

            if account["status_code"] == 200:
                if account["result"][7]:
                    # self.writeJson(minecraft_dir + "/CustomSkinLoader/CustomSkinLoader.json", skin_settings)
                    options = {
                        "username": account["result"][1],
                        "jvmArguments": [
                            f"-Xmx{settings['ram']}m",
                            f"-Xms{settings['ram']}m",
                            f"-javaagent:{authlib_dir}/authlib-injector-1.2.5.jar=https://wacoapi-production.up.railway.app"
                        ],
                        "uuid": account["result"][8],
                        "token": account["result"][9]
                    }

                    launched = True
                    self.disable_button("btn_play", True)
                    self.change_innerHTML("btn_play", "Запущено")
                    try:
                        start_minecraft_command = minecraft_launcher_lib.command.get_minecraft_command("1.20.1-forge-47.3.12", minecraft_dir, options=options)
                        logging.info(f"Запуск Minecraft: {start_minecraft_command}")

                        with open("../minecraft_logs.txt", "w") as file:
                            subprocess.run(start_minecraft_command, stdout=file, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

                    except Exception as e:
                        self.show_info_message("Ошибка", f"Ошибка запуска Minecraft: {e}")

                    launched = False
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

    def reinstall(self, what):
        if what == "minecraft":
            remove_directory(minecraft_dir)
            self.load_tab("index")
            self.change_innerHTML("btn_play", "Установить")

        elif what == "mods":
            remove_directory(minecraft_dir + "/mods")
            self.load_tab("index")
            self.change_innerHTML("btn_play", "Установить")

        elif what == "rp":
            remove_file(minecraft_dir + "/resourcepacks/WacoRP.zip")
            remove_file(minecraft_dir + "/pointblank")
            self.load_tab("index")
            self.change_innerHTML("btn_play", "Установить")

    def set_server_online(self):
        global server_status
        while True:
            if tab == "index" or tab == "settings":
                try:
                    server_ip = "m7.joinserver.xyz:25625"

                    server = JavaServer.lookup(server_ip)

                    server_status = server.status()

                    window.evaluate_js(f"""
                    const players_online = document.getElementById('players_online').textContent = "Игроков онлайн: {server_status.players.online}"
                    """)
                except:
                    server_status = False
                    window.evaluate_js(f"""
                    const players_online = document.getElementById('players_online').textContent = "Сервер выключен"
                    """)
            time.sleep(5)

if __name__ == '__main__':
    api = Api()

    settings = api.readJson("data/settings.json")
    minecraft_version = api.readJson(minecraft_dir + "/minecraft_version.json")

    if not settings or not settings["ram"]:
        memory_info = psutil.virtual_memory()
        api.writeJson("data/settings.json", {"ram": (round(memory_info.total / (1024 ** 2) / 2))})

    if minecraft_version is None:
        api.writeJson(minecraft_dir + "/minecraft_version.json", {"mods": [], "rp_version": None, "pointblank": None})

    threading.Thread(target=api.set_server_online, daemon=True).start()
    window = webview.create_window(title="WacoLauncher", url=f"https://wacolauncher-web-production.up.railway.app/{api.check_login()}", width=1296, height=809, js_api=api, resizable=False, fullscreen=False)
    webview.start(debug=False)