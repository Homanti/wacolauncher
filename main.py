import asyncio
import base64
import json
import webbrowser
import io

import aiohttp
import webview
import os
import requests
from PIL import Image


def createFolderIfNeeded(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        print(f"Папка {folder_name} создана")

createFolderIfNeeded("data")

def readJson(filename):  # чтение json файлов
    if filename.startswith('http://'):
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

def writeJson(filename, data):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Файл {filename} создан или изменен")
    except Exception as e:
        print(f"Ошибка при обработке файла {filename}: {e}, информация которая записывалась в файл {data}")

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
        writeJson("data/credentials.json", data)
    except Exception as e:
        print(f"Ошибка при обработке файла data/credentials.json: {e}, информация которая записывалась в файл {new_account_data}")


class Api:
    def load_tab(self, html_name):
        window.load_url(f'file://{os.path.abspath("web/" + html_name)}')

    def account_login(self, nickname, password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "login", "nickname": nickname, "password": password}
        )

        if response.status_code == 200:
            save_account(response.json()["result"][1], response.json()["result"][2])
            return response.json()["result"]

        elif response.status_code == 401:
            data = readJson("data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == nickname and item['password'] == password)]
                writeJson("data/credentials.json", data)

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
        data = readJson("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    return self.account_login(item['nickname'], item['password'])

    def open_link(self, url):
        webbrowser.open(url)

    def get_accounts(self):
        return readJson("data/credentials.json")

    def get_account_id(self):
        data = readJson("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    return self.account_login(item['nickname'], item['password'])

    def check_login(self):
        data = readJson("data/credentials.json")
        if data:
            for item in data:
                if item['active']:
                    result = self.account_login(item['nickname'], item['password'])
                    if isinstance(result, list):
                        if result[3]:
                            self.load_tab("index.html")
                        else:
                            self.load_tab("link_discord_register.html")

    def update_password(self, nickname, password, new_password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "update_password", "nickname": nickname, "password": password, "new_password": new_password}
        )

        if response.status_code == 200:
            save_account(nickname, new_password)
            return 200

        elif response.status_code == 401:
            data = readJson("data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == nickname and item['password'] == password)]
                writeJson("data/credentials.json", data)

            print(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502


if __name__ == '__main__':
    api = Api()
    window = webview.create_window(title="WacoLauncher", url="web/login.html", width=1296, height=809, js_api=api, resizable=False, fullscreen=False)
    webview.start(api.check_login, debug=True)