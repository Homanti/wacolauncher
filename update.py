import json
import shutil
from urllib.parse import urlsplit
import webview
import os
import requests

def createFolderIfNeeded(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        print(f"Папка {folder_name} создана")

createFolderIfNeeded("data")

def file_download(url, folder_path, what):
    global downloading
    os.makedirs(folder_path, exist_ok=True)

    api = Api()

    try:
        # Получаем ответ от сервера
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        # Пытаемся получить имя файла из заголовков
        if 'Content-Disposition' in response.headers:
            filename = response.headers.get('Content-Disposition').split('filename=')[-1].strip('"')
        else:
            filename = os.path.basename(urlsplit(url).path)

        file_path = os.path.join(folder_path, filename)

        if total_length is None:
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
                    api.progress_bar_set(progress, what)

            print(f"Файл успешно загружен и сохранен в {file_path}.")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка загрузки файла: {e}")
        return False

    downloading = False
    return True

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

    def progress_bar_set(self, percent, what):
        window.evaluate_js(f"""
        document.getElementById('progress_bar').style.width = '{percent}%';
        document.getElementById('progress_text').textContent = 'Установка {what}... {round(percent, 2)}%';
        """)

    def change_innerHTML(self, element_id, innerHTML):
        window.evaluate_js(f"""
        document.getElementById('{element_id}').innerHTML = '{innerHTML}';
        """)

    def show_info_message(self, title, text):
        window.evaluate_js(f"""
        show_info_modal('{title}', '{text}');
        """)

if __name__ == '__main__':
    api = Api()
    launcher_version = api.readJson("data/launcher_version.json")

    if launcher_version is None:
        api.writeJson("data/launcher_version.json", {"version": None})

    window = webview.create_window(title="WacoLauncher", url="web/update.html", width=400, height=100, js_api=api, resizable=False, fullscreen=False, frameless=True)
    webview.start(debug=True)