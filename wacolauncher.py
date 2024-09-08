import asyncio
import base64
import json
import shutil
import subprocess
import webbrowser
import io
import zipfile
from urllib.parse import urlsplit
import aiohttp
import psutil
import webview
import os
import requests
from PIL import Image
import minecraft_launcher_lib

appdata_path = os.path.expandvars('%APPDATA%')
minecraft_dir = appdata_path + "/.wacorp"
downloading = False
launched = False
skin_settings = {
    "version": "14.20",
    "buildNumber": 27,
    "loadlist": [
        {
            "name": "Github",
            "skin": "https://github.com/Homanti/wacoskins/blob/main/{USERNAME}_skin.png?raw=true"
        }
    ],
    "enableDynamicSkull": True,
    "enableTransparentSkin": False,
    "forceLoadAllTextures": True,
    "enableCape": True,
    "threadPoolSize": 8,
    "enableLogStdOut": False,
    "cacheExpiry": 30,
    "forceUpdateSkull": False,
    "enableLocalProfileCache": False,
    "enableCacheAutoClean": False,
    "forceDisableCache": False
}

def createFolderIfNeeded(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        print(f"Папка {folder_name} создана")

createFolderIfNeeded("data")
createFolderIfNeeded(minecraft_dir)

def save_account(nickname, password):
    new_account_data = {
        "nickname": nickname,
        "password": password,
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
                    if account["password"] != password:
                        account["password"] = password
                        print(f"Пароль для аккаунта с ником {nickname} был обновлен.")
                    else:
                        print(f"Аккаунт с ником {nickname} уже существует с таким же паролем.")
                    account["active"] = True
                    updated = True
                else:
                    account["active"] = False

            if not updated:
                for account in data:
                    account["active"] = False
                data.append(new_account_data)

        # Сохраняем изменения обратно в credentials.json
        Api().writeJson("data/credentials.json", data)
    except Exception as e:
        print(f"Ошибка при обработке файла data/credentials.json: {e}, информация которая записывалась в файл {new_account_data}")

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

        if total_length is None:
            if what:
                api.progress_bar_set(0, what)
        else:
            dl = 0
            total_length = int(total_length)
            with open(file_path, 'wb') as file:
                for data in response.iter_content(chunk_size=4096):
                    downloading = True
                    dl += len(data)
                    file.write(data)
                    progress = round(dl / total_length * 100, 2)
                    if what:
                        api.progress_bar_set(progress, what)

            print(f"Файл успешно загружен и сохранен в {file_path}.")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка загрузки файла: {e}")
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
        print(f"Файл {filepath} успешно удален.")
    except FileNotFoundError:
        print(f"Файл {filepath} не найден.")
    except Exception as e:
        print(f"Ошибка при удалении файла {filepath}: {e}")

def remove_directory(dirpath):
    try:
        shutil.rmtree(dirpath)
        print(f"Директория {dirpath} и все ее содержимое успешно удалены.")
    except FileNotFoundError:
        print(f"Директория {dirpath} не найдена.")
    except Exception as e:
        print(f"Ошибка при удалении директории {dirpath}: {e}")

class Api:
    def load_tab(self, html_name):
        window.load_url(f"web/{html_name}")
        if html_name == "index.html" and downloading:
            self.open_progress_bar(True)
            self.disable_button("btn_play", True)

        elif html_name == "index.html" and launched:
            self.disable_button("btn_play", True)
            self.change_innerHTML("btn_play", "Запущено")

    def readJson(self, filename):  # чтение json файлов
        if filename.startswith('https://') or filename.startswith('http://'):
            try:
                response = requests.get(filename)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Ошибка при запросе к {filename}: {e}")
                return None
        else:
            try:
                with open(filename, "r") as json_file:
                    return json.load(json_file)
            except FileNotFoundError:
                print(f"Файл {filename} не найден")
                return None
            except json.JSONDecodeError:
                print(f"Ошибка декодирования JSON в файле {filename}")
                return None

    def writeJson(self, filename, data):
        try:
            with open(filename, "w") as json_file:
                json.dump(data, json_file, indent=4)
            print(f"Файл {filename} создан или изменен")
        except Exception as e:
            print(f"Ошибка при обработке файла {filename}: {e}, информация которая записывалась в файл {data}")

    def account_login(self, nickname, password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "login", "nickname": nickname, "password": password}
        )

        if response.status_code == 200:
            save_account(response.json()["result"][1], response.json()["result"][2])
            return response.json()["result"]

        elif response.status_code == 401:
            data = self.readJson("data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == nickname and item['password'] == password)]
                self.writeJson("data/credentials.json", data)

            print(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    async def upload_skin(self, nickname, password, skin_bytes):
        result = self.account_login(nickname, password)

        if isinstance(result, list):
            skin_bytes = bytes(skin_bytes)
            image = Image.open(io.BytesIO(skin_bytes))

            head_box = (8, 8, 16, 16)
            head = image.crop(head_box)
            head = head.resize((40, 40), Image.Resampling.LANCZOS)

            async with aiohttp.ClientSession() as session:
                for file_suffix, img in zip(["skin", "head"], [image, head]):
                    image_file = io.BytesIO()
                    img.save(image_file, format='PNG')
                    image_file.seek(0)

                    encoded_image = base64.b64encode(image_file.getvalue()).decode('utf-8')

                    headers = {
                        'Authorization': f'token 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',
                        'Accept': 'application/vnd.github.v3+json',
                    }

                    upload_url = f'https://api.github.com/repos/Homanti/wacoskins/contents/{nickname}_{file_suffix}.png'

                    # Получаем существующий файл
                    async with session.get(upload_url, headers=headers) as response_check:
                        if response_check.status == 200:
                            file_info = await response_check.json()
                            sha = file_info['sha']

                            # Если файл существует, удаляем его
                            delete_data = {
                                'message': f'Delete existing {file_suffix} image',
                                'sha': sha,
                                'branch': 'main'
                            }
                            async with session.delete(upload_url, headers=headers, json=delete_data) as response_delete:
                                if response_delete.status in (200, 204):
                                    print(f"Existing {file_suffix} image deleted successfully.")
                                else:
                                    print(f"Failed to delete existing {file_suffix} image: {response_delete.status} - {await response_delete.json()}")

                    # Загрузка нового изображения
                    data = {
                        'message': f'Upload {file_suffix} image',
                        'content': encoded_image,
                        'branch': 'main'
                    }

                    async with session.put(upload_url, headers=headers, json=data) as response_upload:
                        if response_upload.status in (201, 200):
                            print(f"{file_suffix.capitalize()} image uploaded successfully.")
                        else:
                            print(f"Image upload failed: {response_upload.status} - {await response_upload.json()}")

        return True

    def start_upload_skin(self, nickname, password, skin_bytes):
        return asyncio.run(self.upload_skin(nickname, password, skin_bytes))

    def account_register(self, nickname, password, rp_history, how_did_you_find, skin_bytes):
        response = requests.post("https://wacodb-production.up.railway.app/database/", json={
            "action": "register",
            "nickname": nickname,
            "password": password,
            "rp_history": rp_history,
            "how_did_you_find": how_did_you_find
        })

        if response.status_code == 200:
            self.start_upload_skin(nickname, password, skin_bytes)
            return self.account_login(nickname, password)
        else:
            print(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
            return 502

    def check_discord_link(self):
        data = self.readJson("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    return self.account_login(item['nickname'], item['password'])

    def open_link(self, url):
        webbrowser.open(url)

    def get_accounts(self):
        return self.readJson("data/credentials.json")

    def get_account_id(self):
        data = self.readJson("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    return self.account_login(item['nickname'], item['password'])

    def check_login(self):
        data = self.readJson("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    result = self.account_login(item['nickname'], item['password'])
                    if isinstance(result, list):
                        if result[3]:
                            return "index.html"
                        else:
                            return "link_discord_register.html"
        return "login.html"

    def update_password(self, nickname, password, new_password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "update_password", "nickname": nickname, "password": password, "new_password": new_password}
        )

        if response.status_code == 200:
            save_account(nickname, new_password)
            return 200

        elif response.status_code == 401:
            print(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    def delete_account(self, nickname, password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "delete", "nickname": nickname, "password": password}
        )

        if response.status_code == 200:
            data = self.readJson("data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == nickname and item['password'] == password)]
                self.writeJson("data/credentials.json", data)
            return 200

        elif response.status_code == 401:
            print(f"Login failed: {response.json()['detail']}")
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

        minecraft_launcher_lib.forge.install_forge_version("1.20.1-47.3.7", minecraft_dir, callback=callback)
        downloading = False
        self.open_progress_bar(False)
        self.disable_button("btn_play", False)
        self.disable_button("profile_button", False)
        self.disable_button("btn_settings", False)
        self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')
        api.writeJson(minecraft_dir + "/minecraft_version.json", {"mods": [], "rp_version": None, "pointblank": None})

        with open(minecraft_dir + "/options.txt", "w", encoding="utf-8") as file:
            response = requests.get("https://pastebin.com/raw/ntDpjK0L")
            file.write(response.text)

    def install_mods(self):
        global downloading

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
                print(f"Удален мод: {mod}")

        for mod in mods_to_install:
            mod_path = os.path.join(mods_dir, mod)
            if not os.path.exists(mod_path):
                print(f"Скачивание мода: {mod}")
                file_download(f"https://github.com/Homanti/wacominecraft/raw/main/mods/{mod}", mods_dir, f"модов: {mod}")

        for mod in latest_list_mods:
            if mod not in os.listdir(mods_dir):
                print(f"Скачивание мода: {mod}")
                file_download(f"https://github.com/Homanti/wacominecraft/raw/main/mods/{mod}", mods_dir, f"модов: {mod}")

        downloading = False
        self.open_progress_bar(False)
        self.disable_button("btn_play", False)
        self.disable_button("profile_button", False)
        self.disable_button("btn_settings", False)
        self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

        minecraft_version["mods"] = latest_list_mods
        self.writeJson(minecraft_dir + "/minecraft_version.json", minecraft_version)

    def install_rp(self):
        global downloading

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

        downloading = False
        self.open_progress_bar(False)
        self.disable_button("btn_play", False)
        self.disable_button("profile_button", False)
        self.disable_button("btn_settings", False)
        self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

        minecraft_version["rp_version"] = latest_rp_version
        self.writeJson(minecraft_dir + "/minecraft_version.json", minecraft_version)

    def install_pointblank(self):
        global downloading

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

        downloading = False
        self.open_progress_bar(False)
        self.disable_button("btn_play", False)
        self.disable_button("profile_button", False)
        self.disable_button("btn_settings", False)
        self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')

        minecraft_version["pointblank"] = latest_pointblank_version
        self.writeJson(minecraft_dir + "/minecraft_version.json", minecraft_version)

    def check_minecraft_installation(self):
        if os.path.exists(minecraft_dir + "/versions/1.20.1-forge-47.3.7/1.20.1-forge-47.3.7.jar"):
            return True
        else:
            return False

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
        if self.check_minecraft_installation() and self.check_mods_installation() and self.check_rp_installation() and self.check_pointblank_installation():
            data = self.readJson("data/credentials.json")
            settings = self.readJson("data/settings.json")

            if data:
                for item in data:
                    if item['active']:
                        createFolderIfNeeded(minecraft_dir + "/CustomSkinLoader")
                        account = self.account_login(item['nickname'], item['password'])

                        if isinstance(account, list):
                            if account[7]:
                                self.writeJson(minecraft_dir + "/CustomSkinLoader/CustomSkinLoader.json", skin_settings)
                                options = {
                                    "username": item['nickname'],
                                    "jvmArguments": [f"-Xmx{settings["ram"]}m", f"-Xms{settings["ram"]}m"]
                                }

                                launched = True
                                self.disable_button("btn_play", True)
                                self.change_innerHTML("btn_play", "Запущено")
                                subprocess.run(minecraft_launcher_lib.command.get_minecraft_command("1.20.1-forge-47.3.7", minecraft_dir, options=options))

                                launched = False
                                self.disable_button("btn_play", False)
                                self.change_innerHTML("btn_play", '<span class="material-icons icon-settings">play_arrow</span>Играть')
                            else:
                                self.show_info_message("Ошибка", "Ваша заявка еще не одобрена. Ожидайте сообщение в Discord.")

                        elif account == 401:
                            self.show_info_message("Ошибка", "Неверный логин или пароль")

                        elif account == 502:
                            self.show_info_message("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.")

        else:
            if not self.check_minecraft_installation():
                self.install_minecraft()

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
            self.load_tab("index.html")
            self.change_innerHTML("btn_play", "Установить")

        elif what == "mods":
            remove_directory(minecraft_dir + "/mods")
            self.load_tab("index.html")
            self.change_innerHTML("btn_play", "Установить")

        elif what == "rp":
            remove_file(minecraft_dir + "/resourcepacks/WacoRP.zip")
            self.load_tab("index.html")
            self.change_innerHTML("btn_play", "Установить")

if __name__ == '__main__':
    api = Api()

    settings = api.readJson("data/settings.json")
    minecraft_version = api.readJson(minecraft_dir + "/minecraft_version.json")

    if not settings or not settings["ram"]:
        memory_info = psutil.virtual_memory()
        api.writeJson("data/settings.json", {"ram": (round(memory_info.total / (1024 ** 2) / 2))})

    if minecraft_version is None:
        api.writeJson(minecraft_dir + "/minecraft_version.json", {"mods": [], "rp_version": None, "pointblank": None})

    window = webview.create_window(title="WacoLauncher", url=f"web/{api.check_login()}", width=1296, height=809, js_api=api, resizable=False, fullscreen=False)
    webview.start(debug=True)