import json
import webbrowser
import webview
import os
import requests

def readJson(filename):  # чтение json файлов
    if filename.startswith('https://'):
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

    def account_login(self, login, password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "login", "nickname": login, "password": password}
        )

        if response.status_code == 200:
            save_account(response.json()["result"][1], response.json()["result"][2])
            return response.json()["result"]

        elif response.status_code == 401:
            data = readJson("data/credentials.json")
            if data:
                data = [item for item in data if not (item['nickname'] == login and item['password'] == password)]
                writeJson("data/credentials.json", data)

            print(f"Login failed: {response.json()['detail']}")
            return 401
        else:
            return 502

    def account_register(self, login, password):
        response = requests.post(
            "https://wacodb-production.up.railway.app/database/",
            json={"action": "register", "nickname": login, "password": password}
        )
        if response.status_code == 200:
            return self.account_login(login, password)
        else:
            print(f"Registration failed: {response.json()['detail']}")
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
    webview.start(api.check_login,debug=True)
