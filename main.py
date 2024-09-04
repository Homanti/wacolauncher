import base64
import json
import webbrowser
import io
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

def save_account(login, password):
    new_account_data = {
        "nickname": login,
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
                if account["nickname"] == login:
                    if account["password"] != password:
                        account["password"] = password
                        print(f"Пароль для аккаунта с ником {login} был обновлен.")
                    else:
                        print(f"Аккаунт с ником {login} уже существует с таким же паролем.")
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

    def account_register(self, nickname, password, rp_history, how_did_you_find, skin_bytes):
        skin_bytes = bytes(skin_bytes)

        # Отправляем данные для регистрации
        response = requests.post("https://wacodb-production.up.railway.app/database/", json={
            "action": "register",
            "nickname": nickname,
            "password": password,
            "rp_history": rp_history,
            "how_did_you_find": how_did_you_find
        })

        if response.status_code == 200:
            # Открываем изображение скина
            image = Image.open(io.BytesIO(skin_bytes))

            # Вырезаем голову (координаты для Minecraft-скина)
            head_box = (8, 8, 16, 16)
            head = image.crop(head_box)
            head = head.resize((40, 40), Image.Resampling.LANCZOS)

            # Сохраняем и полный скин, и голову
            for file_suffix, img in zip(["skin", "head"], [image, head]):
                # Сохраняем изображение в буфер
                image_file = io.BytesIO()
                img.save(image_file, format='PNG')
                image_file.seek(0)

                # Кодируем изображение в base64
                encoded_image = base64.b64encode(image_file.getvalue()).decode('utf-8')

                headers = {
                    'Authorization': f'token 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',
                    'Accept': 'application/vnd.github.v3+json',
                }

                # Проверяем, существует ли файл
                upload_url = f'https://api.github.com/repos/Homanti/wacoskins/contents/{nickname}_{file_suffix}.png'
                response_check = requests.get(upload_url, headers=headers)

                if response_check.status_code == 200:
                    # Файл существует, получаем информацию о нём для удаления
                    file_info = response_check.json()
                    sha = file_info['sha']

                    # Удаляем существующий файл
                    delete_data = {
                        'message': f'Delete existing {file_suffix} image',
                        'sha': sha,
                        'branch': 'main'
                    }
                    response_delete = requests.delete(upload_url, headers=headers, json=delete_data)

                    if response_delete.status_code in (200, 204):
                        print(f"Existing {file_suffix} image deleted successfully.")
                    else:
                        print(f"Failed to delete existing {file_suffix} image: {response_delete.status_code} - {response_delete.json().get('message', 'Unknown error')}")

                # Теперь загружаем новое изображение
                data = {
                    'message': f'Upload {file_suffix} image',
                    'content': encoded_image,
                    'branch': 'main'
                }

                response_upload = requests.put(upload_url, headers=headers, json=data)

                if response_upload.status_code in (201, 200):
                    print(f"{file_suffix.capitalize()} image uploaded successfully.")
                else:
                    print(f"Image upload failed: {response_upload.status_code} - {response_upload.json().get('message', 'Unknown error')}")

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

if __name__ == '__main__':
    api = Api()
    window = webview.create_window(title="WacoLauncher", url="web/login.html", width=1296, height=809, js_api=api, resizable=False, fullscreen=False)
    webview.start(api.check_login, debug=False)
