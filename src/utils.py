import json
import os
import shutil
import requests
from src.logger_setup import logging

def create_folder_if_needed(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        logging.info(f"Папка {folder_name} создана")

def remove_file(file_path):
    try:
        os.remove(file_path)
        logging.info(f"Файл {file_path} успешно удален.")
    except FileNotFoundError:
        logging.warning(f"Файл {file_path} не найден.")
    except Exception as e:
        logging.error(f"Ошибка при удалении файла {file_path}: {e}")

def remove_directory(dir_path):
    try:
        shutil.rmtree(dir_path)
        logging.info(f"Директория {dir_path} и все ее содержимое успешно удалены.")
    except FileNotFoundError:
        logging.warning(f"Директория {dir_path} не найдена.")
    except Exception as e:
        logging.error(f"Ошибка при удалении директории {dir_path}: {e}")

def read_json(filename):  # чтение json файлов
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

def write_json(filename, data):
    try:
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)
        logging.info(f"Файл {filename} создан или изменен")
    except Exception as e:
        logging.error(f"Ошибка при обработке файла {filename}: {e}, информация которая записывалась в файл {data}")